
import board
import busio
import time
# === Debug Toggle ===
debug = False  # Set to True to enable debug prints
# === Coordinate Change Detection ===
def coords_changed(new, old, threshold=0.00001):
    if not old:
        return True
    return abs(new[0] - old[0]) > threshold or abs(new[1] - old[1]) > threshold
# === GPS UART Setup ===
try:
    gps_uart = busio.UART(tx=board.GP4, rx=board.GP5, baudrate=9600)
except Exception as e:
    if debug: print("UART init failed:", e)
    gps_uart = None

def parse_lat_lon(raw_lat, lat_dir, raw_lon, lon_dir):
    try:
        raw_lat = raw_lat.strip(); raw_lon = raw_lon.strip()
        lat_dir = lat_dir.strip(); lon_dir = lon_dir.strip()
        lat_deg = int(raw_lat[:2]); lat_min = float(raw_lat[2:])
        lat = lat_deg + lat_min / 60.0
        if lat_dir == 'S': lat = -lat
        lon_deg = int(raw_lon[:3]); lon_min = float(raw_lon[3:])
        lon = lon_deg + lon_min / 60.0
        if lon_dir == 'W': lon = -lon
        if debug: print(f"Parsed lat/lon: {lat:.8f}, {lon:.8f}")
        return (lat, lon)
    except Exception as e:
        if debug: print(f"Exception in parse_lat_lon: {e}")
        return None

def parse_gpgga(sentence):
    try:
        parts = sentence.split(',')
        if parts[0] != "$GPGGA": return None
        return parse_lat_lon(parts[2], parts[3], parts[4], parts[5])
    except Exception as e:
        if debug: print(f"Exception in parse_gpgga: {e}")
        return None

def parse_gprmc(sentence):
    try:
        parts = sentence.split(',')
        if parts[0] != "$GPRMC" or parts[2] != 'A': return None
        return parse_lat_lon(parts[3], parts[4], parts[5], parts[6])
    except Exception as e:
        if debug: print(f"Exception in parse_gprmc: {e}")
        return None

def parse_gpgll(sentence):
    try:
        parts = sentence.split(',')
        if parts[0] != "$GPGLL" or parts[6] != 'A': return None
        return parse_lat_lon(parts[1], parts[2], parts[3], parts[4])
    except Exception as e:
        if debug: print(f"Exception in parse_gpgll: {e}")
        return None
# === Read and return one set of coordinates (blocking) ===
def get_lat_lon():
    if not gps_uart:
        return None
    while True:
        line = gps_uart.readline()
        if not line:
            continue
        try:
            sentence = line.decode('utf-8').strip()
            coords = None
            if sentence.startswith("$GPGGA"):
                coords = parse_gpgga(sentence)
            elif sentence.startswith("$GPRMC"):
                coords = parse_gprmc(sentence)
            elif sentence.startswith("$GPGLL"):
                coords = parse_gpgll(sentence)
            if coords:
                return coords
        except Exception as e:
            if debug: print("Exception in get_lat_lon:", e)
            continue
# === Non-blocking poll helper ===
def poll_lat_lon(max_lines=10):
    """Try up to max_lines; return (lat, lon) or None without blocking forever."""
    if not gps_uart:
        return None
    for _ in range(max_lines):
        line = gps_uart.readline()
        if not line:
            continue
        try:
            sentence = line.decode('utf-8').strip()
            coords = None
            if sentence.startswith("$GPGGA"):
                coords = parse_gpgga(sentence)
            elif sentence.startswith("$GPRMC"):
                coords = parse_gprmc(sentence)
            elif sentence.startswith("$GPGLL"):
                coords = parse_gpgll(sentence)
            if coords:
                return coords
        except Exception:
            continue
    return None

if __name__ == "__main__":
    last_coords = None
    while True:
        coordinates = get_lat_lon()
        if coordinates and coords_changed(coordinates, last_coords):
            print(f"	Current GPS Location: Latitude={coordinates[0]:.8f}, Longitude={coordinates[1]:.8f}")
            last_coords = coordinates
        elif not coordinates:
            print("Failed to retrieve GPS coordinates.")
