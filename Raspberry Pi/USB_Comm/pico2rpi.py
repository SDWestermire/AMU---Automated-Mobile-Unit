#pico2rpi.py dated 9 Oct Ver 1

import time
import usb_cdc
import json

def send_telemetry(counter):
    if usb_cdc.data:
        telemetry = {
            "v": 1,
            "type": "telemetry",
            "ts": time.time(),
            "imu": {
                "heading": 123.45,
                "compass": 120,
                "roll": -10.5,
                "pitch": 5.2
            },
            "gps": {
                "lat": 33.686377,
                "lon": -117.789653
            },
            "calib": {
                "sys": 3,
                "gyro": 3,
                "accel": 3,
                "mag": 3
            }
        }
        message = json.dumps(telemetry) + "\n"
        usb_cdc.data.write(message.encode('utf-8'))
        print(f"Pico sent: {message.strip()}")
    else:
        print("usb_cdc.data is not available. Check boot.py configuration.")

def receive_message():
    if usb_cdc.data and usb_cdc.data.in_waiting > 0:
        try:
            data_in = usb_cdc.data.readline().strip().decode('utf-8')
            if data_in:
                print(f"\tPico received: {data_in}")
        except Exception as e:
            print(f"Error reading data: {e}")

print("Pico ready and listening on serial data channel...")
counter = 0

while True:
    send_telemetry(counter)
    receive_message()
    counter += 1
    time.sleep(5)