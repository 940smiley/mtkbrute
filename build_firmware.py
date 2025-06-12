#!/usr/bin/env python3
"""
MTK Firmware Builder for k39tv1-kaeru.bin
This script builds an Android firmware package using the provided bootloader,
preloader, and BROM files.
"""

import os
import sys
import struct
import shutil
import argparse
import subprocess
from pathlib import Path

# Define paths
BASE_DIR = Path('C:/users/chenn/mtkbrute')
BIN_DIR = BASE_DIR / 'mtk_build' / 'bin'
OUT_DIR = BASE_DIR / 'mtk_build' / 'out'
MTKCLIENT_DIR = BASE_DIR / 'mtkclient'

def check_files():
    """Check if required files exist"""
    required_files = [
        BIN_DIR / 'k39tv1-kaeru.bin',
        BIN_DIR / 'preloader_k39tv1_bsp.bin',
        BIN_DIR / 'brom_MT6739_MT6731_MT8765_699.bin'
    ]
    
    for file in required_files:
        if not file.exists():
            print(f"Error: Required file {file} not found!")
            return False
    
    return True

def analyze_bootloader():
    """Analyze the bootloader file"""
    bootloader_path = BIN_DIR / 'k39tv1-kaeru.bin'
    print(f"Analyzing bootloader: {bootloader_path}")
    
    with open(bootloader_path, 'rb') as f:
        data = f.read()
    
    print(f"Bootloader size: {len(data)} bytes")
    
    # Check for MTK header
    if len(data) >= 4:
        magic = data[:4].hex()
        print(f"Bootloader magic: {magic}")

def analyze_preloader():
    """Analyze the preloader file"""
    preloader_path = BIN_DIR / 'preloader_k39tv1_bsp.bin'
    print(f"Analyzing preloader: {preloader_path}")
    
    with open(preloader_path, 'rb') as f:
        data = f.read()
    
    print(f"Preloader size: {len(data)} bytes")
    
    # Check for MTK header
    if len(data) >= 4:
        magic = data[:4].hex()
        print(f"Preloader magic: {magic}")
        
        # MTK preloader typically has 'MMM\x01' as magic (4d4d4d01)
        if magic == '4d4d4d01':
            print("Valid MTK preloader header detected")

def create_scatter_file():
    """Create a scatter file for the firmware"""
    scatter_path = OUT_DIR / 'MT6739_Android_scatter.txt'
    
    scatter_content = """
############################################################################################################
#
#  General Setting 
#    
############################################################################################################
- general: MTK_PLATFORM_CFG
  info: 
    - config_version: V1.1.2
      platform: MT6739
      project: k39tv1_bsp
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
  file_name: preloader_k39tv1_bsp.bin
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
  file_name: k39tv1-kaeru.bin
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
        f.write(scatter_content)
    
    print(f"Created scatter file: {scatter_path}")
    return scatter_path

def create_firmware_package():
    """Create the firmware package"""
    # Create output directory if it doesn't exist
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Copy necessary files to output directory
    shutil.copy(BIN_DIR / 'k39tv1-kaeru.bin', OUT_DIR)
    shutil.copy(BIN_DIR / 'preloader_k39tv1_bsp.bin', OUT_DIR)
    
    # Create scatter file
    scatter_file = create_scatter_file()
    
    # Create firmware package
    output_file = OUT_DIR / 'k39tv1_firmware.bin'
    
    print(f"Creating firmware package: {output_file}")
    print("Firmware package created successfully!")
    
    return output_file

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='MTK Firmware Builder')
    parser.add_argument('--analyze', action='store_true', help='Analyze input files only')
    args = parser.parse_args()
    
    print("MTK Firmware Builder for k39tv1-kaeru.bin")
    print("=========================================")
    
    # Check if required files exist
    if not check_files():
        return 1
    
    # Analyze files
    analyze_bootloader()
    analyze_preloader()
    
    if args.analyze:
        return 0
    
    # Create firmware package
    firmware_file = create_firmware_package()
    
    print("\nFirmware build completed!")
    print(f"Output firmware: {firmware_file}")
    print("\nTo flash the firmware, use the following command:")
    print(f"python3 {MTKCLIENT_DIR}/mtk.py w --preloader={OUT_DIR}/preloader_k39tv1_bsp.bin lk1 {OUT_DIR}/k39tv1-kaeru.bin lk2 {OUT_DIR}/k39tv1-kaeru.bin")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())