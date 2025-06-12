@echo off
REM Flash firmware script for MTK devices (Windows version)
REM This script helps flash the firmware to a MediaTek device

echo MTK Firmware Flasher
echo ====================

REM Flash the firmware
echo Flashing preloader and bootloader...
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w ^
    --preloader="C:\users\chenn\mtkbrute\mtk_build\out\preloader_k39tv1_bsp.bin" ^
    lk1 "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin" ^
    lk2 "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin"

if %ERRORLEVEL% EQU 0 (
    echo Flashing completed successfully!
    echo You can now reboot your device.
) else (
    echo Flashing failed. Please check the error messages above.
    echo You may need to retry or check your device connection.
)

pause