#!/usr/bin/env python3
# Script to extract DA files, preloaders, and generate scatter file

import os
import sys
import shutil
import glob
import subprocess
import re
from datetime import datetime

# Configuration
CONFIG = {
    "firmware_dir": "firmware_dump",  # Directory containing firmware dump
    "output_dir": "output",           # Output directory
}

def log(message):
    """Print log message"""
    print(f"[*] {message}")

def error(message):
    """Print error message and exit"""
    print(f"[!] ERROR: {message}")
    sys.exit(1)

def extract_da_files():
    """Extract DA files and preloaders from firmware"""
    log("Extracting DA files and preloaders from firmware...")
    
    # Create output directory for DA files
    da_output_dir = os.path.join(CONFIG["output_dir"], "da_files")
    os.makedirs(da_output_dir, exist_ok=True)
    
    # Look for DA files in firmware_dump directory
    da_files = []
    preloader_files = []
    scatter_files = []
    
    # Path to firmware dump directory
    firmware_dir = os.path.join(os.getcwd(), CONFIG["firmware_dir"])
    
    # Search for DA, preloader, and scatter files
    for root, _, files in os.walk(firmware_dir):
        for file in files:
            filepath = os.path.join(root, file)
            lower_file = file.lower()
            
            # Look for DA files
            if ("da" in lower_file or "download_agent" in lower_file) and lower_file.endswith(".bin"):
                da_files.append(filepath)
                # Copy to output directory
                dst_file = os.path.join(da_output_dir, file)
                shutil.copy(filepath, dst_file)
                log(f"Found DA file: {file}")
            
            # Look for preloader files
            elif "preloader" in lower_file and lower_file.endswith(".bin"):
                preloader_files.append(filepath)
                # Copy to output directory
                dst_file = os.path.join(da_output_dir, file)
                shutil.copy(filepath, dst_file)
                log(f"Found preloader file: {file}")
            
            # Look for scatter files
            elif file.lower().endswith((".txt", ".xml")) and "scatter" in file.lower():
                scatter_files.append(filepath)
                # Copy to output directory
                dst_file = os.path.join(da_output_dir, file)
                shutil.copy(filepath, dst_file)
                log(f"Found scatter file: {file}")
    
    # If no scatter file found, try to generate one
    if not scatter_files and (da_files or preloader_files):
        generate_scatter_file(da_output_dir, da_files, preloader_files)
    
    # If no DA files found, try to extract from scatter file
    if not da_files and scatter_files:
        extract_da_from_scatter(da_output_dir, scatter_files)
    
    # Generate DA file from preloader if needed and possible
    if not da_files and preloader_files:
        generate_da_from_preloader(da_output_dir, preloader_files)
    
    log(f"Found {len(da_files)} DA files, {len(preloader_files)} preloader files, and {len(scatter_files)} scatter files")
    log(f"Files saved to: {da_output_dir}")
    return da_output_dir

def extract_da_from_scatter(output_dir, scatter_files):
    """Extract DA information from scatter files"""
    log("Extracting DA information from scatter files...")
    
    for scatter_file in scatter_files:
        try:
            with open(scatter_file, 'r', errors='ignore') as f:
                content = f.read()
                
                # Look for DA download agent info in scatter file
                if "download_agent" in content.lower():
                    log(f"Scatter file {os.path.basename(scatter_file)} contains DA information")
                    
                    # Try to extract DA file path
                    da_path_match = re.search(r'download_agent\s*=\s*([^\s;]+)', content, re.IGNORECASE)
                    if da_path_match:
                        da_path = da_path_match.group(1).strip('"\'')
                        log(f"Found DA path in scatter file: {da_path}")
                        
                        # Check if the DA file exists in the firmware directory
                        da_filename = os.path.basename(da_path)
                        for root, _, files in os.walk(CONFIG["firmware_dir"]):
                            for file in files:
                                if file.lower() == da_filename.lower():
                                    src_file = os.path.join(root, file)
                                    dst_file = os.path.join(output_dir, file)
                                    shutil.copy(src_file, dst_file)
                                    log(f"Extracted DA file from scatter reference: {file}")
                    
                    # Save scatter file with DA info
                    info_file = os.path.join(output_dir, f"da_info_from_{os.path.basename(scatter_file)}.txt")
                    with open(info_file, 'w') as out_f:
                        out_f.write(f"DA information extracted from {os.path.basename(scatter_file)}:\n\n")
                        
                        # Extract relevant sections
                        da_section = re.search(r'(download_agent\s*=.+?)(?:\n\s*\n|\Z)', content, re.DOTALL | re.IGNORECASE)
                        if da_section:
                            out_f.write(da_section.group(1) + "\n\n")
                        
                        # Extract platform info if available
                        platform_section = re.search(r'(platform\s*=.+?)(?:\n\s*\n|\Z)', content, re.DOTALL | re.IGNORECASE)
                        if platform_section:
                            out_f.write(platform_section.group(1) + "\n\n")
        
        except Exception as e:
            log(f"Error processing scatter file {os.path.basename(scatter_file)}: {str(e)}")

