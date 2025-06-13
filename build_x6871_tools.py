#!/usr/bin/env python3
# Script to build TWRP and patch boot image with Magisk for Infinix X6871
# For use with firmware dump

import os
import sys
import shutil
import subprocess
import glob
import json
import tempfile
import zipfile
import requests
from pathlib import Path

# Configuration
DEVICE = "Infinix-X6871"
PLATFORM = "mt6895"
CONFIG = {
    "firmware_dir": "firmware_dump",  # Directory containing firmware dump
    "output_dir": "output",           # Output directory
    "magisk_version": "latest",       # Magisk version to use
    "twrp_branch": "twrp-12.1"        # TWRP branch to use
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

def check_requirements():
    """Check if required tools are installed"""
    log("Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 6):
        error("Python 3.6 or higher is required")
    
    # Check for required tools
    required_tools = ["adb", "fastboot", "unzip", "git"]
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            error(f"{tool} not found. Please install it.")
    
    # Check for firmware directory
    if not os.path.exists(CONFIG["firmware_dir"]):
        error(f"Firmware directory '{CONFIG['firmware_dir']}' not found. Please create it and add firmware files.")
    
    # Create output directory
    os.makedirs(CONFIG["output_dir"], exist_ok=True)

def find_boot_images():
    """Find boot and recovery images in firmware directory"""
    log("Looking for boot and recovery images...")
    
    boot_images = []
    recovery_images = []
    
    # Look for boot.img, recovery.img, and other variations
    for root, _, files in os.walk(CONFIG["firmware_dir"]):
        for file in files:
            filepath = os.path.join(root, file)
            lower_file = file.lower()
            
            if "boot" in lower_file and lower_file.endswith(".img"):
                boot_images.append(filepath)
            elif "recovery" in lower_file and lower_file.endswith(".img"):
                recovery_images.append(filepath)
    
    if not boot_images:
        error("No boot images found in firmware directory")
    
    log(f"Found {len(boot_images)} boot images and {len(recovery_images)} recovery images")
    return boot_images, recovery_images

def download_magisk():
    """Download latest Magisk APK"""
    log("Downloading Magisk...")
    
    magisk_dir = os.path.join(CONFIG["output_dir"], "magisk")
    os.makedirs(magisk_dir, exist_ok=True)
    magisk_apk = os.path.join(magisk_dir, "magisk.apk")
    
    if CONFIG["magisk_version"] == "latest":
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
    else:
        error("Custom Magisk versions not implemented yet")
    
    return magisk_apk

def patch_boot_with_magisk(boot_img, magisk_apk):
    """Patch boot image with Magisk"""
    log(f"Patching boot image: {os.path.basename(boot_img)}")
    
    # Extract Magisk from APK
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(magisk_apk, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find Magisk binary in extracted APK
    magisk_bin = os.path.join(temp_dir, "lib", "x86_64", "libmagiskboot.so")
    if not os.path.exists(magisk_bin):
        magisk_bin = os.path.join(temp_dir, "lib", "armeabi-v7a", "libmagiskboot.so")
    
    if not os.path.exists(magisk_bin):
        error("Could not find Magisk binary in APK")
    
    # Copy boot image to temp directory
    boot_img_copy = os.path.join(temp_dir, "boot.img")
    shutil.copy(boot_img, boot_img_copy)
    
    # Run Magisk patching
    os.chmod(magisk_bin, 0o755)
    result = run_command([magisk_bin, "unpack", boot_img_copy], cwd=temp_dir)
    if not result:
        error("Failed to unpack boot image")
    
    # Check if kernel was extracted successfully
    if not os.path.exists(os.path.join(temp_dir, "kernel")):
        error("Failed to extract kernel from boot image")
    
    # Repack with Magisk
    result = run_command([magisk_bin, "repack", boot_img_copy], cwd=temp_dir)
    if not result:
        error("Failed to repack boot image with Magisk")
    
    # Copy patched boot image to output directory
    patched_boot = os.path.join(temp_dir, "new-boot.img")
    if not os.path.exists(patched_boot):
        error("Patched boot image not found")
    
    output_file = os.path.join(CONFIG["output_dir"], f"magisk_patched_{os.path.basename(boot_img)}")
    shutil.copy(patched_boot, output_file)
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    log(f"Patched boot image saved to: {output_file}")
    return output_file

def build_twrp(recovery_img):
    """Build TWRP recovery for the device"""
    log("Setting up TWRP build environment...")
    
    twrp_dir = os.path.join(CONFIG["output_dir"], "twrp")
    os.makedirs(twrp_dir, exist_ok=True)
    
    # Clone firmware dump repo from GitGud
    firmware_repo_dir = os.path.join(CONFIG["output_dir"], "firmware_repo")
    if not os.path.exists(os.path.join(firmware_repo_dir, ".git")):
        log("Cloning firmware repository from GitGud...")
        run_command(["git", "clone", "https://gitgud.io/rama-firmware-dumps/infinix/Infinix-X6871.git", firmware_repo_dir])
    else:
        # Pull latest changes if repo already exists
        log("Updating firmware repository...")
        run_command(["git", "pull"], cwd=firmware_repo_dir)
    
    # Extract necessary files from firmware repo
    log("Extracting necessary files from firmware repository...")
    # Copy boot/recovery images if not already in firmware_dir
    for root, _, files in os.walk(firmware_repo_dir):
        for file in files:
            if file.lower().endswith(".img") and ("boot" in file.lower() or "recovery" in file.lower()):
                src_file = os.path.join(root, file)
                dst_file = os.path.join(CONFIG["firmware_dir"], file)
                if not os.path.exists(dst_file):
                    shutil.copy(src_file, dst_file)
                    log(f"Copied {file} to firmware directory")
    
    # Set up TWRP build environment
    if not os.path.exists(os.path.join(twrp_dir, ".repo")):
        run_command(["repo", "init", "-u", "git://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git", 
                    "-b", CONFIG["twrp_branch"]], cwd=twrp_dir)
        run_command(["repo", "sync"], cwd=twrp_dir)
    
    # Create device tree directory
    device_tree_dir = os.path.join(twrp_dir, "device", "infinix", "X6871")
    os.makedirs(device_tree_dir, exist_ok=True)
    
    # Create basic device tree files
    create_twrp_device_tree(device_tree_dir, recovery_img)
    
    # Build TWRP
    log("Building TWRP (this may take a while)...")
    build_cmd = [
        "source", "build/envsetup.sh", "&&",
        "lunch", "twrp_X6871-eng", "&&",
        "mka", "recoveryimage"
    ]
    run_command(["bash", "-c", " ".join(build_cmd)], cwd=twrp_dir)
    
    # Check if build was successful
    twrp_img = os.path.join(twrp_dir, "out", "target", "product", "X6871", "recovery.img")
    if not os.path.exists(twrp_img):
        error("TWRP build failed")
    
    # Copy TWRP image to output directory
    output_file = os.path.join(CONFIG["output_dir"], "twrp_X6871.img")
    shutil.copy(twrp_img, output_file)
    
    log(f"TWRP image saved to: {output_file}")
    return output_file
    """Build TWRP recovery for the device"""
    log("Setting up TWRP build environment...")
    
    twrp_dir = os.path.join(CONFIG["output_dir"], "twrp")
    os.makedirs(twrp_dir, exist_ok=True)
    
    # Clone your forked repo instead of setting up from scratch
    if not os.path.exists(os.path.join(twrp_dir, ".git")):
        run_command(["git", "clone", "https://github.com/940smiley/infinix_x6871_twrp.git", twrp_dir])
        run_command(["git", "checkout", "main"], cwd=twrp_dir)  # or whatever your main branch is called
    else:
        # Pull latest changes if repo already exists
        run_command(["git", "pull"], cwd=twrp_dir)
    
    # Build TWRP
    log("Building TWRP (this may take a while)...")
    build_cmd = [
        "source", "build/envsetup.sh", "&&",
        "lunch", "twrp_X6871-eng", "&&",
        "mka", "recoveryimage"
    ]
    run_command(["bash", "-c", " ".join(build_cmd)], cwd=twrp_dir)
    
    # Check if build was successful
    twrp_img = os.path.join(twrp_dir, "out", "target", "product", "X6871", "recovery.img")
    if not os.path.exists(twrp_img):
        error("TWRP build failed")
    
    # Copy TWRP image to output directory
    output_file = os.path.join(CONFIG["output_dir"], "twrp_X6871.img")
    shutil.copy(twrp_img, output_file)
    
    log(f"TWRP image saved to: {output_file}")
    return output_file
  """Build TWRP recovery for the device"""
    log("Setting up TWRP build environment...")
    
    twrp_dir = os.path.join(CONFIG["output_dir"], "twrp")
    os.makedirs(twrp_dir, exist_ok=True)
    
    # Clone TWRP repo if not already present
    if not os.path.exists(os.path.join(twrp_dir, ".repo")):
        run_command(["repo", "init", "-u", "git://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git", 
                    "-b", CONFIG["twrp_branch"]], cwd=twrp_dir)
        run_command(["repo", "sync"], cwd=twrp_dir)
    
    # Create device tree directory
    device_tree_dir = os.path.join(twrp_dir, "device", "infinix", "X6871")
    os.makedirs(device_tree_dir, exist_ok=True)
    
    # Create basic device tree files
    create_twrp_device_tree(device_tree_dir, recovery_img)
    
    # Build TWRP
    log("Building TWRP (this may take a while)...")
    build_cmd = [
        "source", "build/envsetup.sh", "&&",
        "lunch", "twrp_X6871-eng", "&&",
        "mka", "recoveryimage"
    ]
    run_command(["bash", "-c", " ".join(build_cmd)], cwd=twrp_dir)
    
    # Check if build was successful
    twrp_img = os.path.join(twrp_dir, "out", "target", "product", "X6871", "recovery.img")
    if not os.path.exists(twrp_img):
        error("TWRP build failed")
    
    # Copy TWRP image to output directory
    output_file = os.path.join(CONFIG["output_dir"], "twrp_X6871.img")
    shutil.copy(twrp_img, output_file)
    
    log(f"TWRP image saved to: {output_file}")
    return output_file

def create_twrp_device_tree(device_tree_dir, recovery_img):
    """Create basic TWRP device tree files"""
    log("Creating TWRP device tree...")
    
    # Extract recovery image info
    temp_dir = tempfile.mkdtemp()
    run_command(["unpackbootimg", "-i", recovery_img, "-o", temp_dir])
    
    # Create Android.mk
    with open(os.path.join(device_tree_dir, "Android.mk"), "w") as f:
        f.write("""LOCAL_PATH := $(call my-dir)

ifneq ($(filter X6871,$(TARGET_DEVICE)),)
include $(call all-makefiles-under,$(LOCAL_PATH))
endif
""")
    
    # Create AndroidProducts.mk
    with open(os.path.join(device_tree_dir, "AndroidProducts.mk"), "w") as f:
        f.write("""PRODUCT_MAKEFILES := \\
    $(LOCAL_DIR)/twrp_X6871.mk

COMMON_LUNCH_CHOICES := \\
    twrp_X6871-eng
""")
    
    # Create device.mk
    with open(os.path.join(device_tree_dir, "device.mk"), "w") as f:
        f.write("""# Dynamic partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# Fastbootd
PRODUCT_PACKAGES += \\
    android.hardware.fastboot@1.0-impl-mock \\
    fastbootd
""")
    
    # Create twrp_X6871.mk
    with open(os.path.join(device_tree_dir, "twrp_X6871.mk"), "w") as f:
        f.write(f"""# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/aosp_base.mk)

# Inherit from our custom product configuration
$(call inherit-product, vendor/twrp/config/common.mk)

# Device identifier
PRODUCT_DEVICE := X6871
PRODUCT_NAME := twrp_X6871
PRODUCT_BRAND := Infinix
PRODUCT_MODEL := Infinix X6871
PRODUCT_MANUFACTURER := Infinix

# HACK: Set vendor patch level
PRODUCT_PROPERTY_OVERRIDES += \\
    ro.vendor.build.security_patch=2099-12-31
""")
    
    # Create recovery.fstab
    with open(os.path.join(device_tree_dir, "recovery.fstab"), "w") as f:
        f.write("""# Android fstab file.
# The filesystem that contains the filesystem checker binary (typically /system) cannot
# specify MF_CHECK, and must come before any filesystems that do specify MF_CHECK

# Mount point       FS           Device                                                   Flags
/system             ext4         system                                                   flags=display="System";backup=1;logical;
/system_ext         ext4         system_ext                                               flags=display="System_ext";backup=1;logical;
/vendor             ext4         vendor                                                   flags=display="Vendor";backup=1;logical;
/product            ext4         product                                                  flags=display="Product";backup=1;logical;
/metadata           ext4         /dev/block/by-name/metadata                              flags=display="Metadata";
/data               f2fs         /dev/block/by-name/userdata                              flags=display="Data";
/boot               emmc         /dev/block/by-name/boot                                  flags=display="Boot";backup=1;flashimg=1;
/dtbo               emmc         /dev/block/by-name/dtbo                                  flags=display="Dtbo";backup=1;flashimg=1;
/vbmeta             emmc         /dev/block/by-name/vbmeta                                flags=display="VBMeta";backup=1;flashimg=1;
/vbmeta_system      emmc         /dev/block/by-name/vbmeta_system                         flags=display="VBMeta System";backup=1;flashimg=1;
/vbmeta_vendor      emmc         /dev/block/by-name/vbmeta_vendor                         flags=display="VBMeta Vendor";backup=1;flashimg=1;
/misc               emmc         /dev/block/by-name/misc                                  flags=display="Misc";backup=1;flashimg=1;
""")
    
    # Create BoardConfig.mk
    with open(os.path.join(device_tree_dir, "BoardConfig.mk"), "w") as f:
        f.write(f"""DEVICE_PATH := device/infinix/X6871

# For building with minimal manifest
ALLOW_MISSING_DEPENDENCIES := true

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a55

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := cortex-a55

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := {PLATFORM}
TARGET_NO_BOOTLOADER := true

# Platform
TARGET_BOARD_PLATFORM := {PLATFORM}

# Kernel
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2
BOARD_KERNEL_BASE := 0x40078000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_RAMDISK_OFFSET := 0x07c08000
BOARD_KERNEL_TAGS_OFFSET := 0x0bc08000
BOARD_FLASH_BLOCK_SIZE := 131072 # (BOARD_KERNEL_PAGESIZE * 64)
BOARD_BOOTIMG_HEADER_VERSION := 2
BOARD_KERNEL_IMAGE_NAME := Image.gz

# Assert
TARGET_OTA_ASSERT_DEVICE := X6871

# Partition
BOARD_HAS_LARGE_FILESYSTEM := true
BOARD_BOOTIMAGE_PARTITION_SIZE := 33554432
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 33554432
BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := f2fs
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_VENDOR := vendor
TARGET_USERIMAGES_USE_F2FS := true

# Dynamic Partition
BOARD_SUPER_PARTITION_SIZE := 9126805504
BOARD_SUPER_PARTITION_GROUPS := main
BOARD_MAIN_SIZE := 9126805504
BOARD_MAIN_PARTITION_LIST := system system_ext vendor product

# Recovery
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery.fstab
BOARD_USES_RECOVERY_AS_BOOT := false
BOARD_INCLUDE_RECOVERY_DTBO := true
BOARD_USES_FULL_RECOVERY_IMAGE := true

# TWRP Configuration
TW_THEME := portrait_hdpi
TW_EXTRA_LANGUAGES := true
TW_SCREEN_BLANK_ON_BOOT := true
TW_INPUT_BLACKLIST := "hbtp_vm"
TW_USE_TOOLBOX := true
TW_INCLUDE_RESETPROP := true
TW_INCLUDE_REPACKTOOLS := true
TW_EXCLUDE_DEFAULT_USB_INIT := true
RECOVERY_SDCARD_ON_DATA := true
TW_INCLUDE_FASTBOOTD := true
TW_EXCLUDE_APEX := true
""")
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    log("TWRP device tree created")

def main():
    """Main function"""
    log(f"Starting build process for {DEVICE} ({PLATFORM})")
    
    # Check requirements
    check_requirements()
    
    # Find boot and recovery images
    boot_images, recovery_images = find_boot_images()
    
    # Download Magisk
    magisk_apk = download_magisk()
    
    # Patch boot images with Magisk
    for boot_img in boot_images:
        patch_boot_with_magisk(boot_img, magisk_apk)
    
    # Build TWRP if recovery image is available
    if recovery_images:
        build_twrp(recovery_images[0])
    else:
        log("No recovery image found, skipping TWRP build")
    
    log("Build process completed!")
    log(f"Output files are in: {os.path.abspath(CONFIG['output_dir'])}")

if __name__ == "__main__":
    main()