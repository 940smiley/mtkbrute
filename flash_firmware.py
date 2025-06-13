#!/usr/bin/env python3
# Script to connect to MediaTek device and flash firmware

import os
import sys
import time
import subprocess
import glob
import argparse

# Configuration
CONFIG = {
    "firmware_dir": "firmware_dump",  # Directory containing firmware files
    "output_dir": "output",           # Output directory
    "da_files_dir": "output/da_files", # Directory with DA files and preloaders
    "retry_count": 3,                 # Number of connection retries
    "timeout": 60                     # Connection timeout in seconds
}

def log(message):
    """Print log message"""
    print(f"[*] {message}")

def error(message):
    """Print error message and exit"""
    print(f"[!] ERROR: {message}")
    sys.exit(1)

def run_command(cmd, cwd=None, timeout=None):
    """Run shell command and return output"""
    try:
        log(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, timeout=timeout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout} seconds")
        return None

def find_files(directory, pattern):
    """Find files matching pattern in directory"""
    matches = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if pattern.lower() in filename.lower():
                matches.append(os.path.join(root, filename))
    return matches

def connect_to_device(preloader=None, da_file=None):
    """Connect to MediaTek device in bootrom/preloader mode"""
    log("Attempting to connect to device...")
    
    # Try to use mtkclient for connection
    try:
        import sys
        # Add mtkclient to path if it exists in the current directory
        if os.path.exists("mtkclient"):
            sys.path.insert(0, "mtkclient")
        
        from mtkclient.Library.Port import Port
        from mtkclient.Library.Connection.Connection import Connection
        from mtkclient.Library.utils import LogBase
        from mtkclient.Library.Connection.usblib import UsbClass
        from mtkclient.config.usb_ids import default_ids
        
        # Initialize connection
        log("Initializing connection...")
        cdc = UsbClass(portconfig=default_ids, loglevel=0, devclass=10)
        port = Port(cdc, 0)
        connection = Connection(port, 0)
        
        # Try to connect
        for attempt in range(CONFIG["retry_count"]):
            log(f"Connection attempt {attempt + 1}/{CONFIG['retry_count']}...")
            if connection.connect(preloader=preloader):
                log("Connected to device!")
                mtk = connection.mtk
                if mtk is not None:
                    log(f"Device HW code: {hex(mtk.config.hwcode)}")
                    log(f"Device HW sub code: {hex(mtk.config.hwsubcode)}")
                    log(f"Device HW version: {hex(mtk.config.hwver)}")
                    log(f"Device SW version: {hex(mtk.config.swver)}")
                    log(f"Device chip name: {mtk.config.chipconfig.name}")
                    return connection
            time.sleep(2)
        
        error("Failed to connect to device after multiple attempts")
    except ImportError:
        log("mtkclient library not found, falling back to command line tools...")
        # Try using command line tools as fallback
        try:
            # Check if device is in fastboot mode
            fastboot_devices = run_command(["fastboot", "devices"])
            if fastboot_devices and len(fastboot_devices.strip()) > 0:
                log("Device detected in fastboot mode")
                return "fastboot"
            
            # Check if device is in ADB mode
            adb_devices = run_command(["adb", "devices"])
            if adb_devices and "device" in adb_devices:
                log("Device detected in ADB mode")
                # Try to reboot to bootloader
                run_command(["adb", "reboot", "bootloader"])
                time.sleep(5)
                fastboot_devices = run_command(["fastboot", "devices"])
                if fastboot_devices and len(fastboot_devices.strip()) > 0:
                    log("Device rebooted to fastboot mode")
                    return "fastboot"
            
            error("Could not connect to device. Please ensure device is connected and in bootrom/preloader/fastboot mode")
        except Exception as e:
            error(f"Failed to connect to device: {str(e)}")

def flash_firmware(connection, args):
    """Flash firmware to device"""
    log("Preparing to flash firmware...")
    
    # Check connection type
    if connection == "fastboot":
        flash_with_fastboot(args)
    else:
        flash_with_mtkclient(connection, args)

