
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: AMU / botCar
File: _BotCarNode.py
Description: BotCarNode class handling YAML config, LoRa setup, registration,
             waypoint transmission, ACK listening, and mission logging.
             v1.0.4 adds dynamic exponential backoff driven by YAML retry window
             plus a small per-node jitter to reduce cross-AMU collisions.

Version: v1.0.4 Baseline Patch (Exponential Backoff)
Date: 2025-12-03
Author: Steven Westermire (Maddog / Gunny)
Co-Author: M365 Copilot (Microsoft)

Copyright (c) 2025 Steven Westermire. All rights reserved.
"""

import serial
import time
import threading
import yaml
import os
import csv
import random
from datetime import datetime

class BotCarNode:
    def __init__(self, config_path="botcar_config.yaml"):
        # Load configuration (snake_case expected)
        self.config = self.load_yaml_config(config_path)

        # Core IDs and port settings
        self.node_id       = int(self.config.get("node_id", 1))
        self.base_id       = int(self.config.get("base_id", 1))
        self.node_label    = str(self.config.get("node_label", f"AMU_{self.node_id:02d}"))
        self.port          = self.config.get("serial_port", "/dev/ttyS0")
        self.baud          = int(self.config.get("baud_rate", 115200))
        self.network_id    = int(self.config.get("network_id", 6))
        self.band          = int(self.config.get("band", 915000000))

        # Mission and transmission controls
        self.role          = str(self.config.get("role", "scout"))
        self.mission_name  = str(self.config.get("mission_name", "Test Route"))
        self.waypoints     = self.config.get("waypoints", [])
        self.tx_interval   = float(self.config.get("tx_interval", 0))  # optional spacing between ACKed waypoints
        self.max_retries   = int(self.config.get("max_retries", 3))

        # --- YAML-driven retry window (BASE for exponential backoff) ---
        self.retry_min     = int(self.config.get("retry_delay_min", 15))
        self.retry_max     = int(self.config.get("retry_delay_max", 80))

        # Logging toggles
        _mlog = self.config.get("mission_logging", True)
        self.mission_logging = bool(_mlog) if isinstance(_mlog, bool) else str(_mlog).strip().upper() == "Y"
        self.log_dir = self.config.get("log_directory", "./logs")

        # CSV logging toggle
        _csv = self.config.get("csv_logging", False)
        self.csv_logging = bool(_csv) if isinstance(_csv, bool) else str(_csv).strip().upper() == "Y"

        # Initialize log files (TXT + CSV)
        os.makedirs(self.log_dir, exist_ok=True)
        ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.txt_log_path = os.path.join(self.log_dir, f"mission_log_{self.node_label}_{ts_now}.txt") if self.mission_logging else None
        self.csv_log_path = os.path.join(self.log_dir, f"mission_log_{self.node_label}_{ts_now}.csv") if self.csv_logging else None

        self.csv_fh = None
        self.csv_writer = None
        if self.csv_logging and self.csv_log_path:
            self.csv_fh = open(self.csv_log_path, "w", newline="")
            self.csv_writer = csv.writer(self.csv_fh)
            self.csv_writer.writerow(["timestamp", "node_id", "node_label", "type", "wp_index", "lat", "lon", "rssi", "snr", "ack_status"])
            self.csv_fh.flush()

        if self.mission_logging and self.txt_log_path:
            print(f"[BotCarNode] Mission TXT log: {self.txt_log_path}")
        if self.csv_logging and self.csv_log_path:
            print(f"[BotCarNode] Mission CSV log: {self.csv_log_path}")

        # Initialize LoRa serial
        try:
            self.lora = serial.Serial(self.port, self.baud, timeout=1)
            print(f"[BotCarNode] LoRa initialized on {self.port} at {self.baud} baud.")
        except Exception as e:
            print(f"[BotCarNode] Error initializing LoRa: {e}")
            self.lora = None

        # Runtime state
        self.running = False

        # ACK synchronization
        self.ack_lock = threading.Lock()
        self.ack_event = threading.Event()
        self.expected_ack = None
        self.last_rssi = None
        self.last_snr = None

        # Threads
        self.rx_thread = None
        self.tx_thread = None

    # -------------------- Config & Logging --------------------
    def load_yaml_config(self, path):
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[Config Error] Unable to load {path}: {e}")
            return {}

    def write_txt_log(self, entry):
        if self.mission_logging and self.txt_log_path:
            with open(self.txt_log_path, "a") as f:
                f.write(entry + "\n")

    def write_csv_log(self, ts, msg_type, wp_index, lat, lon, ack_status):
        if self.csv_logging and self.csv_writer and self.csv_fh:
            self.csv_writer.writerow([
                ts, self.node_id, self.node_label, msg_type,
                wp_index if wp_index is not None else "N/A",
                lat if lat is not None else "N/A",
                lon if lon is not None else "N/A",
                self.last_rssi if self.last_rssi is not None else "N/A",
                self.last_snr if self.last_snr is not None else "N/A",
                ack_status
            ])
            self.csv_fh.flush()

    # -------------------- Radio setup --------------------
    def setup_lora(self):
        if not self.lora:
            return
        cmds = [
            f"AT+ADDRESS={self.node_id}\r\n",
            f"AT+NETWORKID={self.network_id}\r\n",
            f"AT+BAND={self.band}\r\n",
            "AT+ADDRESS?\r\n",
            "AT+NETWORKID?\r\n",
            "AT+BAND?\r\n"
        ]
        for cmd in cmds:
            self.lora.write(cmd.encode())
            time.sleep(0.15)
        # Drain any echoes to start clean
        time.sleep(0.1)
        while self.lora.in_waiting:
            _ = self.lora.read(self.lora.in_waiting)

        print(f"[Node {self.node_id}] Radio configured: ADDRESS={self.node_id}, NETWORKID={self.network_id}, BAND={self.band}")

    # -------------------- RX listener (ACKs) --------------------
    def listen_for_ack(self):
        while self.running and self.lora:
            try:
                if self.lora.in_waiting > 0:
                    line = self.lora.readline().decode(errors="ignore").strip()
                    if not line:
                        time.sleep(0.02)
                        continue

                    # Expect +RCV=<sender>,<len>,<msg>,<rssi>,<snr>
                    if line.startswith("+RCV="):
                        parts = line.split(",")
                        if len(parts) >= 5:
                            msg = parts[2].strip()
                            try:
                                rssi = int(parts[3].strip())
                            except Exception:
                                rssi = None
                            try:
                                snr = int(parts[4].strip())
                            except Exception:
                                snr = None

                            # Only accept exact expected ACK
                            with self.ack_lock:
                                if self.expected_ack and msg == self.expected_ack:
                                    # Update link metrics only on matched ACK
                                    self.last_rssi = rssi
                                    self.last_snr = snr
                                    self.ack_event.set()
                                    # For operator visibility
                                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    print(f"[Node {self.node_id} RX {ts}] ACK matched: {msg} (RSSI={rssi}, SNR={snr})")
                    else:
                        # Ignore module housekeeping (+OK, +ERR=...)
                        pass

                time.sleep(0.05)
            except Exception as e:
                print(f"[Node {self.node_id}] RX error: {e}")
                time.sleep(0.1)

    # -------------------- Exponential backoff (YAML-driven) --------------------
    def _compute_retry_delay(self, attempt: int) -> int:
        """
        Compute an exponential backoff delay based on YAML base window and attempt number.
        attempt: 1..max_retries
        Returns delay in seconds (int).
        """
        # Base window from YAML (e.g., 15..80)
        base_min = int(self.retry_min)
        base_max = int(self.retry_max)

        # Exponential growth per attempt: (2 ** (attempt - 1))
        factor = 2 ** (attempt - 1)

        delay_min = base_min * factor
        delay_max = base_max * factor

        # Stable per-node jitter (0..2s) prevents same-second retries across nodes
        node_jitter = (self.node_id % 3)

        # Randomized delay within the grown window + jitter
        delay = random.randint(delay_min, delay_max) + node_jitter
        return delay

    # -------------------- Registration --------------------
    def send_registration(self):
        if not self.lora:
            return
        reg_msg = f"REG:{self.node_id}"
        payload = f"AT+SEND={self.base_id},{len(reg_msg)},{reg_msg}\r\n"

        for attempt in range(1, self.max_retries + 1):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.ack_lock:
                self.expected_ack = f"ACKREG:{self.node_id}"
                self.ack_event.clear()

            print(f"[Node {self.node_id}] REG attempt {attempt}")
            self.lora.write(payload.encode())

            # Wait for ACKREG with a bounded timeout
            acknowledged = self.ack_event.wait(5.0)
            ack_status = "Received" if acknowledged else "Timeout"

            # Log entry
            self.write_txt_log(
                f"[{ts}] node_id={self.node_id}, type=REG, wp_index=N/A, lat=N/A, lon=N/A, "
                f"RSSI={self.last_rssi if self.last_rssi is not None else 'N/A'}, "
                f"SNR={self.last_snr if self.last_snr is not None else 'N/A'}, ACK={ack_status}"
            )
            self.write_csv_log(ts, "REG", None, None, None, ack_status)

            if acknowledged:
                print(f"[Node {self.node_id}] Registration acknowledged.")
                return
            else:
                # Dynamic exponential backoff
                delay = self._compute_retry_delay(attempt)
                print(f"[Node {self.node_id}] REG backoff {delay}s...")
                time.sleep(delay)

        print(f"[Node {self.node_id}] REG failed after {self.max_retries} attempts")

    # -------------------- Waypoint TX --------------------
    def transmit_waypoints(self):
        if not self.lora:
            return

        for i, wp in enumerate(self.waypoints):
            if not self.running:
                break

            lat, lon = wp
            msg = f"{self.node_id}:{i}:{lat},{lon}"
            payload = f"AT+SEND={self.base_id},{len(msg)},{msg}\r\n"

            delivered = False
            for attempt in range(1, self.max_retries + 1):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with self.ack_lock:
                    self.expected_ack = f"ACK:{self.node_id}:{i}"
                    self.ack_event.clear()

                print(f"[Node {self.node_id} TX] WP {i}, attempt {attempt}")
                self.lora.write(payload.encode())

                # Wait for matching ACK with timeout
                acknowledged = self.ack_event.wait(self._ack_timeout_for_payload(msg))
                ack_status = "Received" if acknowledged else "Timeout"

                # Log attempt
                self.write_txt_log(
                    f"[{ts}] node_id={self.node_id}, type=WAYPOINT, wp_index={i}, "
                    f"lat={lat}, lon={lon}, "
                    f"RSSI={self.last_rssi if self.last_rssi is not None else 'N/A'}, "
                    f"SNR={self.last_snr if self.last_snr is not None else 'N/A'}, ACK={ack_status}"
                )
                self.write_csv_log(ts, "WAYPOINT", i, lat, lon, ack_status)

                if acknowledged:
                    print(f"[Node {self.node_id} SUCCESS] WP {i} acknowledged.")
                    delivered = True
                    break
                else:
                    # Dynamic exponential backoff
                    delay = self._compute_retry_delay(attempt)
                    print(f"[Node {self.node_id}] WP {i} backoff {delay}s before retry...")
                    time.sleep(delay)

            if not delivered:
                print(f"[Node {self.node_id}] WP {i} failed after {self.max_retries} retries")

            # Optional spacing between ACKed waypoints
            if delivered and self.tx_interval > 0:
                print(f"[Node {self.node_id}] Waiting tx_interval={self.tx_interval}s before next WP...")
                time.sleep(self.tx_interval)

    def _ack_timeout_for_payload(self, msg: str) -> float:
        """
        Heuristic timeout helper. LoRa airtime depends on RF parameters and payload length.
        We use a simple fixed window (5s) which is adequate for short payloads; adjust if needed.
        """
        return 5.0

    # -------------------- Lifecycle --------------------
    def start(self):
        if not self.lora:
            print(f"[Node {self.node_id}] LoRa not available; abort start.")
            return
        self.running = True
        self.setup_lora()

        # Start RX listener thread
        self.rx_thread = threading.Thread(target=self.listen_for_ack, name=f"ACK_RX_{self.node_id}", daemon=True)
        self.rx_thread.start()

        # Registration (blocking until done)
        self.send_registration()

        # Start TX thread
        self.tx_thread = threading.Thread(target=self.transmit_waypoints, name=f"WP_TX_{self.node_id}", daemon=True)
        self.tx_thread.start()

    def stop(self):
        self.running = False
        # Give threads a moment to unwind
        try:
            if self.tx_thread and self.tx_thread.is_alive():
                self.tx_thread.join(timeout=1.5)
        except Exception:
            pass
        try:
            if self.rx_thread and self.rx_thread.is_alive():
                self.rx_thread.join(timeout=1.5)
        except Exception:
            pass
        # Close serial
        try:
            if self.lora and self.lora.is_open:
                self.lora.close()
        except Exception:
            pass
        # Close CSV
        try:
            if self.csv_fh:
                self.csv_fh.close()
        except Exception:
            pass
        print(f"[Node {self.node_id}] Shutdown complete.")

if __name__ == "__main__":
    # Optional direct run (use mainBotCar.py in production)
    botCar = BotCarNode(config_path="botcar_config.yaml")
    try:
        botCar.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        botCar.stop()