def generate_da_from_preloader(output_dir, preloader_files):
    """Generate DA file from preloader"""
    log("Attempting to extract DA information from preloader...")
    
    for preloader in preloader_files:
        preloader_name = os.path.basename(preloader)
        info_file = os.path.join(output_dir, f"preloader_info_{preloader_name}.txt")
        
        try:
            # Extract header information from preloader
            with open(preloader, 'rb') as f:
                data = f.read(512)  # Read first 512 bytes for header
                
                # Look for MediaTek header signatures
                if b'MTK' in data or b'EMMC_BOOT' in data:
                    log(f"Found MediaTek signature in preloader: {preloader_name}")
                    
                    # Extract basic info
                    with open(info_file, 'w') as out_f:
                        out_f.write(f"Preloader information for {preloader_name}:\n\n")
                        out_f.write(f"File size: {os.path.getsize(preloader)} bytes\n")
                        
                        # Try to identify chipset from binary patterns
                        chipsets = ["MT6739", "MT6761", "MT6765", "MT6768", "MT6771", 
                                   "MT6785", "MT6833", "MT6853", "MT6873", "MT6877", 
                                   "MT6885", "MT6889", "MT6893", "MT6895"]
                        
                        with open(preloader, 'rb') as bin_f:
                            bin_data = bin_f.read()
                            for chipset in chipsets:
                                if chipset.encode() in bin_data:
                                    out_f.write(f"Possible chipset: {chipset}\n")
                                    log(f"Detected possible chipset {chipset} in {preloader_name}")
        
        except Exception as e:
            log(f"Error analyzing preloader {preloader_name}: {str(e)}")

def generate_scatter_file(output_dir, da_files, preloader_files):
    """Generate a basic scatter file"""
    log("Generating basic scatter file...")
    
    scatter_file = os.path.join(output_dir, "generated_scatter.txt")
    
    with open(scatter_file, 'w') as f:
        f.write(f"# Generated scatter file - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Add platform info if we can determine it
        platform = "MT6895"  # Default to MT6895 for Infinix X6871
        f.write(f"############################################\n")
        f.write(f"# Platform: {platform}\n")
        f.write(f"############################################\n\n")
        
        # Add preloader info
        if preloader_files:
            preloader = os.path.basename(preloader_files[0])
            f.write("- name: preloader\n")
            f.write("  location: preloader\n")
            f.write(f"  file_name: {preloader}\n")
            f.write("  type: preloader\n\n")
        
        # Add DA info
        if da_files:
            da_file = os.path.basename(da_files[0])
            f.write("############################################\n")
            f.write("# Download Agent\n")
            f.write("############################################\n")
            f.write(f"download_agent = {da_file}\n\n")
        
        # Add basic partition info
        f.write("############################################\n")
        f.write("# Partition info\n")
        f.write("############################################\n\n")
        
        partitions = ["boot", "recovery", "system", "vendor", "product", "userdata"]
        for partition in partitions:
            f.write(f"- name: {partition}\n")
            f.write(f"  location: {partition}\n")
            f.write(f"  file_name: {partition}.img\n")
            f.write(f"  type: {partition}\n\n")
    
    log(f"Generated basic scatter file: {scatter_file}")

def main():
    """Main function"""
    log("MediaTek DA and Preloader Extractor")
    
    # Create output directory
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    
    # Create firmware directory if it doesn't exist
    if not os.path.exists(CONFIG["firmware_dir"]):
        os.makedirs(CONFIG["firmware_dir"], exist_ok=True)
        log(f"Created firmware directory: {CONFIG['firmware_dir']}")
        log(f"Please place firmware files in the {CONFIG['firmware_dir']} directory")
        return
    
    # Extract DA files and preloaders
    da_dir = extract_da_files()
    log(f"Extraction complete. Files saved to: {da_dir}")

if __name__ == "__main__":
    main()
