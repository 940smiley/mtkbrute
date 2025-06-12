#!/bin/bash

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

# Create fixed directory if it doesn't exist
mkdir -p C:/users/chenn/mtkbrute/mtk_build/fixed

# Copy original files to fixed directory
cp C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin C:/users/chenn/mtkbrute/mtk_build/fixed/preloader_k39tv1_bsp.bin
cp C:/users/chenn/mtkbrute/mtk_build/out/k39tv1-kaeru.bin C:/users/chenn/mtkbrute/mtk_build/fixed/k39tv1-kaeru.bin

# Flash the firmware with modified parameters to bypass DRAM setup
echo "Flashing with modified parameters to bypass DRAM issues..."
python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write \
    --preloader=C:/users/chenn/mtkbrute/mtk_build/fixed/preloader_k39tv1_bsp.bin \
    --skip_dram_setup=1

if [ $? -eq 0 ]; then
    echo "Preloader flashing completed successfully!"
    
    # Now try to flash the bootloader separately
    echo "Flashing bootloader..."
    python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write \
        --bootloader=C:/users/chenn/mtkbrute/mtk_build/fixed/k39tv1-kaeru.bin
    
    if [ $? -eq 0 ]; then
        echo "Bootloader flashing completed successfully!"
        echo "You can now reboot your device."
    else
        echo "Bootloader flashing failed. Your device may still boot with just the preloader."
    fi
else
    echo "Flashing failed. Trying alternative method..."
    
    # Try with different parameters
    echo "Attempting alternative flashing method..."
    python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write \
        --preloader=C:/users/chenn/mtkbrute/mtk_build/fixed/preloader_k39tv1_bsp.bin \
        --da_addr=0x200000
    
    if [ $? -eq 0 ]; then
        echo "Alternative flashing method succeeded!"
    else
        echo "All flashing attempts failed. Please check your device connection."
        echo ""
        echo "You may need to try one of these commands manually:"
        echo "1. python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write --preloader=C:/users/chenn/mtkbrute/mtk_build/fixed/preloader_k39tv1_bsp.bin --skip_dram_setup=1"
        echo "2. python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write --preloader=C:/users/chenn/mtkbrute/mtk_build/fixed/preloader_k39tv1_bsp.bin --da_addr=0x200000"
        echo "3. python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write --preloader=C:/users/chenn/mtkbrute/mtk_build/fixed/preloader_k39tv1_bsp.bin --usbdl_mode=1"
    fi
fi