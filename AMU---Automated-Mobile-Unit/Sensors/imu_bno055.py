
# imu_bno055.py  — CircuitPython minimal BNO055 driver (drift-hardened)
import time
import board
import busio

# --- BNO055 Registers & Constants (Page 0 unless noted) ---
BNO055_ADDR      = 0x28

# Data output
EULER_REG        = 0x1A

# Raw magnetometer (for diagnostics)
MAG_X_LSB        = 0x0E
MAG_X_MSB        = 0x0F
MAG_Y_LSB        = 0x10
MAG_Y_MSB        = 0x11
MAG_Z_LSB        = 0x12
MAG_Z_MSB        = 0x13

# Config & status
UNIT_SEL_REG     = 0x3B
OPR_MODE_REG     = 0x3D
PWR_MODE_REG     = 0x3E
SYS_TRIGGER_REG  = 0x3F
CALIB_STAT_REG   = 0x35
SYS_STAT_REG     = 0x39
SYS_ERR_REG      = 0x3A
# Offsets & radii (22 bytes total)
ACC_OFF_X_LSB    = 0x55  # through 0x6A

# Operation modes
CONFIGMODE           = 0x00
ACCONLY_MODE         = 0x01
MAGONLY_MODE         = 0x02
GYRONLY_MODE         = 0x03
AMG_MODE             = 0x07
IMUPLUS_MODE         = 0x08   # IMU fusion (no mag)
COMPASS_MODE         = 0x09   # accel + mag fusion
NDOF_FMC_OFF_MODE    = 0x0B   # NDOF with Fast Mag Cal OFF
NDOF_MODE            = 0x0C   # full fusion

# User-tunable roll bias
ROLL_OFFSET_DEG  = 1.88

MODE_NAME_TO_CODE = {
    "CONFIG": CONFIGMODE,
    "ACCONLY": ACCONLY_MODE,
    "MAGONLY": MAGONLY_MODE,
    "GYRONLY": GYRONLY_MODE,
    "AMG": AMG_MODE,
    "IMUPLUS": IMUPLUS_MODE,
    "COMPASS": COMPASS_MODE,
    "NDOF_FMC_OFF": NDOF_FMC_OFF_MODE,
    "NDOF": NDOF_MODE,
}

