#!/usr/bin/env python3
# MTK Board Detection Script

import os
import sys
import time
import logging
import glob
from datetime import datetime
from mtkclient.Library.Connection.usblib import UsbClass
from mtkclient.Library.utils import LogBase
from mtkclient.config.usb_ids import default_ids
from mtkclient.Library.Connection.Connection import Connection
from mtkclient.Library.DA.mtk_da_cmd import DA_handler
from mtkclient.Library.Port import Port

class BoardDetector(metaclass=LogBase):
    def __init__(self, loglevel=logging.INFO):
        self.__logger = self.__logger
        self.loglevel = loglevel
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        self.debug = self.__logger.debug
        
        # Setup logging
        log_dir = os.path.join("logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        self.logfile = os.path.join(log_dir, f"board_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        fh = logging.FileHandler(self.logfile, encoding='utf-8')
        self.__logger.addHandler(fh)
        self.__logger.setLevel(loglevel)
        
        # Initialize connection
        self.cdc = UsbClass(portconfig=default_ids, loglevel=loglevel, devclass=10)
        
    def log_message(self, message):
        self.info(message)
        with open(self.logfile, "a") as f:
            f.write(f"{message}\n")
            
    def find_preloaders(self):
        """Find all preloader files in the repository"""
        preloaders = []
        
        # Look in common locations
        search_paths = [
            "/workspaces/mtkbrute/mtk_build/out/*.bin",
            "/workspaces/mtkbrute/*.bin",
            "/workspaces/mtkbrute/mtkclient/mtkclient/Loader/Preloader/*.bin"
        ]
        
        for path in search_paths:
            preloaders.extend(glob.glob(path))
            
        self.log_message(f"Found {len(preloaders)} preloader files")
        return preloaders
        
    def detect_board(self):
        """Try to detect the board by connecting with different preloaders"""
        self.log_message("Starting board detection...")
        
        # Initialize connection components
        port = Port(self.cdc, self.loglevel)
        connection = Connection(port, self.loglevel)
        
        # First try to connect without specifying a preloader
        self.log_message("Attempting initial connection to detect device...")
        
        if connection.connect():
            mtk = connection.mtk
            if mtk is not None:
                self.log_message(f"Connected to device!")
                self.log_message(f"Device HW code: {hex(mtk.config.hwcode)}")
                self.log_message(f"Device HW sub code: {hex(mtk.config.hwsubcode)}")
                self.log_message(f"Device HW version: {hex(mtk.config.hwver)}")
                self.log_message(f"Device SW version: {hex(mtk.config.swver)}")
                self.log_message(f"Device chip name: {mtk.config.chipconfig.name}")
                
                # Try to get more info if possible
                try:
                    da_handler = DA_handler(mtk, self.loglevel)
                    if da_handler.setup():
                        self.log_message("DA setup successful")
                        self.log_message(f"DA version: {da_handler.da_version}")
                        self.log_message(f"Target config: {da_handler.target_config}")
                    else:
                        self.log_message("DA setup failed")
                except Exception as e:
                    self.log_message(f"Error during DA setup: {str(e)}")
                
                connection.close()
                return True
        
        # If initial connection failed, try with different preloaders
        preloaders = self.find_preloaders()
        
        for preloader in preloaders:
            preloader_name = os.path.basename(preloader)
            self.log_message(f"Trying with preloader: {preloader_name}")
            
            try:
                # Reset connection
                connection.close()
                time.sleep(1)
                
                # Try to connect with this preloader
                if connection.connect(preloader=preloader):
                    mtk = connection.mtk
                    if mtk is not None:
                        self.log_message(f"SUCCESS with preloader: {preloader_name}")
                        self.log_message(f"Device HW code: {hex(mtk.config.hwcode)}")
                        self.log_message(f"Device HW sub code: {hex(mtk.config.hwsubcode)}")
                        self.log_message(f"Device HW version: {hex(mtk.config.hwver)}")
                        self.log_message(f"Device SW version: {hex(mtk.config.swver)}")
                        self.log_message(f"Device chip name: {mtk.config.chipconfig.name}")
                        
                        # Try to get more info if possible
                        try:
                            da_handler = DA_handler(mtk, self.loglevel)
                            if da_handler.setup():
                                self.log_message("DA setup successful")
                                self.log_message(f"DA version: {da_handler.da_version}")
                                self.log_message(f"Target config: {da_handler.target_config}")
                            else:
                                self.log_message("DA setup failed")
                        except Exception as e:
                            self.log_message(f"Error during DA setup: {str(e)}")
                        
                        connection.close()
                        return True
                    else:
                        self.log_message(f"Connected but MTK object is None with {preloader_name}")
                else:
                    self.log_message(f"Failed to connect with {preloader_name}")
            except Exception as e:
                self.log_message(f"Error with {preloader_name}: {str(e)}")
                
            # Wait a bit before trying the next preloader
            time.sleep(1)
        
        self.log_message("Board detection failed with all preloaders")
        return False

if __name__ == "__main__":
    print("MTK Board Detection Tool")
    print("=======================")
    print("This tool will attempt to detect your MediaTek device and identify the correct board/chipset.")
    print("Please connect your device in preloader/bootrom mode.")
    print("Results will be logged to the logs directory.")
    
    detector = BoardDetector(logging.INFO)
    
    print("\nStarting detection process...")
    print("This may take some time as we try different preloader files.")
    print("Check the log file for detailed results.")
    
    detector.detect_board()
    
    print(f"\nDetection process completed. Results saved to: {detector.logfile}")