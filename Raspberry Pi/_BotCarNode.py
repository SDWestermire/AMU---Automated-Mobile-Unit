<<<<<<< HEAD
import serial
import time
import threading
import yaml
from datetime import datetime
from amuGPS import get_gps_location as gpsLOC

class BotCarNode:
    def __init__(self, config_path="botcar_config.yaml"):
        self.config = self.load_yaml_config(config_path)
        self.node_id = self.config.get("node_id", 0)
        self.base_id = self.config.get("base_id", 1)
        self.tx_interval = self.config.get("tx_interval", 1)
        self.port = self.config.get("serial_port", "/dev/ttyS0")
        self.baud = self.config.get("baud_rate", 115200)
        self.waypoints = self.config.get("waypoints", [])
        self.role = self.config.get("role", "scout")
        self.lora = serial.Serial(self.port, self.baud, timeout=1)
        self.running = True

    def load_yaml_config(self, path):
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[Config Error] Unable to load {path}: {e}")
            return {}

    def setup_lora(self):
        cmds = [
            f"AT+ADDRESS={self.node_id}\r\n",
            f"AT+NETWORKID=6\r\n",
            "AT+BAND?\r\n",
            "AT+ADDRESS?\r\n",
            "AT+NETWORKID?\r\n"
        ]
        for cmd in cmds:
            self.lora.write(cmd.encode())
            time.sleep(0.5)
            response = self.lora.read(self.lora.inWaiting()).decode().strip()
            print(f"[Node {self.node_id} Setup] {response}")

    def transmit_gps(self):
        while self.running:
            gps_data = str(gpsLOC())
            if gps_data and len(gps_data.strip()) > 5:
                payload = f"AT+SEND={self.base_id},{len(gps_data)},{gps_data}\r\n"
                print(f"[Node {self.node_id} TX] GPS: {gps_data}")
                self.lora.write(payload.encode())
            else:
                print(f"[Node {self.node_id} TX] Invalid GPS.")
            time.sleep(self.tx_interval)

    def listen_for_ack(self):
        while self.running:
            if self.lora.in_waiting > 0:
                response = self.lora.readline().decode().strip()
                if response.startswith("+RCV="):
                    fields = response.split(",")
                    if len(fields) == 5:
                        sender, length, msg, rssi, snr = fields
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[Node {self.node_id} RX {ts}] From {sender}: '{msg}' | RSSI={rssi}, SNR={snr}")
                    else:
                        print(f"[Node {self.node_id} RX] Unexpected format: '{response}'")
            time.sleep(0.1)

    def start(self):
        self.setup_lora()
        threading.Thread(target=self.transmit_gps, daemon=True).start()
        threading.Thread(target=self.listen_for_ack, daemon=True).start()

    def stop(self):
        self.running = False
        self.lora.close()
        print(f"[Node {self.node_id}] Shutdown complete.")
=======
import serial
import time
import threading
import yaml
from datetime import datetime
from amuGPS import get_gps_location as gpsLOC

class BotCarNode:
    def __init__(self, config_path="botcar_config.yaml"):
        self.config = self.load_yaml_config(config_path)
        self.node_id = self.config.get("node_id", 0)
        self.base_id = self.config.get("base_id", 1)
        self.tx_interval = self.config.get("tx_interval", 1)
        self.port = self.config.get("serial_port", "/dev/ttyS0")
        self.baud = self.config.get("baud_rate", 115200)
        self.waypoints = self.config.get("waypoints", [])
        self.role = self.config.get("role", "scout")
        self.lora = serial.Serial(self.port, self.baud, timeout=1)
        self.running = True

    def load_yaml_config(self, path):
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[Config Error] Unable to load {path}: {e}")
            return {}

    def setup_lora(self):
        cmds = [
            f"AT+ADDRESS={self.node_id}\r\n",
            f"AT+NETWORKID=6\r\n",
            "AT+BAND?\r\n",
            "AT+ADDRESS?\r\n",
            "AT+NETWORKID?\r\n"
        ]
        for cmd in cmds:
            self.lora.write(cmd.encode())
            time.sleep(0.5)
            response = self.lora.read(self.lora.inWaiting()).decode().strip()
            print(f"[Node {self.node_id} Setup] {response}")

    def transmit_gps(self):
        while self.running:
            gps_data = str(gpsLOC())
            if gps_data and len(gps_data.strip()) > 5:
                payload = f"AT+SEND={self.base_id},{len(gps_data)},{gps_data}\r\n"
                print(f"[Node {self.node_id} TX] GPS: {gps_data}")
                self.lora.write(payload.encode())
            else:
                print(f"[Node {self.node_id} TX] Invalid GPS.")
            time.sleep(self.tx_interval)

    def listen_for_ack(self):
        while self.running:
            if self.lora.in_waiting > 0:
                response = self.lora.readline().decode().strip()
                if response.startswith("+RCV="):
                    fields = response.split(",")
                    if len(fields) == 5:
                        sender, length, msg, rssi, snr = fields
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[Node {self.node_id} RX {ts}] From {sender}: '{msg}' | RSSI={rssi}, SNR={snr}")
                    else:
                        print(f"[Node {self.node_id} RX] Unexpected format: '{response}'")
            time.sleep(0.1)

    def start(self):
        self.setup_lora()
        threading.Thread(target=self.transmit_gps, daemon=True).start()
        threading.Thread(target=self.listen_for_ack, daemon=True).start()

    def stop(self):
        self.running = False
        self.lora.close()
        print(f"[Node {self.node_id}] Shutdown complete.")
>>>>>>> bb5aae96ba06986ab46e1ab2a686263b376c0df3
