#!/usr/bin/env python3
# MTK Brute Force Connection Script

import os
import sys
import time
import logging
from datetime import datetime
import glob
from mtkclient.Library.Connection.usblib import UsbClass
from mtkclient.Library.Connection.Connection import Connection
from mtkclient.Library.Port import Port
from mtkclient.config.usb_ids import default_ids

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logfile = os.path.join(log_dir, f"mtk_brute_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logfile),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MTK_BRUTE")

def log(message):
    logger.info(message)
    print(message)

def find_da_files():
    """Find all DA files in the repository"""
    da_files = []
    
    # Look in common locations
    search_paths = [
        "/workspaces/mtkbrute/mtkclient/mtkclient/Loader/Preloader/*.bin",
        "/workspaces/mtkbrute/*.bin",
        "/workspaces/mtkbrute/mtk_build/out/*.bin"
    ]
    
    for path in search_paths:
        da_files.extend(glob.glob(path))
    
    log(f"Found {len(da_files)} DA/preloader files")
    return da_files

def try_connection(preloader=None):
    """Try to connect with optional preloader"""
    cdc = UsbClass(portconfig=default_ids, loglevel=logging.INFO, devclass=10)
    port = Port(cdc, logging.INFO)
    connection = Connection(port, logging.INFO)
    
    try:
        if connection.connect(preloader=preloader):
            mtk = connection.mtk
            if mtk is not None:
                log(f"CONNECTION SUCCESSFUL!")
                if preloader:
                    log(f"Using preloader: {os.path.basename(preloader)}")
                else:
                    log("Connected without specific preloader")
                
                # Log device info
                log(f"Device HW code: {hex(mtk.config.hwcode)}")
                log(f"Device HW sub code: {hex(mtk.config.hwsubcode)}")
                log(f"Device HW version: {hex(mtk.config.hwver)}")
                log(f"Device SW version: {hex(mtk.config.swver)}")
                log(f"Device chip name: {mtk.config.chipconfig.name}")
                
                # Try to read BROM and preloader if possible
                try:
                    if hasattr(mtk, "port") and mtk.port.cdc.connected:
                        log("Attempting to dump BROM info...")
                        brom_start = mtk.config.chipconfig.brom_payload_addr
                        if brom_start:
                            brom_data = mtk.preloader.read32(brom_start, 4)
                            log(f"BROM data at {hex(brom_start)}: {[hex(x) for x in brom_data]}")
                except Exception as e:
                    log(f"Error reading BROM: {str(e)}")
                
                connection.close()
                return True, mtk.config.chipconfig.name
            else:
                log("Connected but MTK object is None")
        else:
            if preloader:
                log(f"Failed to connect with {os.path.basename(preloader)}")
            else:
                log("Failed to connect without specific preloader")
    except Exception as e:
        if preloader:
            log(f"Error with {os.path.basename(preloader)}: {str(e)}")
        else:
            log(f"Connection error: {str(e)}")
    
    try:
        connection.close()
    except:
        pass
    
    return False, None

def main():
    log("MTK Brute Force Connection Tool")
    log("==============================")
    log("This tool will try to connect to your MediaTek device using different preloader files")
    log(f"Results will be logged to: {logfile}")
    
    # First try without specific preloader
    log("\nAttempting connection without specific preloader...")
    success, chipname = try_connection()
    
    if success:
        log(f"\nSUCCESS! Detected chipset: {chipname}")
        log("You can use this information to select the correct preloader for your device")
        return
    
    # If that fails, try with each preloader
    log("\nTrying with specific preloader files...")
    da_files = find_da_files()
    
    successful_preloaders = []
    
    for i, da_file in enumerate(da_files):
        preloader_name = os.path.basename(da_file)
        log(f"\n[{i+1}/{len(da_files)}] Trying with: {preloader_name}")
        
        success, chipname = try_connection(da_file)
        if success:
            successful_preloaders.append((da_file, chipname))
        
        # Wait a bit before trying the next preloader
        time.sleep(1)
    
    # Report results
    log("\n\n=== FINAL RESULTS ===")
    if successful_preloaders:
        log(f"Successfully connected with {len(successful_preloaders)} preloader(s):")
        for preloader, chipname in successful_preloaders:
            log(f"- {os.path.basename(preloader)} (Chipset: {chipname})")
        
        # Recommend the first successful preloader
        recommended = os.path.basename(successful_preloaders[0][0])
        log(f"\nRECOMMENDED PRELOADER: {recommended}")
        log(f"Use this preloader for future operations with mtkclient")
    else:
        log("Failed to connect with any preloader. Try the following:")
        log("1. Make sure your device is in preloader/bootrom mode")
        log("2. Check USB connections")
        log("3. Try different USB ports")
        log("4. Make sure you have the correct drivers installed")

if __name__ == "__main__":
    main()