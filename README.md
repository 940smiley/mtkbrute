# MTK Firmware Builder

A tool for building and flashing Android firmware packages for MediaTek devices, specifically for the k39tv1-kaeru bootloader.

## Overview

This project helps you build a firmware package using:
- `k39tv1-kaeru.bin` (bootloader)
- `preloader_k39tv1_bsp.bin` (preloader dump)
- `brom_MT6739_MT6731_MT8765_699.bin` (BROM file)

## Directory Structure

```
C:/users/chenn/mtkbrute/
├── mtk_build/
│   ├── bin/           # Input binary files
│   ├── out/           # Output firmware files
│   ├── fixed/         # Fixed firmware files
│   ├── direct/        # Direct flash method files
│   └── brom/          # BROM exploit method files
├── mtkclient/         # MTK Client tools
├── build_firmware.py  # Firmware builder script
├── fix_firmware.py    # Firmware fixer script
├── flash_firmware.bat # Standard firmware flashing script
├── flash_fixed_firmware.bat # Modified flashing script
├── direct_flash.bat   # Direct flashing script (bypasses stage 2)
└── brom_flash.bat     # BROM exploit flashing script
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bkerler/mtkclient.git
   ```

2. Install dependencies:
   ```bash
   cd mtkclient
   pip install -r requirements.txt
   ```

3. Copy your binary files to the bin directory:
   ```bash
   cp k39tv1-kaeru.bin preloader_k39tv1_bsp.bin brom_MT6739_MT6731_MT8765_699.bin mtk_build/bin/
   ```

## Building Firmware

To analyze the input files without building:
```bash
python build_firmware.py --analyze
```

To build the complete firmware package:
```bash
python build_firmware.py
```

## Flashing Firmware

### Standard Flashing

```
flash_firmware.bat
```

### Stage 2 Boot Failure Solutions

If you encounter errors like:
```
DAXFlash - [LIB]: Stage was't executed. Maybe dram issue?
DAXFlash - [LIB]: Error on booting to da (xflash)
```

Try these solutions in order:

#### 1. Modified Parameters Flashing
```
flash_fixed_firmware.bat
```

#### 2. Direct Flashing (Bypasses Stage 2)
```
direct_flash.bat
```

#### 3. BROM Exploit Flashing (Most Reliable)
```
brom_flash.bat
```

The BROM exploit method is the most reliable as it bypasses all bootloader stages and writes directly to the eMMC storage.

## Advanced Flashing Options

### BROM Exploit Method

This method uses the BROM exploit to bypass all bootloader stages:

1. Put device in BROM mode:
   - Power off device completely
   - Press and hold Volume Down + Volume Up buttons
   - Connect USB cable while holding the buttons
   - Release after 5 seconds

2. Run the BROM exploit:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py payload kamakiri C:/users/chenn/mtkbrute/mtk_build/bin/brom_MT6739_MT6731_MT8765_699.bin
   ```

3. Flash preloader directly:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py e preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin
   ```

4. Flash bootloader directly:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py e lk C:/users/chenn/mtkbrute/mtk_build/out/k39tv1-kaeru.bin
   ```

### Crash Method

If all else fails, try the crash method:

1. Crash the device:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py crash
   ```

2. Flash preloader after crash:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py w preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin --crash
   ```

## File Details

### Bootloader (k39tv1-kaeru.bin)
- Size: 503,077 bytes
- Magic: 88168858

### Preloader (preloader_k39tv1_bsp.bin)
- Size: 118,996 bytes
- Magic: 4d4d4d01 (Valid MTK preloader header)

## Requirements

- Python 3.6+
- USB connection to device
- Device in bootloader or BROM mode for flashing