#!/usr/bin/env python3
# Simple DA File Scanner
# This script scans DA files to extract board and chipset information

import os
import sys
import glob
import struct
import binascii
import re
from datetime import datetime

def setup_logging():
    """Setup basic logging to file"""
    # Use absolute path for Windows
    base_dir = "C:\\Users\\chenn\\mtkbrute"
    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logfile = os.path.join(log_dir, f"da_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    return logfile

def log_message(logfile, message):
    """Log a message to both console and file"""
    print(message)
    with open(logfile, "a") as f:
        f.write(f"{message}\n")

def find_da_files():
    """Find all potential DA files in the repository"""
    da_files = []
    
    # Use absolute path for Windows
    base_dir = "C:\\Users\\chenn\\mtkbrute"
    
    # Look in common locations
    search_paths = [
        os.path.join(base_dir, "*.bin"),
        os.path.join(base_dir, "mtkclient", "mtkclient", "Loader", "*.bin"),
        os.path.join(base_dir, "mtkclient", "mtkclient", "payloads", "*.bin")
    ]
    
    for path in search_paths:
        files = glob.glob(path)
        # Filter for likely DA files (containing "DA" in filename or specific patterns)
        for file in files:
            filename = os.path.basename(file).lower()
            if "da" in filename or "download" in filename:
                da_files.append(file)
    
    return da_files

def extract_hwcode_from_file(file_path):
    """Try to extract hardware codes from binary file"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # Look for common MediaTek hardware codes in binary data
        # Common MT65xx, MT67xx, MT68xx, MT81xx, MT83xx series
        common_hwcodes = [
            0x6572, 0x6582, 0x6592, 0x6595, 0x6735, 0x6737, 0x6739, 0x6755, 
            0x6757, 0x6761, 0x6763, 0x6765, 0x6768, 0x6771, 0x6779, 0x6785, 
            0x6797, 0x6799, 0x6833, 0x6853, 0x6873, 0x6877, 0x6885, 0x6893, 
            0x8127, 0x8163, 0x8167, 0x8168, 0x8173, 0x8183, 0x8195
        ]
        
        found_hwcodes = []
        
        # Search for hardware codes in binary
        for hwcode in common_hwcodes:
            # Search for hwcode as 2-byte value
            hwcode_bytes = struct.pack("<H", hwcode)
            positions = [m.start() for m in re.finditer(re.escape(hwcode_bytes), data)]
            
            if positions:
                found_hwcodes.append((hwcode, positions))
        
        return found_hwcodes
    
    except Exception as e:
        return []

def extract_strings_from_file(file_path):
    """Extract readable strings from binary file that might indicate board/chipset info"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Look for strings that might indicate board or chipset names
        # MediaTek boards often have patterns like "MT6739", "MT8163", etc.
        patterns = [
            rb'MT\d{4}',           # MT followed by 4 digits (e.g., MT6739)
            rb'[A-Za-z0-9_]+_[A-Za-z0-9_]+',  # Words with underscore (common in board names)
            rb'[Bb]oard[A-Za-z0-9_]+',  # Anything with "board" in it
            rb'[Cc]hipset[A-Za-z0-9_]+'   # Anything with "chipset" in it
        ]
        
        found_strings = []
        
        for pattern in patterns:
            matches = re.findall(pattern, data)
            for match in matches:
                try:
                    # Try to decode as string
                    decoded = match.decode('utf-8', errors='ignore')
                    if len(decoded) > 3 and decoded not in found_strings:  # Minimum length and no duplicates
                        found_strings.append(decoded)
                except:
                    pass
        
        return found_strings
    
    except Exception as e:
        return []

def analyze_da_files():
    """Analyze each DA file to extract board and chipset information"""
    logfile = setup_logging()
    log_message(logfile, "Starting DA file analysis...")
    
    # Get all DA files
    da_files = find_da_files()
    log_message(logfile, f"Found {len(da_files)} potential DA files")
    
    # Results dictionary
    results = {}
    
    # Test each DA file
    for da_file in da_files:
        da_name = os.path.basename(da_file)
        log_message(logfile, f"\nAnalyzing DA file: {da_name}")
        
        # Extract hardware codes
        hwcodes = extract_hwcode_from_file(da_file)
        
        # Extract strings that might indicate board/chipset
        strings = extract_strings_from_file(da_file)
        
        # Filter strings to find likely board/chipset names
        board_chipset_strings = []
        for s in strings:
            # Look for common patterns in board/chipset names
            if (re.search(r'MT\d{4}', s) or  # MT followed by 4 digits
                re.search(r'[Bb]oard', s) or  # Contains "board"
                re.search(r'[Cc]hipset', s) or  # Contains "chipset"
                re.search(r'[Pp]latform', s)):  # Contains "platform"
                board_chipset_strings.append(s)
        
        # Store results
        results[da_name] = {
            "path": da_file,
            "size": os.path.getsize(da_file),
            "hwcodes": [f"0x{code[0]:04X}" for code in hwcodes] if hwcodes else [],
            "board_chipset_strings": board_chipset_strings
        }
        
        # Log findings
        log_message(logfile, f"File size: {results[da_name]['size']} bytes")
        
        if results[da_name]['hwcodes']:
            log_message(logfile, f"Found hardware codes: {', '.join(results[da_name]['hwcodes'])}")
        else:
            log_message(logfile, "No hardware codes found")
            
        if results[da_name]['board_chipset_strings']:
            log_message(logfile, "Potential board/chipset identifiers:")
            for s in results[da_name]['board_chipset_strings']:
                log_message(logfile, f"  - {s}")
        else:
            log_message(logfile, "No board/chipset identifiers found")
    
    # Summarize results
    log_message(logfile, "\n\n=== DA ANALYSIS SUMMARY ===")
    log_message(logfile, f"Total DA files analyzed: {len(results)}")
    
    # Group files by hardware codes
    hwcode_groups = {}
    for da_name, info in results.items():
        for hwcode in info['hwcodes']:
            if hwcode not in hwcode_groups:
                hwcode_groups[hwcode] = []
            hwcode_groups[hwcode].append(da_name)
    
    if hwcode_groups:
        log_message(logfile, "\nFiles grouped by hardware code:")
        for hwcode, files in hwcode_groups.items():
            log_message(logfile, f"{hwcode}: {', '.join(files)}")
    
    log_message(logfile, f"\nDetailed results saved to: {logfile}")
    return results

if __name__ == "__main__":
    print("MTK DA File Scanner")
    print("==================")
    print("This tool will scan DA files to extract board and chipset information.")
    print("No device connection required - this is a static analysis tool.")
    
    print("\nStarting analysis process...")
    analyze_da_files()