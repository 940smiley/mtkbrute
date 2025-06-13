#!/usr/bin/env python3
import os
import sys
import time
import serial
import serial.tools.list_ports

def find_mtk_port():
    """Find MediaTek COM port"""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "MediaTek" in port.description or "VCOM" in port.description:
            return port.device
    return None

def prepare_device():
    """Prepare device for SP Flash Tool"""
    port = find_mtk_port()
    
    if not port:
        print("No MediaTek COM port found.")
        return False
    
    print(f"Found MediaTek port: {port}")
    
    try:
        # Open serial connection
        ser = serial.Serial(port, 115200, timeout=5, write_timeout=10)
        
        # Send BROM handshake
        print("Sending BROM handshake...")
        ser.write(b'\xA0\x0A\x50\x05')
        time.sleep(1)
        response = ser.read(4)
        print(f"Response: {response.hex() if response else 'No response'}")
        
        # Send special command to fix 0xC0010001 error
        print("Sending special command to fix 0xC0010001 error...")
        ser.write(b'\xD1\x00\x00\x00\x00\x00\x00\x00')
        time.sleep(1)
        
        # Close and reopen connection
        ser.close()
        time.sleep(1)
        ser = serial.Serial(port, 115200, timeout=5, write_timeout=10)
        
        # Send BROM handshake again
        print("Sending BROM handshake again...")
        ser.write(b'\xA0\x0A\x50\x05')
        time.sleep(1)
        response = ser.read(4)
        print(f"Response: {response.hex() if response else 'No response'}")
        
        # Keep connection open for SP Flash Tool
        print("\nDevice prepared for SP Flash Tool.")
        print("Now quickly open SP Flash Tool and click Download.")
        print("This window will close in 10 seconds...")
        
        # Close connection after 10 seconds
        time.sleep(10)
        ser.close()
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("MediaTek SP Flash Tool Helper")
    print("============================")
    print("This tool prepares your device for SP Flash Tool")
    print("to fix the 0xC0010001 error.")
    print("")
    
    # Install pyserial if needed
    try:
        import serial
    except ImportError:
        print("Installing required package: pyserial")
        os.system("pip install pyserial")
        import serial
    
    prepare_device()
