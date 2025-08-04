from botcar01LoRaPy2 import monitor_serial_data as MSD
from time import sleep
import serial


# Initialize LoRa loraial communication
lora = serial.Serial("/dev/ttyS0", 115200, timeout=1)
lora.write(b"AT+NETWORKID=6\r\n")
lora.write(b"AT+ADDRESS=2")

while True:
    MSD(lora)
    sleep(1.0)
