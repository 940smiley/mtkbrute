#!/usr/bin/env python3
import os
import sys
import time
import serial
import serial.tools.list_ports
from datetime import datetime

def find_mtk_port():
    """Find MediaTek COM port"""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "MediaTek" in port.description or "VCOM" in port.description:
            return port.device
    return None

def establish_connection(port):
    """Establish connection with the device"""
    try:
        # Open serial connection
        ser = serial.Serial(port, 115200, timeout=5, write_timeout=10)
        
        # Send BROM handshake
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending BROM handshake...")
        ser.write(b'\xA0\x0A\x50\x05')
        time.sleep(1)
        response = ser.read(4)
        
        if response == b'\x5F\xF5\xAF\xFA':
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Handshake successful: {response.hex()}")
            
            # Send enable flash command
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Enabling flash write...")
            ser.write(b'\xD6\x00\x00\x00\x01\x00\x00\x00')
            time.sleep(1)
            response = ser.read(4)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Enable response: {response.hex() if response else 'No response'}")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Device ready for SP Flash Tool")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Keeping connection alive...")
            return ser
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Handshake failed: {response.hex() if response else 'No response'}")
            ser.close()
            return None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error establishing connection: {str(e)}")
        return None

def monitor_connection():
    """Monitor for device connection and maintain it"""
    print("MediaTek Connection Monitor")
    print("==========================")
    print("This tool will continuously monitor for MediaTek device connections")
    print("and automatically establish a connection when detected.")
    print("You can use SP Flash Tool while this script is running.")
    print("")
    print("Press Ctrl+C to exit.")
    print("")
    
    active_connection = None
    last_port = None
    
    try:
        while True:
            # Check if we have an active connection
            if active_connection:
                try:
                    # Try to send a keep-alive command
                    active_connection.write(b'\xA0\x0A\x50\x05')
                    response = active_connection.read(1)
                    if not response:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection lost, will reconnect when device is available...")
                        active_connection.close()
                        active_connection = None
                except Exception:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection error, will reconnect when device is available...")
                    try:
                        active_connection.close()
                    except:
                        pass
                    active_connection = None
            
            # If no active connection, look for a device
            if not active_connection:
                port = find_mtk_port()
                if port:
                    if port != last_port:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] MediaTek device found on {port}")
                        last_port = port
                    
                    # Try to establish connection
                    active_connection = establish_connection(port)
                else:
                    if last_port:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Device disconnected, waiting for reconnection...")
                        last_port = None
            
            # Sleep before next check
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        if active_connection:
            active_connection.close()

if __name__ == "__main__":
    # Install pyserial if needed
    try:
        import serial
    except ImportError:
        print("Installing required package: pyserial")
        os.system("pip install pyserial")
        import serial
    
    monitor_connection()
