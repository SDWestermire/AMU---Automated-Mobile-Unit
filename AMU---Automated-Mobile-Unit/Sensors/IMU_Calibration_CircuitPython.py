
import board
import busio
import time

#i2c = None

print("? Script started")

# === I2C Setup ===
try:

    global i2c
    i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
    while not i2c.try_lock():
        pass
    print("? I2C initialized")
except Exception as e:
    print("? I2C init failed:", e)

# === BNO055 Setup ===
BNO055_ADDR = 0x28
EULER_REG = 0x1A
OPR_MODE_REG = 0x3D
PWR_MODE_REG = 0x3E
SYS_TRIGGER_REG = 0x3F
UNIT_SEL_REG = 0x3B
CALIB_STAT_REG = 0x35

CONFIGMODE = 0x00
NDOF_MODE = 0x0C

ROLL_OFFSET = 1.88  # degrees, manually measured physical tilt

def writeto_mem(addr, reg, data):
    i2c.writeto(addr, bytes([reg]) + data)

def readfrom_mem(addr, reg, nbytes):
    result = bytearray(nbytes)
    i2c.writeto_then_readfrom(addr, bytes([reg]), result)
    return result


def initialize_imu():
    print("?? Initializing IMU...")
    try:
        writeto_mem(BNO055_ADDR, OPR_MODE_REG, bytes([CONFIGMODE]))
        time.sleep(0.025)
        writeto_mem(BNO055_ADDR, PWR_MODE_REG, bytes([0x00]))
        time.sleep(0.01)
        writeto_mem(BNO055_ADDR, UNIT_SEL_REG, bytes([0x00]))
        writeto_mem(BNO055_ADDR, SYS_TRIGGER_REG, bytes([0x00]))
        time.sleep(0.01)
        writeto_mem(BNO055_ADDR, OPR_MODE_REG, bytes([NDOF_MODE]))
        time.sleep(2)
        mode = readfrom_mem(BNO055_ADDR, OPR_MODE_REG, 1)[0]
        print("? IMU mode set to:", hex(mode))
    except Exception as e:
        print("? IMU init failed:", e)

def read_calibration_status():
    try:
        calib = readfrom_mem(BNO055_ADDR, CALIB_STAT_REG, 1)[0]
        sys = (calib >> 6) & 0x03
        gyro = (calib >> 4) & 0x03
        accel = (calib >> 2) & 0x03
        mag = calib & 0x03
        print(f"Raw calibration byte: {bin(calib)}")
        return sys, gyro, accel, mag
    except Exception as e:
        print("? Calibration read error:", e)
        return 0, 0, 0, 0

def calibrate_imu():
    print("?? Starting BNO055 calibration routine...")
    print("Move the botcar as follows:")
    print("- Gyroscope: Keep still for a few seconds")
    print("- Accelerometer: Tilt in all directions")
    print("- Magnetometer: Draw figure-8s in the air")
    print("- System: Wait until all sensors are calibrated and fusion stabilizes")
    while True:
        sys, gyro, accel, mag = read_calibration_status()
        print(f"?? Calibration -> SYS:{sys} GYR:{gyro} ACC:{accel} MAG:{mag}")
        if sys == 3 and gyro == 3 and accel == 3 and mag == 3:
            print("? IMU fully calibrated!")
            break
        time.sleep(1)

def initialize_gps():
    print("?? GPS initialization not yet implemented.")

def test_ultrasonic():
    print("?? Ultrasonic range test not yet implemented.")

def to_signed(val):
    return val - 65536 if val > 32767 else val

def read_euler_angles():
    print("?? Reading IMU data...")
    try:
        data = readfrom_mem(BNO055_ADDR, EULER_REG, 6)
        heading = (data[1] << 8 | data[0]) / 16.0
        roll = to_signed(data[3] << 8 | data[2]) / 16.0 + ROLL_OFFSET
        pitch = to_signed(data[5] << 8 | data[4]) / 16.0
        print("? Orientation -> Heading: {:.2f}, Roll: {:.2f}, Pitch: {:.2f}".format(
            heading, roll, pitch))
    except Exception as e:
        print("? IMU read error:", e)

def main():
    print("?? Entering main()")
    initialize_imu()
    calibrate_imu()
    initialize_gps()
    test_ultrasonic()
    last_update = time.monotonic()
    update_interval = 0.1  # seconds
    while True:
        now = time.monotonic()
        if now - last_update >= update_interval:
            last_update = now
            read_euler_angles()
        time.sleep(0.01)

main()