def flash_with_fastboot(args):
    """Flash firmware using fastboot"""
    log("Flashing with fastboot...")
    
    # Find firmware files
    boot_img = args.boot or find_files(CONFIG["firmware_dir"], "boot.img")[0] if find_files(CONFIG["firmware_dir"], "boot.img") else None
    system_img = args.system or find_files(CONFIG["firmware_dir"], "system.img")[0] if find_files(CONFIG["firmware_dir"], "system.img") else None
    vendor_img = args.vendor or find_files(CONFIG["firmware_dir"], "vendor.img")[0] if find_files(CONFIG["firmware_dir"], "vendor.img") else None
    
    # Flash boot image
    if boot_img and os.path.exists(boot_img):
        log(f"Flashing boot image: {boot_img}")
        run_command(["fastboot", "flash", "boot", boot_img])
    else:
        log("No boot image found, skipping...")
    
    # Flash system image
    if system_img and os.path.exists(system_img):
        log(f"Flashing system image: {system_img}")
        run_command(["fastboot", "flash", "system", system_img])
    else:
        log("No system image found, skipping...")
    
    # Flash vendor image
    if vendor_img and os.path.exists(vendor_img):
        log(f"Flashing vendor image: {vendor_img}")
        run_command(["fastboot", "flash", "vendor", vendor_img])
    else:
        log("No vendor image found, skipping...")
    
    # Reboot device if requested
    if args.reboot:
        log("Rebooting device...")
        run_command(["fastboot", "reboot"])
    
    log("Flashing completed!")

def flash_with_mtkclient(connection, args):
    """Flash firmware using mtkclient"""
    log("Flashing with mtkclient...")
    
    try:
        from mtkclient.Library.DA.mtk_da_cmd import DA_handler
        
        mtk = connection.mtk
        
        # Initialize DA handler
        da_handler = DA_handler(mtk, 0)
        
        # Setup DA connection
        if not da_handler.setup():
            error("Failed to setup DA connection")
        
        log("DA setup successful")
        log(f"DA version: {da_handler.da_version}")
        
        # Find firmware files
        boot_img = args.boot or find_files(CONFIG["firmware_dir"], "boot.img")[0] if find_files(CONFIG["firmware_dir"], "boot.img") else None
        system_img = args.system or find_files(CONFIG["firmware_dir"], "system.img")[0] if find_files(CONFIG["firmware_dir"], "system.img") else None
        
        # Flash boot partition
        if boot_img and os.path.exists(boot_img):
            log(f"Flashing boot image: {boot_img}")
            if not da_handler.flash_partition("boot", boot_img):
                log("Failed to flash boot partition")
        else:
            log("No boot image found, skipping...")
        
        # Flash system partition
        if system_img and os.path.exists(system_img):
            log(f"Flashing system image: {system_img}")
            if not da_handler.flash_partition("system", system_img):
                log("Failed to flash system partition")
        else:
            log("No system image found, skipping...")
        
        # Reboot device if requested
        if args.reboot:
            log("Rebooting device...")
            da_handler.reboot()
        
        # Close connection
        connection.close()
        
        log("Flashing completed!")
    
    except Exception as e:
        error(f"Error during flashing: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MediaTek Firmware Flasher")
    parser.add_argument("--preloader", help="Path to preloader file")
    parser.add_argument("--da", help="Path to DA file")
    parser.add_argument("--boot", help="Path to boot image")
    parser.add_argument("--system", help="Path to system image")
    parser.add_argument("--vendor", help="Path to vendor image")
    parser.add_argument("--reboot", action="store_true", help="Reboot device after flashing")
    args = parser.parse_args()
    
    log("MediaTek Firmware Flasher")
    
    # Find preloader and DA files if not specified
    preloader = args.preloader
    da_file = args.da
    
    if not preloader:
        preloader_files = find_files(CONFIG["da_files_dir"], "preloader")
        if preloader_files:
            preloader = preloader_files[0]
            log(f"Using preloader: {os.path.basename(preloader)}")
    
    if not da_file:
        da_files = find_files(CONFIG["da_files_dir"], "da") + find_files(CONFIG["da_files_dir"], "download_agent")
        if da_files:
            da_file = da_files[0]
            log(f"Using DA file: {os.path.basename(da_file)}")
    
    # Connect to device
    connection = connect_to_device(preloader, da_file)
    
    # Flash firmware
    flash_firmware(connection, args)

if __name__ == "__main__":
    main()
