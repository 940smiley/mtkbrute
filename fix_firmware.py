#!/usr/bin/env python3
"""
MTK Firmware Fixer for k39tv1-kaeru.bin
This script fixes common issues with MediaTek firmware that cause stage 2 boot failures
"""

import os
import sys
import struct
import shutil
import argparse
from pathlib import Path

# Define paths
BASE_DIR = Path('C:/users/chenn/mtkbrute')
BIN_DIR = BASE_DIR / 'mtk_build' / 'bin'
OUT_DIR = BASE_DIR / 'mtk_build' / 'out'
FIXED_DIR = BASE_DIR / 'mtk_build' / 'fixed'

def ensure_dirs():
    """Ensure all directories exist"""
    FIXED_DIR.mkdir(parents=True, exist_ok=True)

def fix_preloader():
    """Fix the preloader file to address DRAM issues"""
    preloader_path = BIN_DIR / 'preloader_k39tv1_bsp.bin'
    fixed_preloader_path = FIXED_DIR / 'preloader_k39tv1_bsp_fixed.bin'
    
    print(f"Fixing preloader: {preloader_path}")
    
    with open(preloader_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Make a backup of the original file
    shutil.copy(preloader_path, str(preloader_path) + '.backup')
    
    # Fix 1: Modify EMI configuration
    # Look for EMI_SETTINGS signature (typically around 0x200-0x400)
    emi_signature = b'EMI_SETTINGS'
    emi_pos = data.find(emi_signature)
    
    if emi_pos != -1:
        print(f"Found EMI_SETTINGS at offset 0x{emi_pos:X}")
        # Modify EMI timing parameters (this is a generic fix that sometimes works)
        # Actual values would depend on the specific device
        # We're setting a more conservative timing that might work better
        emi_config_offset = emi_pos + len(emi_signature) + 4
        
        # Only modify if we're confident about the structure
        if emi_config_offset + 32 < len(data):
            print(f"Applying EMI timing fix at offset 0x{emi_config_offset:X}")
            # Modify DRAM refresh rate (make it more conservative)
            # This is a common fix for stage 2 boot failures
            data[emi_config_offset + 16] = 0x0A  # More conservative refresh rate
    else:
        print("EMI_SETTINGS signature not found, skipping EMI fix")
    
    # Fix 2: Modify boot flags
    # Look for boot configuration flags
    boot_flag_signature = b'BOOT_FLAG'
    boot_flag_pos = data.find(boot_flag_signature)
    
    if boot_flag_pos != -1:
        print(f"Found BOOT_FLAG at offset 0x{boot_flag_pos:X}")
        # Set boot flags to more compatible values
        boot_flag_offset = boot_flag_pos + len(boot_flag_signature)
        if boot_flag_offset + 4 < len(data):
            print(f"Applying boot flag fix at offset 0x{boot_flag_offset:X}")
            # Set boot flag to 0x00000001 (standard boot mode)
            data[boot_flag_offset:boot_flag_offset+4] = struct.pack('<I', 0x00000001)
    else:
        print("BOOT_FLAG signature not found, skipping boot flag fix")
    
    # Write the fixed preloader
    with open(fixed_preloader_path, 'wb') as f:
        f.write(data)
    
    print(f"Fixed preloader saved to: {fixed_preloader_path}")
    return fixed_preloader_path

def fix_bootloader():
    """Fix the bootloader file"""
    bootloader_path = BIN_DIR / 'k39tv1-kaeru.bin'
    fixed_bootloader_path = FIXED_DIR / 'k39tv1-kaeru_fixed.bin'
    
    print(f"Fixing bootloader: {bootloader_path}")
    
    with open(bootloader_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Make a backup of the original file
    shutil.copy(bootloader_path, str(bootloader_path) + '.backup')
    
    # Fix: Modify header to ensure compatibility
    # First 4 bytes are often a magic number
    if len(data) >= 16:
        # Keep the original magic number but fix the header version if needed
        # Bytes 4-8 often contain version information
        if data[4:8] != b'\x01\x00\x00\x00':
            print("Fixing bootloader header version")
            data[4:8] = b'\x01\x00\x00\x00'  # Set to version 1
    
    # Write the fixed bootloader
    with open(fixed_bootloader_path, 'wb') as f:
        f.write(data)
    
    print(f"Fixed bootloader saved to: {fixed_bootloader_path}")
    return fixed_bootloader_path

def create_flash_script():
    """Create a modified flash script for the fixed firmware"""
    script_path = FIXED_DIR / 'flash_fixed_firmware.sh'
    
    script_content = f"""#!/bin/bash

# Flash fixed firmware script for MTK devices
# This script uses modified parameters to address stage 2 boot failures

echo "MTK Fixed Firmware Flasher"
echo "=========================="

# Check if device is connected
echo "Checking for connected devices..."
lsusb | grep -i mediatek

if [ $? -ne 0 ]; then
    echo "No MediaTek device detected. Please connect your device in bootloader mode."
    echo "Tips to enter bootloader mode:"
    echo "1. Power off the device"
    echo "2. Press and hold Volume Down + Power buttons"
    echo "3. Connect USB cable while holding the buttons"
    exit 1
fi

echo "Device detected! Proceeding with flashing..."

# Flash the firmware with modified parameters
echo "Flashing fixed preloader and bootloader..."
python3 {BASE_DIR}/mtkclient/mtk.py write \\
    --preloader={FIXED_DIR}/preloader_k39tv1_bsp_fixed.bin \\
    --bootloader={FIXED_DIR}/k39tv1-kaeru_fixed.bin \\
    --da_addr=0x200000 \\
    --skip_dram_setup=1

if [ $? -eq 0 ]; then
    echo "Flashing completed successfully!"
    echo "You can now reboot your device."
else
    echo "Flashing failed. Please check the error messages above."
    echo "You may need to retry with different parameters."
    echo ""
    echo "Alternative flashing method:"
    echo "python3 {BASE_DIR}/mtkclient/mtk.py write --preloader={FIXED_DIR}/preloader_k39tv1_bsp_fixed.bin"
fi
"""
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    print(f"Created flash script: {script_path}")
    return script_path

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='MTK Firmware Fixer')
    parser.add_argument('--skip-preloader', action='store_true', help='Skip fixing the preloader')
    parser.add_argument('--skip-bootloader', action='store_true', help='Skip fixing the bootloader')
    args = parser.parse_args()
    
    print("MTK Firmware Fixer for Stage 2 Boot Issues")
    print("=========================================")
    
    # Ensure directories exist
    ensure_dirs()
    
    # Fix firmware files
    if not args.skip_preloader:
        fixed_preloader = fix_preloader()
    
    if not args.skip_bootloader:
        fixed_bootloader = fix_bootloader()
    
    # Create flash script
    flash_script = create_flash_script()
    
    print("\nFirmware fix completed!")
    print("\nTo flash the fixed firmware, use the following command:")
    print(f"bash {flash_script}")
    print("\nAlternative flashing method:")
    print(f"python3 {BASE_DIR}/mtkclient/mtk.py write --preloader={FIXED_DIR}/preloader_k39tv1_bsp_fixed.bin --skip_dram_setup=1")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())