class BNO055IMU:
    """
    Minimal BNO055 driver using direct register IO (CircuitPython busio).
    Adds: external crystal enable, calibration offset persistence, mode select, raw mag read.
    """

    def __init__(self, i2c: busio.I2C = None, sda=board.GP0, scl=board.GP1, debug=False):
        self.debug = debug
        self.addr = BNO055_ADDR

        # I2C init
        if i2c is None:
            self.i2c = busio.I2C(scl=scl, sda=sda)
            while not self.i2c.try_lock():
                pass
            self._owned_bus = True
        else:
            self.i2c = i2c
            self._owned_bus = False

        # Optional roll low-pass filter
        self.roll_lpf_alpha = None
        self._roll_lpf_state = None

        # Track current mode (for info)
        self._mode = NDOF_MODE

    # ---------- I2C helpers ----------
    def _writeto_mem(self, reg, data_bytes):
        try:
            self.i2c.writeto(self.addr, bytes([reg]) + data_bytes)
        except Exception as e:
            if self.debug:
                print("BNO055 write error @", hex(reg), e)

    def _readfrom_mem(self, reg, nbytes):
        try:
            # Two-phase register select then read
            self.i2c.writeto(self.addr, bytes([reg]))
            time.sleep(0.001)
            out = bytearray(nbytes)
            self.i2c.readfrom_into(self.addr, out)
            return out
        except Exception as e:
            if self.debug:
                print("BNO055 read error @", hex(reg), e)
            return bytearray(nbytes)

    # ---------- Mode & features ----------
    def set_mode(self, mode):
        """Switch operation mode with required CONFIG step & settle delays."""
        self._writeto_mem(OPR_MODE_REG, bytes([CONFIGMODE]))
        time.sleep(0.02)
        self._writeto_mem(OPR_MODE_REG, bytes([mode]))
        time.sleep(0.1)
        self._mode = mode
        if self.debug:
            print("[IMU] set_mode ->", hex(mode))

    def select_mode(self, name: str):
        """Set by name: 'NDOF', 'NDOF_FMC_OFF', 'COMPASS', 'IMUPLUS', etc."""
        code = MODE_NAME_TO_CODE.get(name.upper(), NDOF_MODE)
        self.set_mode(code)

    def use_external_crystal(self, enable=True):
        """
        Enable external 32.768 kHz crystal (if present):
        Write SYS_TRIGGER=0x80 in CONFIG mode, then return to the current op mode.
        """
        # Go to CONFIG
        self._writeto_mem(OPR_MODE_REG, bytes([CONFIGMODE])); time.sleep(0.02)
        self._writeto_mem(SYS_TRIGGER_REG, bytes([0x80 if enable else 0x00]))
        time.sleep(0.01)
        # Return to previously selected mode
        self._writeto_mem(OPR_MODE_REG, bytes([self._mode])); time.sleep(0.1)
        if self.debug:
            print("[IMU] External crystal:", "ENABLED" if enable else "DISABLED")

    # ---------- Public API ----------
    def initialize(self, mode_name="NDOF", ext_crystal=True):
        """Set units/power, select mode, and enable external crystal by default."""
        if self.debug:
            print("[IMU] Initializing...")
        # Units default (deg, C) and normal power
        self._writeto_mem(OPR_MODE_REG, bytes([CONFIGMODE])); time.sleep(0.025)
        self._writeto_mem(PWR_MODE_REG, bytes([0x00]));       time.sleep(0.01)
        self._writeto_mem(UNIT_SEL_REG, bytes([0x00]))
        self._writeto_mem(SYS_TRIGGER_REG, bytes([0x00]));    time.sleep(0.01)

        # Choose op mode (default NDOF)
        self.select_mode(mode_name)

        # Try external crystal (optional)
        if ext_crystal:
            self.use_external_crystal(True)

        if self.debug:
            mode = self._readfrom_mem(OPR_MODE_REG, 1)[0]
            print("[IMU] Mode:", hex(mode))

    def read_calibration_status(self):
        """Return tuple (sys, gyro, accel, mag) each 0..3."""
        calib = self._readfrom_mem(CALIB_STAT_REG, 1)[0]
        sys  = (calib >> 6) & 0x03
        gyro = (calib >> 4) & 0x03
        accel= (calib >> 2) & 0x03
        mag  = calib & 0x03
        if self.debug:
            print(f"[IMU] Calib SYS:{sys} GYR:{gyro} ACC:{accel} MAG:{mag}")
        return sys, gyro, accel, mag

    def wait_until_calibrated(self, poll_interval=0.5):
        """Block until all subsystems report calibrated (3)."""
        if self.debug:
            print("[IMU] Waiting for full calibration (3/3/3/3)...")
        while True:
            sys, gyro, accel, mag = self.read_calibration_status()
            if all(v == 3 for v in (sys, gyro, accel, mag)):
                if self.debug:
                    print("[IMU] Fully calibrated!")
                return
            time.sleep(poll_interval)

    def set_roll_lpf(self, alpha=None):
        """Optional low-pass filter for roll. alpha in (0,1]; lower = more smoothing."""
        self.roll_lpf_alpha = alpha
        self._roll_lpf_state = None

    @staticmethod
    def _to_signed_16(val):
        return val - 65536 if val > 32767 else val

    @staticmethod
    def heading_to_compass(heading_deg):
        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        idx = int((heading_deg + 11.25) % 360 // 22.5)
        return dirs[idx]

    def read_euler(self):
        """
        Return (heading_deg, roll_deg, pitch_deg, compass_str).
        BNO055 Euler format: 16 LSB/deg; heading unsigned, roll/pitch signed.
        """
        data = self._readfrom_mem(EULER_REG, 6)
        raw_heading = (data[1] << 8) | data[0]
        raw_roll    = (data[3] << 8) | data[2]
        raw_pitch   = (data[5] << 8) | data[4]

        heading = raw_heading / 16.0
        roll    = self._to_signed_16(raw_roll) / 16.0 + ROLL_OFFSET_DEG
        pitch   = self._to_signed_16(raw_pitch) / 16.0

        # Optional LPF on roll
        if self.roll_lpf_alpha and 0.0 < self.roll_lpf_alpha <= 1.0:
            if self._roll_lpf_state is None:
                self._roll_lpf_state = roll
            else:
                a = self.roll_lpf_alpha
                self._roll_lpf_state = a * roll + (1 - a) * self._roll_lpf_state
            roll_out = self._roll_lpf_state
        else:
            roll_out = roll

        compass = self.heading_to_compass(heading)
        return heading, roll_out, pitch, compass

    # ---- Diagnostics / persistence ----
    def read_mag_raw(self):
        """Return raw magnetometer (x,y,z) in LSB units."""
        data = self._readfrom_mem(MAG_X_LSB, 6)
        x = self._to_signed_16((data[1] << 8) | data[0])
        y = self._to_signed_16((data[3] << 8) | data[2])
        z = self._to_signed_16((data[5] << 8) | data[4])
        return x, y, z

    def get_offsets(self):
        """
        Read 22-byte calibration blob (acc/mag/gyr offsets + radii).
        Must be in CONFIG mode for access reliability.
        """
        self._writeto_mem(OPR_MODE_REG, bytes([CONFIGMODE])); time.sleep(0.02)
        raw = self._readfrom_mem(ACC_OFF_X_LSB, 22)
        self._writeto_mem(OPR_MODE_REG, bytes([self._mode])); time.sleep(0.1)
        return bytes(raw)

    def set_offsets(self, blob: bytes):
        """
        Restore 22-byte calibration blob previously read by get_offsets().
        Must be in CONFIG mode to write.
        """
        if not blob or len(blob) != 22:
            if self.debug: print("[IMU] set_offsets: invalid blob (need 22 bytes)")
            return
        self._writeto_mem(OPR_MODE_REG, bytes([CONFIGMODE])); time.sleep(0.02)
        self._writeto_mem(ACC_OFF_X_LSB, blob); time.sleep(0.01)
        self._writeto_mem(OPR_MODE_REG, bytes([self._mode])); time.sleep(0.1)
        if self.debug: print("[IMU] Offsets restored.")

    def deinit(self):
        if self._owned_bus:
            try:
                self.i2c.unlock()
            except Exception:
                pass
if __name__ == "__main__":
    imu = BNO055IMU(debug=True)
    imu.initialize(mode_name="NDOF", ext_crystal=True)
    imu.wait_until_calibrated()
    print("Offsets length:", len(imu.get_offsets()))
