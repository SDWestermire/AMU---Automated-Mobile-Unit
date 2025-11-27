
import serial
import time
import yaml
import os
from datetime import datetime

# Load configuration from YAML
CONFIG_FILE = "baseStation_config.yaml"
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

SERIAL_PORT = config.get("Serial_Port", "/dev/ttyS0")
BAUD_RATE = config.get("Baud_Rate", 115200)
TIMEOUT = config.get("Timeout", 1)
MISSION_LOGGING = str(config.get("Mission_Logging", "N")).upper() == "Y"
LOG_DIR = config.get("Log_Directory", "./logs")
RETRY_COUNT = config.get("Retry_Count", 3)

# Prepare log file if logging is enabled
log_file = None
if MISSION_LOGGING:
    os.makedirs(LOG_DIR, exist_ok=True)  # Ensure directory exists
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"mission_log_{timestamp}.txt")
    print(f"[BaseStation] Mission logging enabled. Log file: {log_file}")

def write_log(entry):
    if MISSION_LOGGING and log_file:
        with open(log_file, 'a') as f:
            f.write(entry + "\n")

def setup_lora(port, baud):
    try:
        lora = serial.Serial(port, baud, timeout=TIMEOUT)
        print("[BaseStation] LoRa module initialized.")
        return lora
    except Exception as e:
        print(f"[BaseStation] Error initializing LoRa: {e}")
        return None

def listen_for_botcar_transmissions(lora):
    print("[BaseStation] Listening for botCar transmissions...")
    while True:
        if lora.in_waiting > 0:
            response = lora.readline().decode().strip()
            if response.startswith("+RCV="):
                try:
                    fields = response.split(",")
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sender = fields[0].split("=")[1]

                    # Registration message
                    if fields[2].startswith("REG:"):
                        node_id = fields[2].split(":")[1]
                        rssi = fields[3]
                        snr = fields[4]
                        ack_msg = f"ACKREG:{node_id}"
                        ack_payload = f"AT+SEND={sender},{len(ack_msg)},{ack_msg}\r\n"
                        lora.write(ack_payload.encode())
                        print(f"[{ts}] Registration from Node {node_id}: RSSI={rssi}, SNR={snr}")
                        print(f"[BaseStation] Sent ACK for registration: {ack_msg}")
                        log_entry = f"[{ts}] node_id={node_id}, type=REG, wp_index=N/A, lat=N/A, lon=N/A, RSSI={rssi}, SNR={snr}, ACK=Sent"
                        write_log(log_entry)

                    # Waypoint message
                    elif len(fields) >= 6:
                        node_id, wp_index, lat = fields[2].split(":")
                        lon = fields[3]
                        rssi = fields[4]
                        snr = fields[5]
                        ack_msg = f"ACK:{node_id}:{wp_index}"
                        ack_payload = f"AT+SEND={sender},{len(ack_msg)},{ack_msg}\r\n"
                        lora.write(ack_payload.encode())
                        print(f"[{ts}] Node {node_id} Waypoint {wp_index}: Lat={lat}, Lon={lon}, RSSI={rssi}, SNR={snr}")
                        print(f"[BaseStation] Sent ACK to Node {node_id}: {ack_msg}")
                        log_entry = f"[{ts}] node_id={node_id}, type=WAYPOINT, wp_index={wp_index}, lat={lat}, lon={lon}, RSSI={rssi}, SNR={snr}, ACK=Sent"
                        write_log(log_entry)

                    else:
                        print(f"[BaseStation] Unexpected format: '{response}'")

                except Exception as e:
                    print(f"[BaseStation] Parse error: {e}")
        time.sleep(0.5)

if __name__ == "__main__":
    lora = setup_lora(SERIAL_PORT, BAUD_RATE)
    if lora:
        try:
            listen_for_botcar_transmissions(lora)
        except KeyboardInterrupt:
            print("[BaseStation] Shutting down listener.")
            lora.close()
