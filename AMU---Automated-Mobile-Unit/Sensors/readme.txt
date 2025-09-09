Created with circuitpython for the Raspberry Pi Pico - any version
There are four files but only two are necessary:

a.  GPS_All_Display_CircuitPython - will provide a full NMEA sentence presentation
b.  IMU_Calibration_CircuitPython - is the full BNO055 IMU code base
c.  imu_bno055.py - LOAD THIS TO PICO - final optimized IMU code
d.  GPS_LatLon.py - LOAD THIS TO PICO - final optimized GPS code

Note that all four may live safely on the Pico.  Items a and b were/are created for independent sensor testing.
