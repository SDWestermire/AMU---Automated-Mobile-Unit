# botcar01LoRaPy2.py
# Raspberry Pi 4 - botCar GPS LoRa Transmitter
# Modules: NEO-6M via amuGPS, RYLR998 (REYAX)
# Author: Steven's Autonomous Fleet Project

import serial
import time
import threading
from datetime import datetime
from amuGPS import get_gps_location as gpsLOC

# Configuration Constants
NODE_ADDRESS = 2       # Unique LoRa address for this botCar
BASE_ADDRESS = 1       # LoRa address of base station
PORT = "/dev/ttyS0"    # UART serial port
BAUD = 115200          # Baud rate for RYLR998
TX_INTERVAL = 1        # Seconds between GPS transmissions

# Initialize serial port for LoRa
lora = serial.Serial(PORT, BAUD, timeout=1)

def setup_lora():
    """Configure LoRa module with address and network settings."""
    cmds = [
        f"AT+ADDRESS={NODE_ADDRESS}\r\n",
        f"AT+NETWORKID=6\r\n",
        "AT+BAND?\r\n",
        "AT+ADDRESS?\r\n",
        "AT+NETWORKID?\r\n"
    ]
    for cmd in cmds:
        lora.write(cmd.encode())
        time.sleep(0.5)
        response = lora.read(lora.inWaiting()).decode().strip()
        print(f"[Setup] {response}")

def transmit_gps():
    """Transmit GPS location every TX_INTERVAL seconds."""
    while True:
        gps_data = str(gpsLOC())  # Format: "lat lon"
        if gps_data and len(gps_data.strip()) > 5:
            print(f"[TX] GPS Raw: {gps_data}")
            payload = f"AT+SEND={BASE_ADDRESS},{len(gps_data)},{gps_data}\r\n"
            print(f"[TX] Payload: {repr(payload)}")
            lora.write(payload.encode())
        else:
            print("[TX] Warning: No valid GPS data available.")
        time.sleep(TX_INTERVAL)

def listen_for_ack():
    """Continuously listen for ACK/NACK messages from base station."""
    while True:
        if lora.in_waiting > 0:
            response = lora.readline().decode().strip()
            if response.startswith("+RCV="):
                try:
                    fields = response.split(",")
                    if len(fields) == 5:
                        sender, length, msg, rssi, snr = fields
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[RX {timestamp}] From Node {sender}: '{msg}' | RSSI={rssi}, SNR={snr}")
                    else:
                        print(f"[RX] Unexpected format: '{response}'")
                except Exception as e:
                    print(f"[RX] Error parsing response: '{response}' ({e})")
        time.sleep(0.1)


# Main execution
if __name__ == "__main__":
    try:
        setup_lora()

        # Start TX and RX loops in parallel
        tx_thread = threading.Thread(target=transmit_gps, daemon=True)
        rx_thread = threading.Thread(target=listen_for_ack, daemon=True)

        tx_thread.start()
        rx_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Shutdown] BotCar halted by user.")
    finally:
        lora.close()
        print("[Shutdown] Serial port closed.")
