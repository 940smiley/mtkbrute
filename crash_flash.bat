@echo off
REM Crash method flashing script
REM This uses the crash method which is most reliable for problematic devices

echo MTK Crash Method Firmware Flasher
echo ================================

REM Create a directory for the crash method
mkdir "C:\users\chenn\mtkbrute\mtk_build\crash" 2>nul
copy "C:\users\chenn\mtkbrute\mtk_build\out\preloader_k39tv1_bsp.bin" "C:\users\chenn\mtkbrute\mtk_build\crash\preloader_k39tv1_bsp.bin"
copy "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin" "C:\users\chenn\mtkbrute\mtk_build\crash\k39tv1-kaeru.bin"

echo INSTRUCTIONS:
echo 1. Power off your device completely
echo 2. Press and hold Volume Down button
echo 3. Connect USB cable while holding the button
echo 4. Release the button after 5 seconds
echo.
echo Press any key when ready...
pause > nul

echo Step 1: Crashing the device...
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" crash

echo Step 2: Flashing preloader...
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\crash\preloader_k39tv1_bsp.bin"

if %ERRORLEVEL% EQU 0 (
    echo Preloader flashing completed successfully!
    
    echo Step 3: Flashing bootloader...
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w lk "C:\users\chenn\mtkbrute\mtk_build\crash\k39tv1-kaeru.bin"
    
    if %ERRORLEVEL% EQU 0 (
        echo Bootloader flashing completed successfully!
        echo You can now reboot your device.
    ) else (
        echo Bootloader flashing failed. Your device may still boot with just the preloader.
    )
) else (
    echo Preloader flashing failed. Trying with crash parameter...
    
    echo Step 2 (alternative): Flashing preloader with crash parameter...
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\crash\preloader_k39tv1_bsp.bin" --crash
)

pause