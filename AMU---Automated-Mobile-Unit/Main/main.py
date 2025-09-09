# main.py
import time
import json
import usb_cdc

from imu_bno055 import BNO055IMU
from GPS_LatLon import get_lat_lon

# --- Config ---
ROLL_LPF_ALPHA = 0.30
GPS_STABLE_SAMPLES = 3
GPS_MAX_WAIT_S = 300
TELEMETRY_PERIOD_S = 0.5
PRINT_PERIOD_S = 0.5

def _send_to_pi(obj: dict):
    if not usb_cdc.data:
        return
    line = json.dumps(obj, separators=(",", ":")) + "\n"
    usb_cdc.data.write(line.encode("utf-8"))

def _wait_for_imu_calibration(imu: BNO055IMU):
    print("[STARTUP] Initializing IMU...")
    imu.initialize()
    if ROLL_LPF_ALPHA:
        imu.set_roll_lpf(alpha=ROLL_LPF_ALPHA)
    print("[STARTUP] Waiting for IMU calibration (move the botcar: rotate, tilt, figure-8)...")
    imu.wait_until_calibrated(poll_interval=0.5)
    print("[STARTUP] IMU calibrated.")

def _wait_for_gps_fix(min_samples=GPS_STABLE_SAMPLES, max_wait_s=GPS_MAX_WAIT_S):
    print("[STARTUP] Waiting for GPS fix...")
    got = 0
    start = time.monotonic()
    last = None
    while True:
        coords = get_lat_lon()  # blocking until parsed coords
        if not coords:
            continue
        if last is None:
            got = 1
            last = coords
        else:
            lat, lon = coords
            l2, g2 = last
            drift = abs(lat - l2) + abs(lon - g2)
            if drift < 0.0005:
                got += 1
                last = coords
            else:
                got = 1
                last = coords
        if got >= min_samples:
            print(f"[STARTUP] GPS fix acquired. lat={last[0]:.6f}, lon={last[1]:.6f}")
            return last
        if max_wait_s is not None and (time.monotonic() - start) > max_wait_s:
            raise TimeoutError("Timed out waiting for GPS fix")

def main():
    print("=== AMU Pico Startup ===")
    # Explicitly initialize lat/lon so prints are unambiguous
    lat, lon = None, None

    # 1) IMU calibration
    imu = BNO055IMU(debug=False)
    _wait_for_imu_calibration(imu)

    # 2) GPS fix
    try:
        lat, lon = _wait_for_gps_fix()
    except TimeoutError as e:
        print(f"[STARTUP] {e}. Stopping here.")
        while True:
            time.sleep(1)

    # 3) Announce readiness
    _send_to_pi({"v": 1, "type": "hello", "role": "pico", "status": "ready"})
    print("[RUN] Sensors ready. Starting telemetry stream to Pi...")

    last_tx = 0.0
    last_print = 0.0
    while True:
        heading, roll, pitch, compass = imu.read_euler()

        coords = get_lat_lon()  # blocking; returns latest valid coord
        if coords:
            lat, lon = coords

        now = time.monotonic()

        if now - last_tx >= TELEMETRY_PERIOD_S:
            last_tx = now
            _send_to_pi({
                "v": 1, "type": "telemetry", "ts": now,
                "imu": {"heading": heading, "compass": compass, "roll": roll, "pitch": pitch},
                "gps": {"lat": lat, "lon": lon}
            })

        if now - last_print >= PRINT_PERIOD_S:
            last_print = now
            if (lat is not None) and (lon is not None):
                gps_str = f"GPS: lat={lat:.6f} lon={lon:.6f}"
            else:
                gps_str = "GPS: NO FIX"
            imu_str = f"IMU: Heading={heading:6.2f}° ({compass}) Roll={roll:6.2f}° Pitch={pitch:6.2f}°"
            print(gps_str + "\n" + imu_str)

        time.sleep(0.05)

if __name__ == "__main__":
    main()
