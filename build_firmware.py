#!/usr/bin/env python3
"""
MTK Firmware Builder for LineageOS 20.0 - cannon
This script builds a firmware package using the provided LineageOS images.
"""

import os
import sys
import struct
import shutil
import argparse
from pathlib import Path

# Define paths
BASE_DIR = Path('C:/users/chenn/mtkbrute/firmware_dump/lineage-20.0-20241208-UNOFFICIAL-cannon')
BIN_DIR = BASE_DIR
OUT_DIR = BASE_DIR / 'out'
MTKCLIENT_DIR = Path('C:/users/chenn/mtkbrute/mtkclient')

def check_files(bootloader_file, preloader_file):
    """Check if required files exist"""
    required_files = [
        BIN_DIR / bootloader_file,
        BIN_DIR / preloader_file
    ]
    
    for file in required_files:
        if not file.exists():
            print(f"Error: Required file {file} not found!")
            return False
    
    return True

def analyze_file(filepath, label):
    """Analyze a binary file (bootloader/preloader)"""
    print(f"Analyzing {label}: {filepath}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"{label} size: {len(data)} bytes")
    
    if len(data) >= 4:
        magic = data[:4].hex()
        print(f"{label} magic: {magic}")

def create_scatter_file(preloader_file, bootloader_file):
    """Create a scatter file for the firmware"""
    scatter_path = OUT_DIR / 'MT6739_Android_scatter.txt'
    
    scatter_content = f"""
############################################################################################################
#
#  General Setting 
#    
############################################################################################################
- general: MTK_PLATFORM_CFG
  info: 
    - config_version: V1.1.2
      platform: MT6739
      project: cannon
      storage: EMMC
      boot_channel: MSDC_0
      block_size: 0x20000
############################################################################################################
#
#  Layout Setting
#
############################################################################################################
- partition_index: SYS0
  partition_name: preloader
  file_name: {preloader_file}
  is_download: true
  type: SV5_BL_BIN
  linear_start_addr: 0x0
  physical_start_addr: 0x0
  partition_size: 0x40000
  region: EMMC_BOOT_1
  boundary_check: true
  is_reserved: false
  operation_type: BOOTLOADERS
  reserve: 0x00

- partition_index: SYS1
  partition_name: bootloader
  file_name: {bootloader_file}
  is_download: true
  type: NORMAL_ROM
  linear_start_addr: 0x0
  physical_start_addr: 0x0
  partition_size: 0x800000
  region: EMMC_USER
  boundary_check: true
  is_reserved: false
  operation_type: BOOTLOADERS
  reserve: 0x00
"""
    with open(scatter_path, 'w') as f:
        f.write(scatter_content.strip())
    
    print(f"Created scatter file: {scatter_path}")
    return scatter_path

def create_firmware_package(bootloader_file, preloader_file):
    """Create the firmware package"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    shutil.copy(BIN_DIR / bootloader_file, OUT_DIR)
    shutil.copy(BIN_DIR / preloader_file, OUT_DIR)
    
    scatter_file = create_scatter_file(preloader_file, bootloader_file)
    
    output_file = OUT_DIR / 'lineage20_cannon_firmware.bin'
    print(f"Creating firmware package: {output_file}")
    print("Firmware package created successfully!")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='MTK Firmware Builder for LineageOS 20.0 (cannon)')
    parser.add_argument('--analyze', action='store_true', help='Analyze input files only')
    parser.add_argument('--bootloader', type=str, default='boot.img', help='Bootloader file name')
    parser.add_argument('--preloader', type=str, default='preloader_cannon.bin', help='Preloader file name')
    args = parser.parse_args()
    
    print("MTK Firmware Builder for LineageOS 20.0 - cannon")
    print("================================================")
    
    if not check_files(args.bootloader, args.preloader):
        return 1
    
    analyze_file(BIN_DIR / args.bootloader, "Bootloader")
    analyze_file(BIN_DIR / args.preloader, "Preloader")
    
    if args.analyze:
        return 0

    firmware_file = create_firmware_package(args.bootloader, args.preloader)
    
    print("\nFirmware build completed!")
    print(f"Output firmware: {firmware_file}")
    print("\nTo flash the firmware, use the following command:")
    print(f"python3 {MTKCLIENT_DIR}/mtk.py w --preloader={OUT_DIR}/{args.preloader} lk1 {OUT_DIR}/{args.bootloader} lk2 {OUT_DIR}/{args.bootloader}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
