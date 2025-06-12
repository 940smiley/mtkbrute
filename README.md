# MTK Firmware Builder

A tool for building and flashing Android firmware packages for MediaTek devices, specifically for the k39tv1-kaeru bootloader.

## Overview

This project helps you build a firmware package using:
- `k39tv1-kaeru.bin` (bootloader)
- `preloader_k39tv1_bsp.bin` (preloader dump)
- `brom_MT6739_MT6731_MT8765_699.bin` (BROM file)

## Directory Structure

```
mtkbrute/
├── mtk_build/
│   ├── bin/           # Input binary files
│   └── out/           # Output firmware files
├── mtkclient/         # MTK Client tools
├── build_firmware.py  # Firmware builder script
└── flash_firmware.sh  # Firmware flashing script
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bkerler/mtkclient.git
   ```

2. Install dependencies:
   ```bash
   cd mtkclient
   pip3 install -r requirements.txt
   ```

3. Copy your binary files to the bin directory:
   ```bash
   cp k39tv1-kaeru.bin preloader_k39tv1_bsp.bin brom_MT6739_MT6731_MT8765_699.bin mtk_build/bin/
   ```

## Building Firmware

To analyze the input files without building:
```bash
python3 build_firmware.py --analyze
```

To build the complete firmware package:
```bash
python3 build_firmware.py
```

This will:
1. Analyze the bootloader and preloader files
2. Create a scatter file for the firmware
3. Build the firmware package in `mtk_build/out/`

## Flashing Firmware

To flash the firmware to a device:
```bash
./flash_firmware.sh
```

Or manually:
```bash
python3 mtkclient/mtk.py write --preloader=mtk_build/out/preloader_k39tv1_bsp.bin --bootloader=mtk_build/out/k39tv1-kaeru.bin
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

### Scatter File
The scatter file (`MT6739_Android_scatter.txt`) defines the firmware layout:
- Preloader partition at EMMC_BOOT_1
- Bootloader partition at EMMC_USER

## Requirements

- Python 3.6+
- USB connection to device
- Device in bootloader mode for flashing

## Troubleshooting

If flashing fails:
1. Ensure device is in bootloader mode
2. Check USB connection
3. Try running with sudo if permission issues occur
4. Verify that the binary files are not corrupted