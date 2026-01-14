#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: AMU / botCar
File: botcarBaseStation.py  (Ver 1.1)
Description: LoRa base station listener that ACKs botCar messages and logs mission data.
Restores mission logging and fixes parsing; minimal changes to preserve baseline behavior.
"""

import os
import time
from datetime import datetime

import serial
import yaml


# ---------------- Configuration ----------------
CONFIG_FILE = "baseStation_config.yaml"
DEFAULTS = {
    "Serial_Port": "/dev/ttyS0",
    "Baud_Rate": 115200,
    "Timeout": 1,             # seconds
    "Retry_Count": 3,
    "Mission_Logging": "Y",   # ON by default to match baseline behavior
    "Log_Directory": "./logs",
}

def load_config(path: str) -> dict:
    cfg = DEFAULTS.copy()
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            cfg.update(loaded)
    except Exception as e:
        print(f"[BaseStation] Config load warning ({path}): {e}. Using defaults.")
    return cfg

cfg = load_config(CONFIG_FILE)

SERIAL_PORT     = cfg["Serial_Port"]
BAUD_RATE       = int(cfg["Baud_Rate"])
TIMEOUT         = float(cfg["Timeout"])
RETRY_COUNT     = int(cfg["Retry_Count"])
MISSION_LOGGING = str(cfg["Mission_Logging"]).strip().upper() == "Y"
LOG_DIR         = cfg["Log_Directory"]

# ---------------- Logging setup ----------------
os.makedirs(LOG_DIR, exist_ok=True)  # ensure ./logs exists

log_file = None
if MISSION_LOGGING:
    ts_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"mission_log_{ts_stamp}.txt")
    print(f"[BaseStation] Mission logging enabled. Log file: {log_file}")

def write_log(line: str) -> None:
    if MISSION_LOGGING and log_file:
        with open(log_file, "a", buffering=1, encoding="utf-8") as f:
            f.write(line + "\n")

# --------------- Serial / LoRa I/O ---------------
def setup_lora(port: str, baud: int):
    try:
        lora = serial.Serial(port, baud, timeout=TIMEOUT)
        print("[BaseStation] LoRa module initialized.")
        return lora
    except Exception as e:
        print(f"[BaseStation] Error initializing LoRa: {e}")
        return None


def parse_rcv(raw: str):
    """
    Parse lines like: +RCV=<src>,<len>,<data>,<RSSI>,<SNR>
    Returns (src:int, ln:int, data:str, rssi:int, snr:int) or None.
    Handles commas inside <data> (e.g., lat,lon) by splitting RSSI/SNR from the right.
    """
    s = (raw or "").strip()
    if not s.startswith("+RCV="):
        return None
    try:
        _, rest = s.split("=", 1)
        left, rssi_str, snr_str = rest.rsplit(",", 2)       # split from RIGHT
        src_str, ln_str, data   = left.split(",", 2)        # split LEFT side
        return int(src_str), int(ln_str), data.strip(), int(rssi_str), int(snr_str)
    except Exception:
        return None


def listen_for_botcar_transmissions(lora: serial.Serial):
    print("[BaseStation] Listening for botCar transmissions...")

    while True:
        try:
            line = lora.readline().decode(errors="ignore").strip()
            if not line:
                time.sleep(0.05)
                continue

            pkt = parse_rcv(line)
            if not pkt:
                # Ignore housekeeping (+OK, +ERR=...), or echoes
                continue

            src, length, data, rssi, snr = pkt
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Registration payload: "REG:<node_id>"
            if data.startswith("REG:"):
                node_id = data.split(":", 1)[1]

                # Send ACKREG back to sender (src)
                ack_msg = f"ACKREG:{node_id}"
                ack_cmd = f"AT+SEND={src},{len(ack_msg)},{ack_msg}\r\n"
                lora.write(ack_cmd.encode("utf-8"))

                print(f"[{ts}] Registration from Node {node_id}: RSSI={rssi}, SNR={snr}")
                print(f"[BaseStation] Sent ACK for registration: {ack_msg}")
                log_line = (
                    f"[{ts}] node_id={node_id}, type=REG, wp_index=N/A, "
                    f"lat=N/A, lon=N/A, RSSI={rssi}, SNR={snr}, ACK=Sent"
                )
                write_log(log_line)

            else:
                # Waypoint payload: "<node_id>:<idx>:lat,lon"
                p = data.split(":")
                if len(p) >= 3:
                    node_id  = p[0]
                    wp_index = p[1]
                    lat, lon = (p[2].split(",", 1) + ["N/A"])[:2]

                    # Send ACK back to sender
                    ack_msg = f"ACK:{node_id}:{wp_index}"
                    ack_cmd = f"AT+SEND={src},{len(ack_msg)},{ack_msg}\r\n"
                    lora.write(ack_cmd.encode("utf-8"))

                    print(
                        f"[{ts}] Node {node_id} Waypoint {wp_index}: "
                        f"Lat={lat}, Lon={lon}, RSSI={rssi}, SNR={snr}"
                    )
                    print(f"[BaseStation] Sent ACK to Node {node_id}: {ack_msg}")

                    log_line = (
                        f"[{ts}] node_id={node_id}, type=WAYPOINT, wp_index={wp_index}, "
                        f"lat={lat}, lon={lon}, RSSI={rssi}, SNR={snr}, ACK=Sent"
                    )
                    write_log(log_line)
                else:
                    # Unexpected payload format—skip but keep running
                    print(f"[BaseStation] Unexpected +RCV data format: '{line}'")

        except KeyboardInterrupt:
            print("[BaseStation] Stopped by user.")
            break
        except Exception as e:
            print(f"[BaseStation] Parse/IO error: {e}")
            time.sleep(0.2)


# -------------------- Main ----------------------
if __name__ == "__main__":
    lora = setup_lora(SERIAL_PORT, BAUD_RATE)
    if lora:
        try:
            listen_for_botcar_transmissions(lora)
        finally:
            try:
                lora.close()
            except Exception:
                pass
