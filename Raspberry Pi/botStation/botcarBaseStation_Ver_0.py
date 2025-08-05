import serial
import time
from datetime import datetime

# Initialize LoRa serial communication
lora = serial.Serial("/dev/ttyS0", 115200, timeout=1)

# In-memory fleet tracking
fleet_registry = {}

def send_ack(node_id, status='ACK'):
    """Respond to a specific node with ACK or NACK."""
    msg = f"{status}-{node_id}"
    payload = f"AT+SEND={node_id},{len(msg)},{msg}\r\n"
    lora.write(payload.encode('utf-8'))
    time.sleep(0.5)
    response = lora.read(lora.inWaiting()).decode()
    print(f"Sent {status} to Node {node_id}: {response}")

def parse_message(line):
    """Extract message contents from LoRa packet."""
    if line.startswith("+RCV="):
        try:
            raw = line[len("+RCV="):]
            parts = raw.split(',')

            if len(parts) >= 5:
                node_id, msg_len, payload, rssi, snr = parts[:5]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save to fleet registry
                fleet_registry[node_id] = {
                    'payload': payload,
                    'rssi': rssi,
                    'snr': snr,
                    'last_seen': timestamp
                }

                print(f"[{timestamp}] Node {node_id}: GPS={payload}, RSSI={rssi}, SNR={snr}")
                
                # Deploy ACK
                send_ack(node_id, 'ACK')
            else:
                print(f"Malformed incoming packet: {line}")
                send_ack(node_id, 'NACK')
        except Exception as e:
            print(f"Error parsing message: {e}")
            send_ack(node_id, 'NACK')

def monitor_serial_data():
    """Main receive loop."""
    print(f"Listening on {lora.port} at {lora.baudrate} baud...")

    try:
        while True:
            if lora.in_waiting > 0:
                raw_line = lora.readline().decode('utf-8').strip()
                if raw_line:
                    parse_message(raw_line)
            time.sleep(0.1)  # Avoid CPU spike
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    finally:
        print("Stopping serial monitor.")
        lora.close()

def setup_station():
    """Initial LoRa configuration."""
    cmds = [
        b'AT+NETWORKID=6\r\n',
        b'AT+ADDRESS=1\r\n',
        b'AT+NETWORKID?\r\n',
        b'AT+ADDRESS?\r\n',
        b'AT+BAND?\r\n'
    ]

    for cmd in cmds:
        lora.write(cmd)
        time.sleep(1)
        response = lora.read(lora.inWaiting()).decode()
        print(response.strip())

# Run setup and start monitoring
setup_station()
monitor_serial_data()