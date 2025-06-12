#!/bin/bash

# Flash firmware script for MTK devices
# This script helps flash the firmware to a MediaTek device

echo "MTK Firmware Flasher"
echo "===================="

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

# Flash the firmware
echo "Flashing preloader and bootloader..."
python3 C:/users/chenn/mtkbrute/mtkclient/mtk.py write --preloader=C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin --bootloader=C:/users/chenn/mtkbrute/mtk_build/out/k39tv1-kaeru.bin

if [ $? -eq 0 ]; then
    echo "Flashing completed successfully!"
    echo "You can now reboot your device."
else
    echo "Flashing failed. Please check the error messages above."
    echo "You may need to retry or check your device connection."
fi