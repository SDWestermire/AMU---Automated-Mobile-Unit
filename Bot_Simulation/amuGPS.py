import serial
import pynmea2
import time

# Open serial port to which GPS is connected
port = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=1)

def get_gps_location():
    while True:
        try:
            data = port.readline().decode('ascii', errors='replace')
            if data.startswith('$GPGGA') or data.startswith('$GPRMC'):
                msg = pynmea2.parse(data)
                if hasattr(msg, 'latitude') and hasattr(msg, 'longitude'):
                    return (msg.latitude, msg.longitude)
        except pynmea2.ParseError:
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue

# Main loop

if __name__ == '__main__':
    while True:
        currentLocation = get_gps_location()
        print(f"Current Location: {currentLocation}")
        time.sleep(0.4)
