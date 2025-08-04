# noted from https://github.com/papercodeIN/Embedded_Devices/blob/main/REYAX/RYLR998/Python/RYLR998%20Integration%20with%20Python.ipynb
# pip3 install pyserial
#TESTED GOOD ON 2 JUL 2025

import serial
import time
import random
from datetime import datetime
from amuGPS import get_gps_location as gpsLOC

#Initialize LoRa loraial communication
lora = serial.Serial("/dev/ttyS0", 115200, timeout=1)
lora.write(b"AT+NETWORKID=6\r\n")
lora.write(b"AT+ADDRESS=2")


def check_networkid():
    lora.write(b'AT+NETWORKID?\r\n')
    time.sleep(1)
    response = lora.read(lora.inWaiting()).decode()
    print(response)
    
def check_rfband():
    lora.write(b'AT+BAND?\r\n')
    time.sleep(1)
    response = lora.read(lora.inWaiting()).decode()
    print(response)
    
def check_address():
    lora.write(b'AT+ADDRESS?\r\n')
    time.sleep(1)
    response = lora.read(lora.inWaiting()).decode()
    print(response)

def set_address():
     lora.write(b'AT+ADDRESS=2\r\n')
     time.sleep(1)
     response = lora.read(lora.inWaiting()).decode()
     print(response)


def check_lastpayload():
    lora.write(b'AT+SEND?\r\n')
    time.sleep(1)
    response = lora.read(lora.inWaiting()).decode()
    print(response)

def send_ACK(ACK='ACK1'):
    lora.write(f'AT+SEND=1,{len(ACK)},{ACK}\r\n'.encode('utf-8'))
    time.sleep(1)
    response = lora.read(lora.inWaiting()).decode()
    print(response)

def send_payload(loc):
    lora.write(b'AT+SEND=1,{len(loc)},{loc}\r\n'.encode('utf-8'))
    time.sleep(1)
    response = lora.read(lora.inWaiting()).decode()
    print(response)

def monitor_serial_data(lora):
    try:
        print(f"Listening on {lora.port} at {lora.baudrate} baud rate...")
        while True:
            global curGPSLoc
            if lora.in_waiting > 0:
                data = lora.readline().decode('utf-8').strip()  # Read and decode data
                if data:  # Ensure it's not empty
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp
                    # print(f"[{current_time}] Received data: {data}")
                    
                    if data.startswith("+RCV="):
                        parts = data.split(',')
                        node_id, msg_len, message, rssi, snr = parts[0], parts[1], parts[2], parts[3], parts[4]
                        print(f"[{current_time}] NodeID: {node_id}, Message: {message}, RSSI: {rssi}, SNR: {snr}")
                        print(f"Message:{message}")
                        curGPSLoc = gpsLOC()
                        curGPSLoc = str(curGPSLoc)
                        send_ACK(curGPSLoc)
                        
                        print (f"Current Loc:{curGPSLoc}")
                       #send_payload(curGPSLoc)
            time.sleep(0.1)  # Prevent CPU overload
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    finally:
        print("Serial monitoring stopped.")

check_networkid()
check_address()
check_rfband()


if __name__ == '__main__':
    while True:
       monitor_serial_data(lora)

lora.close
# monitor_serial_data(ser)
# Close serial connection
# ser.close()
# check_networkid()
# set_address()
# check_rfband()
# check_address()
# check_lastpayload()
# send_payload()
