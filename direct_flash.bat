@echo off
REM Direct flashing script that bypasses stage 2 boot process
REM This uses the emergency download mode approach

echo MTK Direct Firmware Flasher
echo ==========================

REM Create a directory for the direct flash method
mkdir "C:\users\chenn\mtkbrute\mtk_build\direct" 2>nul
copy "C:\users\chenn\mtkbrute\mtk_build\out\preloader_k39tv1_bsp.bin" "C:\users\chenn\mtkbrute\mtk_build\direct\preloader_k39tv1_bsp.bin"
copy "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin" "C:\users\chenn\mtkbrute\mtk_build\direct\k39tv1-kaeru.bin"

echo Attempting direct flashing method with emergency download mode...

REM Try with emergency download mode
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\direct\preloader_k39tv1_bsp.bin" --usbdl_mode=1 --skip_dram_setup=1 --da_addr=0x200000

if %ERRORLEVEL% EQU 0 (
    echo Preloader flashing completed successfully!
    
    REM Try to flash bootloader with emergency mode
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w lk "C:\users\chenn\mtkbrute\mtk_build\direct\k39tv1-kaeru.bin" --usbdl_mode=1
    
    if %ERRORLEVEL% EQU 0 (
        echo Bootloader flashing completed successfully!
        echo You can now reboot your device.
    ) else (
        echo Bootloader flashing failed. Your device may still boot with just the preloader.
    )
) else (
    echo Direct flashing failed. Trying legacy mode...
    
    REM Try with legacy mode
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\direct\preloader_k39tv1_bsp.bin" --legacy
    
    if %ERRORLEVEL% EQU 0 (
        echo Legacy flashing method succeeded!
    ) else (
        echo All flashing attempts failed.
        echo.
        echo Try these manual commands:
        echo 1. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" r32 0x201000 16
        echo 2. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" peek 0x201000 16
        echo 3. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" crash
        echo 4. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\direct\preloader_k39tv1_bsp.bin" --crash
    )
)

pause