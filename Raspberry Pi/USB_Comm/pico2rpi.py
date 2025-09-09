
import time
import usb_cdc

def send_message(counter):
    if usb_cdc.data:
        message = f"Hello from Pico: {counter}\n"
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
    send_message(counter)
    receive_message()
    counter += 1
    time.sleep(5)
