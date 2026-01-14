# rpi2pico.py ver.1 9 Oct

import serial
import time
import json
from datetime import datetime

SERIAL_PORT = '/dev/ttyACM0'	
BAUD_RATE = 115200

def send_and_receive():
    counter = 100
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        ser.reset_input_buffer()
        time.sleep(2)

        while True:
            command_str = f"Message from Pi: {counter}\n"
            ser.write(command_str.encode('utf-8'))
            print(f"Sent: {command_str.strip()}")
            counter += 1

            while ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        data = json.loads(line)
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{ts}] Telemetry Received:")
                        imu = data.get("imu", {})
                        gps = data.get("gps", {})
                        calib = data.get("calib", {})
                        print(f"  IMU: Heading={imu.get('heading')}° Compass={imu.get('compass')} Roll={imu.get('roll')}° Pitch={imu.get('pitch')}°")
                        print(f"  GPS: lat={gps.get('lat')} lon={gps.get('lon')}")
                        print(f"  CALIB: SYS={calib.get('sys')} GYR={calib.get('gyro')} ACC={calib.get('accel')} MAG={calib.get('mag')}")
                    except json.JSONDecodeError:
                        print(f"\tReceived from Pico (non-JSON): {line}")

            time.sleep(5)

    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    send_and_receive()