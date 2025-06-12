@echo off
REM BROM direct flashing script (fixed version)
REM This uses the correct payload command syntax

echo MTK BROM Direct Firmware Flasher
echo ===============================

REM Create a directory for the BROM flash method
mkdir "C:\users\chenn\mtkbrute\mtk_build\brom" 2>nul
copy "C:\users\chenn\mtkbrute\mtk_build\out\preloader_k39tv1_bsp.bin" "C:\users\chenn\mtkbrute\mtk_build\brom\preloader_k39tv1_bsp.bin"
copy "C:\users\chenn\mtkbrute\mtk_build\out\k39tv1-kaeru.bin" "C:\users\chenn\mtkbrute\mtk_build\brom\k39tv1-kaeru.bin"
copy "C:\users\chenn\mtkbrute\mtk_build\bin\brom_MT6739_MT6731_MT8765_699.bin" "C:\users\chenn\mtkbrute\mtk_build\brom\brom.bin"

echo INSTRUCTIONS:
echo 1. Power off your device completely
echo 2. Press and hold Volume Down + Volume Up buttons
echo 3. Connect USB cable while holding the buttons
echo 4. Release the buttons after 5 seconds
echo.
echo Press any key when ready...
pause > nul

REM Try with BROM exploit mode using correct syntax
python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" payload --filename="C:\users\chenn\mtkbrute\mtk_build\brom\brom.bin"

if %ERRORLEVEL% EQU 0 (
    echo BROM exploit successful!
    
    REM Flash preloader directly
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\brom\preloader_k39tv1_bsp.bin"
    
    if %ERRORLEVEL% EQU 0 (
        echo Preloader flashing completed successfully!
        
        REM Flash bootloader
        python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w lk "C:\users\chenn\mtkbrute\mtk_build\brom\k39tv1-kaeru.bin"
        
        if %ERRORLEVEL% EQU 0 (
            echo Bootloader flashing completed successfully!
            echo You can now reboot your device.
        ) else (
            echo Bootloader flashing failed. Your device may still boot with just the preloader.
        )
    ) else (
        echo Preloader flashing failed.
    )
) else (
    echo BROM exploit failed. Trying crash method...
    
    REM Try with crash method
    python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" crash
    
    if %ERRORLEVEL% EQU 0 (
        echo Device crashed successfully. Attempting direct write...
        python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\brom\preloader_k39tv1_bsp.bin"
    ) else (
        echo All flashing attempts failed.
        echo.
        echo Try these manual commands:
        echo 1. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" crash
        echo 2. python "C:\users\chenn\mtkbrute\mtkclient\mtk.py" w preloader "C:\users\chenn\mtkbrute\mtk_build\brom\preloader_k39tv1_bsp.bin"
    )
)

pause