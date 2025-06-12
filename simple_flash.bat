@echo off
REM Simple flashing script with minimal commands
REM This uses the most basic approach that should work with any mtkclient version

echo MTK Simple Firmware Flasher
echo =========================

echo INSTRUCTIONS:
echo 1. Power off your device completely
echo 2. Press and hold Volume Down button
echo 3. Connect USB cable while holding the button
echo 4. Release the button after 5 seconds
echo.
echo Press any key when ready...
pause > nul

echo Flashing preloader...
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\out\preloader_k39tv1_bsp.bin"

if %ERRORLEVEL% EQU 0 (
    echo Preloader flashing completed successfully!
    echo.
    echo Now reconnect your device in bootloader mode and press any key...
    pause > nul
    
    echo Flashing bootloader...
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w lk "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin"
    
    if %ERRORLEVEL% EQU 0 (
        echo Bootloader flashing completed successfully!
        echo You can now reboot your device.
    ) else (
        echo Bootloader flashing failed.
    )
) else (
    echo Preloader flashing failed.
)

pause