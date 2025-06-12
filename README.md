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
│   └── fixed/         # Fixed firmware files
├── mtkclient/         # MTK Client tools
├── build_firmware.py  # Firmware builder script
├── fix_firmware.py    # Firmware fixer script
├── flash_firmware.sh  # Standard firmware flashing script (Linux/Mac)
├── flash_firmware.bat # Standard firmware flashing script (Windows)
├── flash_fixed_firmware.sh # Modified flashing script (Linux/Mac)
└── flash_fixed_firmware.bat # Modified flashing script (Windows)
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

#### On Windows:
```
flash_firmware.bat
```

#### On Linux/Mac:
```bash
./flash_firmware.sh
```

Or manually:
```bash
# Flash preloader
python C:/users/chenn/mtkbrute/mtkclient/mtk.py w preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin

# Flash bootloader
python C:/users/chenn/mtkbrute/mtkclient/mtk.py w lk C:/users/chenn/mtkbrute/mtk_build/out/k39tv1-kaeru.bin
```

### Troubleshooting Stage 2 Boot Failures

If you encounter errors like:
```
DAXFlash - [LIB]: Stage was't executed. Maybe dram issue?
DAXFlash - [LIB]: Error on booting to da (xflash)
```

Try the fixed firmware flashing script:

#### On Windows:
```
flash_fixed_firmware.bat
```

#### On Linux/Mac:
```bash
./flash_fixed_firmware.sh
```

This script:
1. Bypasses DRAM setup
2. Uses alternative memory addresses
3. Tries multiple flashing methods

You can also try fixing the firmware files:
```bash
python fix_firmware.py
```

### Entering Bootloader Mode

To put your device in bootloader mode:
1. Power off the device
2. Press and hold Volume Down + Power buttons
3. Connect USB cable while holding the buttons

## File Details

### Bootloader (k39tv1-kaeru.bin)
- Size: 503,077 bytes
- Magic: 88168858

### Preloader (preloader_k39tv1_bsp.bin)
- Size: 118,996 bytes
- Magic: 4d4d4d01 (Valid MTK preloader header)

## Advanced Flashing Options

If standard flashing fails, try these options:

1. Skip DRAM setup:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py w preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin --skip_dram_setup=1
   ```

2. Use alternative DA address:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py w preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin --da_addr=0x200000
   ```

3. Force USB download mode:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py w preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin --usbdl_mode=1
   ```

4. Flash preloader only:
   ```bash
   python C:/users/chenn/mtkbrute/mtkclient/mtk.py w preloader C:/users/chenn/mtkbrute/mtk_build/out/preloader_k39tv1_bsp.bin
   ```

## Requirements

- Python 3.6+
- USB connection to device
- Device in bootloader mode for flashing