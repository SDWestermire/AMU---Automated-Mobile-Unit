
import random
import serial
import time
import threading
import yaml
import os
from datetime import datetime

class BotCarNode:
    def __init__(self, config_path="botcar_config.yaml"):
        # Load configuration
        self.config = self.load_yaml_config(config_path)
        self.node_id = self.config.get("node_id", 4)
        self.base_id = self.config.get("base_id", 1)
        self.port = self.config.get("serial_port", "/dev/ttyS0")
        self.baud = self.config.get("baud_rate", 115200)
        self.waypoints = self.config.get("waypoints", [])
        self.role = self.config.get("role", "scout")

        # Retry delay settings from YAML
        self.retry_delay_min = self.config.get("retry_delay_min", 5)
        self.retry_delay_max = self.config.get("retry_delay_max", 15)

        # Logging settings
        self.mission_logging = str(self.config.get("Mission_Logging", "N")).upper() == "Y"
        self.log_dir = self.config.get("Log_Directory", "./logs")
        self.log_file = None
        if self.mission_logging:
            os.makedirs(self.log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = os.path.join(self.log_dir, f"mission_log_{timestamp}.txt")
            print(f"[BotCarNode] Mission logging enabled. Log file: {self.log_file}")

        # Initialize LoRa
        try:
            self.lora = serial.Serial(self.port, self.baud, timeout=1)
            print(f"[BotCarNode] LoRa initialized on {self.port} at {self.baud} baud.")
        except Exception as e:
            print(f"[BotCarNode] Error initializing LoRa: {e}")
            self.lora = None

        self.running = True
        self.last_ack = None
        self.last_rssi = "N/A"
        self.last_snr = "N/A"

    def load_yaml_config(self, path):
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[Config Error] Unable to load {path}: {e}")
            return {}

    def write_log(self, entry):
        if self.mission_logging and self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(entry + "\n")

    def setup_lora(self):
        cmds = [
            f"AT+ADDRESS={self.node_id}\r\n",
            f"AT+NETWORKID=6\r\n",
            "AT+BAND=915000000\r\n",
            "AT+BAND?\r\n",
            "AT+ADDRESS?\r\n",
            "AT+NETWORKID?\r\n"
        ]
        for cmd in cmds:
            self.lora.write(cmd.encode())
            time.sleep(0.5)
            response = self.lora.read(self.lora.inWaiting()).decode().strip()
            print(f"[Node {self.node_id} Setup] {response}")

    def send_registration(self):
        reg_message = f"REG:{self.node_id}"
        payload = f"AT+SEND={self.base_id},{len(reg_message)},{reg_message}\r\n"
        expected_ack = f"ACKREG:{self.node_id}"
        attempt = 1
        ack_status = "Timeout"
        while attempt <= 3 and self.running:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[Node {self.node_id}] Registration attempt {attempt}")
            self.lora.write(payload.encode())
            time.sleep(5)  # Wait for ACK
            if self.last_ack == expected_ack:
                ack_status = "Received"
                print(f"[Node {self.node_id}] Registration acknowledged.")
                break
            else:
                print(f"[Node {self.node_id}] Registration retry {attempt}")
                attempt += 1
        log_entry = f"[{ts}] node_id={self.node_id}, type=REG, wp_index=N/A, lat=N/A, lon=N/A, RSSI={self.last_rssi}, SNR={self.last_snr}, ACK={ack_status}"
        self.write_log(log_entry)

    def transmit_waypoints(self):
        for i, waypoint in enumerate(self.waypoints):
            if not self.running:
                break
            lat, lon = waypoint
            message = f"{self.node_id}:{i}:{lat},{lon}"
            payload = f"AT+SEND={self.base_id},{len(message)},{message}\r\n"
            expected_ack = f"ACK:{self.node_id}:{i}"
            self.last_ack = None
            attempt = 1
            while attempt <= 3 and self.running:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[Node {self.node_id} TX] Waypoint {i}, Attempt {attempt}")
                self.lora.write(payload.encode())
                delay = random.randint(self.retry_delay_min, self.retry_delay_max)
                print(f"[Node {self.node_id}] Waiting {delay}s before next attempt...")
                time.sleep(delay)
                ack_status = "Timeout"
                if self.last_ack == expected_ack:
                    ack_status = "Received"
                    print(f"[Node {self.node_id} SUCCESS] Waypoint {i} acknowledged.")
                    log_entry = f"[{ts}] node_id={self.node_id}, type=WAYPOINT, wp_index={i}, lat={lat}, lon={lon}, RSSI={self.last_rssi}, SNR={self.last_snr}, ACK={ack_status}"
                    self.write_log(log_entry)
                    break
                else:
                    print(f"[Node {self.node_id} RETRY] Waypoint {i}, Attempt {attempt}")
                    log_entry = f"[{ts}] node_id={self.node_id}, type=WAYPOINT, wp_index={i}, lat={lat}, lon={lon}, RSSI={self.last_rssi}, SNR={self.last_snr}, ACK={ack_status}"
                    self.write_log(log_entry)
                    attempt += 1
            if attempt > 3:
                print(f"[Node {self.node_id} FAIL] Waypoint {i} failed after 3 retries")

    def listen_for_ack(self):
        last_processed_ack = None
        while self.running:
            if self.lora.in_waiting > 0:
                response = self.lora.readline().decode().strip()
                if response.startswith("+RCV="):
                    fields = response.split(",")
                    if len(fields) >= 5:
                        sender, length, msg, rssi, snr = fields[:5]
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if msg.startswith(f"ACK:{self.node_id}:") or msg.startswith(f"ACKREG:{self.node_id}"):
                            if msg != last_processed_ack:
                                print(f"[Node {self.node_id} RX {ts}] ACK received: {msg}")
                                self.last_ack = msg
                                self.last_rssi = rssi
                                self.last_snr = snr
                                last_processed_ack = msg
            time.sleep(0.1)

    def start(self):
        self.setup_lora()
        threading.Thread(target=self.listen_for_ack, daemon=True).start()
        self.send_registration()
        threading.Thread(target=self.transmit_waypoints, daemon=True).start()

    def stop(self):
        self.running = False
        self.lora.close()
        print(f"[Node {self.node_id}] Shutdown complete.")

if __name__ == "__main__":
    botCar = BotCarNode(config_path="botcar_config.yaml")
    try:
        botCar.start()
    except KeyboardInterrupt:
        botCar.stop()
