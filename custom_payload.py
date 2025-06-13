#!/usr/bin/env python3
import os
import sys
import struct
import binascii

def create_patched_payload():
    # Paths to your files
    preloader_path = "C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin"
    bootloader_path = "C:/users/chenn/mtkbrute/mtk_build/out/k39tv1-kaeru.bin"
    brom_path = "C:/users/chenn/mtkbrute/mtk_build/bin/brom_MT6739_MT6731_MT8765_699.bin"
    output_path = "C:/users/chenn/mtkbrute/custom_payload.bin"
    
    # Read files
    with open(preloader_path, 'rb') as f:
        preloader_data = f.read()
    
    with open(bootloader_path, 'rb') as f:
        bootloader_data = f.read()
    
    with open(brom_path, 'rb') as f:
        brom_data = f.read()
    
    # Create payload header
    header = b'MTK_DOWNLOAD_AGENT'
    
    # Create payload with authentication bypass
    payload = bytearray()
    payload.extend(header)
    
    # Add authentication bypass (replace hash check with always return true)
    auth_bypass = bytes.fromhex('00207047')  # ARM Thumb instruction: MOVS R0, #0; BX LR
    
    # Find authentication check in BROM
    auth_offset = find_auth_pattern(brom_data)
    if auth_offset != -1:
        print(f"Found authentication check at offset: 0x{auth_offset:X}")
        
        # Create patch
        patch = bytearray()
        patch.extend(struct.pack('<I', auth_offset))  # Address to patch
        patch.extend(struct.pack('<I', len(auth_bypass)))  # Length of patch
        patch.extend(auth_bypass)  # Patch data
        
        payload.extend(patch)
    
    # Add DA bypass (skip DRAM setup)
    da_bypass = bytes.fromhex('0120704700207047')  # MOVS R0, #1; BX LR; MOVS R0, #0; BX LR
    
    # Find DA check in preloader
    da_offset = find_da_pattern(preloader_data)
    if da_offset != -1:
        print(f"Found DA check at offset: 0x{da_offset:X}")
        
        # Create patch
        patch = bytearray()
        patch.extend(struct.pack('<I', da_offset))  # Address to patch
        patch.extend(struct.pack('<I', len(da_bypass)))  # Length of patch
        patch.extend(da_bypass)  # Patch data
        
        payload.extend(patch)
    
    # Add payload terminator
    payload.extend(b'\x00\x00\x00\x00')
    
    # Write custom payload
    with open(output_path, 'wb') as f:
        f.write(payload)
    
    print(f"Custom payload written to: {output_path}")
    print("Use this payload with: python mtk.py payload --filename=custom_payload.bin")

def find_auth_pattern(data):
    # Common authentication check patterns in MediaTek BROMs
    patterns = [
        b'\x4F\xF0\x00\x30\x07\x4A\x13\x68',  # MT6739 auth check
        b'\x4F\xF0\x01\x30\x07\x4A\x13\x68',  # Alternative pattern
        b'\x00\x20\x70\x47\x01\x20\x70\x47'   # Return true pattern
    ]
    
    for pattern in patterns:
        offset = data.find(pattern)
        if offset != -1:
            return offset
    
    # If not found, return a common offset for MT6739
    return 0x102A8

def find_da_pattern(data):
    # Common DA check patterns in MediaTek preloaders
    patterns = [
        b'\xD0\xF8\x00\x80\xB8\xF1\x00\x0F',  # MT6739 DA check
        b'\x01\x20\x70\x47\x00\x20\x70\x47',  # Return pattern
        b'\x2D\xE9\xF0\x41\x0E\x46\x15\x46'   # DA init function
    ]
    
    for pattern in patterns:
        offset = data.find(pattern)
        if offset != -1:
            return offset
    
    # If not found, return a common offset for MT6739 preloaders
    return 0x1024

if __name__ == "__main__":
    create_patched_payload()
