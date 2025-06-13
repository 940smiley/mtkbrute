#!/usr/bin/env python3
# Script to patch boot images with Magisk using WSL

import os
import sys
import shutil
import subprocess
import tempfile
import requests
import zipfile

# Configuration
CONFIG = {
    "output_dir": "output/magisk",  # Output directory for patched images
}

def log(message):
    """Print log message"""
    print(f"[*] {message}")

def error(message):
    """Print error message and exit"""
    print(f"[!] ERROR: {message}")
    sys.exit(1)

def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    try:
        log(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {e.stderr}")
        return None

def check_wsl():
    """Check if WSL is available"""
    try:
        result = subprocess.run(["wsl", "--status"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def download_magisk():
    """Download latest Magisk APK"""
    log("Downloading Magisk...")
    
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    magisk_apk = os.path.join(CONFIG["output_dir"], "magisk.apk")
    
    # Get latest release info from GitHub API
    try:
        response = requests.get("https://api.github.com/repos/topjohnwu/Magisk/releases/latest")
        data = response.json()
        
        # Find APK download URL
        apk_url = None
        for asset in data["assets"]:
            if asset["name"].endswith(".apk") and "debug" not in asset["name"]:
                apk_url = asset["browser_download_url"]
                break
        
        if not apk_url:
            error("Could not find Magisk APK download URL")
        
        # Download APK
        log(f"Downloading Magisk from {apk_url}")
        response = requests.get(apk_url)
        with open(magisk_apk, "wb") as f:
            f.write(response.content)
    except Exception as e:
        error(f"Failed to download Magisk: {str(e)}")
    
    return magisk_apk

def patch_boot_with_magisk_wsl(boot_img):
    """Patch boot image with Magisk using WSL"""
    if not check_wsl():
        error("WSL is not available. Please install WSL first.")
    
    # Create output directory
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    
    # Download Magisk APK
    magisk_apk = download_magisk()
    
    # Convert Windows paths to WSL paths
    wsl_boot_img = boot_img.replace("\\", "/")
    if ":" in wsl_boot_img:  # Handle Windows drive letter
        drive = wsl_boot_img[0].lower()
        wsl_boot_img = f"/mnt/{drive}/{wsl_boot_img[3:]}"
    
    wsl_magisk_apk = magisk_apk.replace("\\", "/")
    if ":" in wsl_magisk_apk:
        drive = wsl_magisk_apk[0].lower()
        wsl_magisk_apk = f"/mnt/{drive}/{wsl_magisk_apk[3:]}"
    
    # Create a temporary directory in WSL
    temp_dir = run_command(["wsl", "mktemp", "-d"]).strip()
    
    # Extract Magisk APK in WSL
    log("Extracting Magisk APK in WSL...")
    run_command(["wsl", "unzip", "-q", wsl_magisk_apk, "-d", temp_dir])
    
    # Find Magisk binary
    magisk_bin = run_command(["wsl", "find", temp_dir, "-name", "libmagiskboot.so", "-type", "f"]).strip()
    if not magisk_bin:
        error("Could not find Magisk binary in APK")
    
    # Copy boot image to WSL temp directory
    wsl_boot_copy = f"{temp_dir}/boot.img"
    run_command(["wsl", "cp", wsl_boot_img, wsl_boot_copy])
    
    # Make Magisk binary executable
    run_command(["wsl", "chmod", "+x", magisk_bin])
    
    # Patch boot image
    log("Patching boot image with Magisk...")
    run_command(["wsl", magisk_bin, "unpack", wsl_boot_copy])
    run_command(["wsl", magisk_bin, "repack", wsl_boot_copy])
    
    # Copy patched boot image back to Windows
    patched_boot = os.path.join(CONFIG["output_dir"], f"magisk_patched_{os.path.basename(boot_img)}")
    wsl_patched = f"{temp_dir}/new-boot.img"
    
    # Convert WSL path back to Windows path for copying
    run_command(["wsl", "cp", wsl_patched, wsl_boot_img + ".patched"])
    shutil.copy(boot_img + ".patched", patched_boot)
    os.remove(boot_img + ".patched")
    
    # Clean up
    run_command(["wsl", "rm", "-rf", temp_dir])
    
    log(f"Patched boot image saved to: {patched_boot}")
    return patched_boot

def main():
    """Main function"""
    log("Magisk Boot Image Patcher (WSL)")
    
    # Check if boot image path is provided
    if len(sys.argv) < 2:
        error("Usage: python patch_magisk_wsl.py <path_to_boot_image>")
    
    boot_img = sys.argv[1]
    if not os.path.exists(boot_img):
        error(f"Boot image not found: {boot_img}")
    
    # Patch boot image
    patched_boot = patch_boot_with_magisk_wsl(boot_img)
    log(f"Successfully patched boot image: {patched_boot}")

if __name__ == "__main__":
    main()
