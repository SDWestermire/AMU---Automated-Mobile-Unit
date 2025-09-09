import serial
import time

# Update the port to use the new data channel, likely ttyACM1
SERIAL_PORT = '/dev/ttyACM1'
BAUD_RATE = 115200

def send_and_receive():
    counter = 100
    try:
        # Use the correct port for the data channel
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        ser.reset_input_buffer()
        time.sleep(2)

        while True:
            # Send the command with a counter to the Pico
            command_str = f"Message from Pi: {counter}\n"
            ser.write(command_str.encode('utf-8'))
            print(f"Sent: {command_str.strip()}")
            counter += 1

            # Read all available lines from the Pico
            while ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"\tReceived from Pico: {line}")
            
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
