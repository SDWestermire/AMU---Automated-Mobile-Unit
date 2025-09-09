
import board
import busio
import time

# === GPS UART Setup ===
try:
    gps_uart = busio.UART(tx=board.GP4, rx=board.GP5, baudrate=9600)
    print("📡 GPS UART initialized")
except Exception as e:
    print("UART init failed:", e)

def parse_gpgga(sentence):
    try:
        parts = sentence.split(',')
        if parts[0] != "$GPGGA":
            return None

        raw_lat = parts[2]
        lat_dir = parts[3]
        raw_lon = parts[4]
        lon_dir = parts[5]

        if not raw_lat or not raw_lon or len(raw_lat) < 4 or len(raw_lon) < 5:
            return None

        lat_deg = int(raw_lat[:2])
        lat_min = float(raw_lat[2:])
        lat = lat_deg + lat_min / 60.0
        if lat_dir == 'S':
            lat = -lat

        lon_deg = int(raw_lon[:3])
        lon_min = float(raw_lon[3:])
        lon = lon_deg + lon_min / 60.0
        if lon_dir == 'W':
            lon = -lon

        return (lat, lon)
    except Exception as e:
        print("Raw GPS:", sentence)
        return None

def read_gps():
    try:
        line = gps_uart.readline()
        if line:
            print(line)
            if line.startswith(b"$GPGGA"):
                try:
                    sentence = line.decode('utf-8').strip()
                    coords = parse_gpgga(sentence)
                    if coords:
                        print("📍 GPS -> Latitude: {:.6f}, Longitude: {:.6f}".format(coords[0], coords[1]))
                except UnicodeError:
                    pass  # Ignore malformed lines
    except Exception as e:
        print("GPS read error:", e)

# === Main Loop ===
print("📡 Starting GPS read loop...")
while True:
    read_gps()
    time.sleep(2)
