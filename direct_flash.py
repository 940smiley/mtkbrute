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

def direct_flash():
    """Direct flash method bypassing mtkclient"""
    preloader_path = "C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin"
    
    # Read preloader
    with open(preloader_path, 'rb') as f:
        preloader_data = f.read()
    
    print("Looking for MediaTek COM port...")
    port = find_mtk_port()
    
    if not port:
        print("No MediaTek COM port found. Please:")
        print("1. Power off your device")
        print("2. Press and hold Volume Down")
        print("3. Connect USB while holding the button")
        print("4. Wait 5 seconds and release")
        input("Press Enter when ready to try again...")
        port = find_mtk_port()
        
        if not port:
            print("Still no MediaTek COM port found. Please check your device connection.")
            return False
    
    print(f"Found MediaTek port: {port}")
    
    try:
        # Open serial connection with longer timeout
        ser = serial.Serial(port, 115200, timeout=5, write_timeout=10)
        
        # Send BROM commands
        print("Sending BROM handshake...")
        ser.write(b'\xA0\x0A\x50\x05')  # BROM handshake
        time.sleep(1)
        response = ser.read(4)
        
        if response != b'\x5F\xF5\xAF\xFA':
            print(f"Unexpected response: {response.hex()}")
            print("Trying alternative approach...")
            
            # Try alternative handshake
            ser.write(b'\x5A\x00\x00\x01')
            time.sleep(1)
            response = ser.read(4)
        
        print(f"Response: {response.hex()}")
        
        # Send enable flash command
        print("Enabling flash write...")
        ser.write(b'\xD6\x00\x00\x00\x01\x00\x00\x00')
        time.sleep(1)
        response = ser.read(4)
        print(f"Enable response: {response.hex()}")
        
        # Send write command
        print("Sending write command...")
        cmd = bytearray([0xD7, 0x00, 0x00, 0x00])  # Write command
        cmd.extend(len(preloader_data).to_bytes(4, byteorder='little'))  # Size
        cmd.extend((0x00000000).to_bytes(4, byteorder='little'))  # Address (EMMC_BOOT1)
        ser.write(cmd)
        time.sleep(1)
        response = ser.read(4)
        print(f"Write command response: {response.hex()}")
        
        # Send preloader data in chunks
        print("Sending preloader data in chunks...")
        chunk_size = 4096
        for i in range(0, len(preloader_data), chunk_size):
            chunk = preloader_data[i:i+chunk_size]
            ser.write(chunk)
            time.sleep(0.5)
            print(f"Sent chunk {i//chunk_size + 1}/{(len(preloader_data) + chunk_size - 1)//chunk_size}")
        
        time.sleep(2)
        print("Preloader sent. Checking response...")
        response = ser.read(4)
        print(f"Final response: {response.hex()}")
        
        # Send reboot command
        print("Sending reboot command...")
        ser.write(b'\x0B\x00\x00\x00')
        time.sleep(1)
        
        ser.close()
        print("Direct flash completed. Please reboot your device.")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("MediaTek Direct Flash Tool")
    print("=========================")
    print("This tool attempts to flash the preloader directly via serial.")
    print("")
    
    # Install pyserial if needed
    try:
        import serial
    except ImportError:
        print("Installing required package: pyserial")
        os.system("pip install pyserial")
        import serial
    
    direct_flash()
