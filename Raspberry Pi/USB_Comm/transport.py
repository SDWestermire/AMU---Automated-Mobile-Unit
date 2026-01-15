# Transport.py - USB CDC communication handler for Pico→Pi
# Version: 1.0
# Date: 2026-01-14
# Author: Gunny / Claude

import usb_cdc
import json
import time

class PicoTransport:
    """
    Handles bidirectional USB CDC serial communication between Pico and Pi.
    Sends telemetry to Pi, receives commands from Pi.
    """
    
    def __init__(self, debug=False):
        self.debug = debug
        self.last_command = None
        
        # Verify USB CDC data channel is available
        if not usb_cdc.data:
            print("[Transport] ERROR: usb_cdc.data not available. Check boot.py!")
            self.enabled = False
        else:
            self.enabled = True
            if self.debug:
                print("[Transport] USB CDC data channel ready.")
    
    def send_telemetry(self, telemetry_dict):
        """
        Send telemetry dictionary as JSON line to Pi.
        
        Args:
            telemetry_dict: Dictionary containing sensor data
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Convert to compact JSON with newline terminator
            message = json.dumps(telemetry_dict, separators=(",", ":")) + "\n"
            usb_cdc.data.write(message.encode('utf-8'))
            
            if self.debug:
                print(f"[Transport] Sent: {message.strip()}")
            
            return True
        except Exception as e:
            print(f"[Transport] Send error: {e}")
            return False
    
    def receive_command(self):
        """
        Non-blocking check for incoming command from Pi.
        
        Returns:
            str: Command string if available, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            if usb_cdc.data.in_waiting > 0:
                line = usb_cdc.data.readline()
                if line:
                    command = line.strip().decode('utf-8')
                    self.last_command = command
                    
                    if self.debug:
                        print(f"[Transport] Received: {command}")
                    
                    return command
        except Exception as e:
            print(f"[Transport] Receive error: {e}")
        
        return None
    
    def get_last_command(self):
        """Return the last received command."""
        return self.last_command
    
    def is_ready(self):
        """Check if transport is enabled and ready."""
        return self.enabled