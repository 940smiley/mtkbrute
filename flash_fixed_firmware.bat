@echo off
REM Flash fixed firmware script for MTK devices (Windows version)
REM This script uses modified parameters to address stage 2 boot failures

echo MTK Fixed Firmware Flasher
echo ==========================

REM Create fixed directory if it doesn't exist
mkdir "C:\users\chenn\mtkbrute\mtk_build\fixed" 2>nul

REM Copy original files to fixed directory
copy "C:\users\chenn\mtkbrute\mtk_build\out\preloader_k39tv1_bsp.bin" "C:\users\chenn\mtkbrute\mtk_build\fixed\preloader_k39tv1_bsp.bin"
copy "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin" "C:\users\chenn\mtkbrute\mtk_build\fixed\k39tv1-kaeru.bin"

REM Flash the firmware with modified parameters to bypass DRAM setup
echo Flashing with modified parameters to bypass DRAM issues...
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\fixed\preloader_k39tv1_bsp.bin" --skip_dram_setup=1

if %ERRORLEVEL% EQU 0 (
    echo Preloader flashing completed successfully!
    
    REM Now try to flash the bootloader separately
    echo Flashing bootloader...
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w lk "C:\users\chenn\mtkbrute\mtk_build\fixed\k39tv1-kaeru.bin"
    
    if %ERRORLEVEL% EQU 0 (
        echo Bootloader flashing completed successfully!
        echo You can now reboot your device.
    ) else (
        echo Bootloader flashing failed. Your device may still boot with just the preloader.
    )
) else (
    echo Flashing failed. Trying alternative method...
    
    REM Try with different parameters
    echo Attempting alternative flashing method...
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\fixed\preloader_k39tv1_bsp.bin" --da_addr=0x200000
    
    if %ERRORLEVEL% EQU 0 (
        echo Alternative flashing method succeeded!
    ) else (
        echo All flashing attempts failed. Please check your device connection.
        echo.
        echo You may need to try one of these commands manually:
        echo 1. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\fixed\preloader_k39tv1_bsp.bin" --skip_dram_setup=1
        echo 2. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\fixed\preloader_k39tv1_bsp.bin" --da_addr=0x200000
        echo 3. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\fixed\preloader_k39tv1_bsp.bin" --usbdl_mode=1
    )
)

pause