#!/usr/bin/env python3
import os
import sys
import time
import serial
import serial.tools.list_ports
import subprocess

def find_mtk_port():
    """Find MediaTek COM port"""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "MediaTek" in port.description or "VCOM" in port.description:
            return port.device, port.description
    return None, None

def remap_com_port():
    """Remap MediaTek COM port to COM1"""
    port, description = find_mtk_port()
    
    if not port:
        print("No MediaTek COM port found.")
        return False
    
    print(f"Found MediaTek port: {port} - {description}")
    
    # Extract COM number
    com_number = port.replace("COM", "")
    
    try:
        # Create registry file to remap port
        reg_file = "C:/users/chenn/mtkbrute/remap_com.reg"
        with open(reg_file, "w") as f:
            f.write('Windows Registry Editor Version 5.00\n\n')
            f.write('[HKEY_LOCAL_MACHINE\\HARDWARE\\DEVICEMAP\\SERIALCOMM]\n')
            f.write(f'"\\\\Device\\\\{description}"="COM1"\n')
        
        # Apply registry changes
        print(f"Remapping {port} to COM1...")
        subprocess.run(["regedit", "/s", reg_file], shell=True)
        
        print("Port remapped. Please:")
        print("1. Disconnect and reconnect your device")
        print("2. Open Device Manager and check if COM1 appears")
        print("3. Now use SP Flash Tool with COM1")
        
        return True
        
    except Exception as e:
        print(f"Error remapping port: {str(e)}")
        return False

def port_forwarder():
    """Forward data between COM ports"""
    source_port, description = find_mtk_port()
    
    if not source_port:
        print("No MediaTek COM port found.")
        return False
    
    print(f"Found MediaTek port: {source_port}")
    print("Starting port forwarding from COM17 to COM1...")
    
    try:
        # Create virtual COM port pair using com0com if available
        # Otherwise, manually forward data between ports
        source = serial.Serial(source_port, 115200, timeout=1)
        dest = serial.Serial("COM1", 115200, timeout=1)
        
        print("Port forwarding active. You can now use SP Flash Tool with COM1.")
        print("Press Ctrl+C to stop forwarding.")
        
        while True:
            # Forward data from source to destination
            if source.in_waiting:
                data = source.read(source.in_waiting)
                dest.write(data)
            
            # Forward data from destination to source
            if dest.in_waiting:
                data = dest.read(dest.in_waiting)
                source.write(data)
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nStopping port forwarding...")
    except Exception as e:
        print(f"Error during port forwarding: {str(e)}")
    finally:
        try:
            source.close()
            dest.close()
        except:
            pass
    
    return True

def main():
    print("MediaTek COM Port Tool")
    print("=====================")
    print("1. Try to remap COM17 to COM1 (requires admin rights)")
    print("2. Try to use virtual port forwarding")
    print("3. Download com0com virtual serial port driver")
    print("4. Exit")
    
    choice = input("Enter your choice (1-4): ")
    
    if choice == "1":
        remap_com_port()
    elif choice == "2":
        try:
            port_forwarder()
        except Exception as e:
            print(f"Error: {str(e)}")
            print("You may need to install com0com virtual serial port driver.")
    elif choice == "3":
        print("Opening com0com download page...")
        os.system("start https://sourceforge.net/projects/com0com/")
        print("After installing com0com, use its setup tool to create a virtual pair between COM17 and COM1")
    else:
        print("Exiting...")

if __name__ == "__main__":
    # Install pyserial if needed
    try:
        import serial
    except ImportError:
        print("Installing required package: pyserial")
        os.system("pip install pyserial")
        import serial
    
    main()
