#!/usr/bin/env python3
# MTK DA File Analyzer
# This script loops through DA files to confirm board and chipset information

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

class DAAnalyzer(metaclass=LogBase):
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
        
        self.logfile = os.path.join(log_dir, f"da_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        fh = logging.FileHandler(self.logfile, encoding='utf-8')
        self.__logger.addHandler(fh)
        self.__logger.setLevel(loglevel)
        
        # Initialize connection
        self.cdc = UsbClass(portconfig=default_ids, loglevel=loglevel, devclass=10)
        
    def log_message(self, message):
        self.info(message)
        with open(self.logfile, "a") as f:
            f.write(f"{message}\n")
            
    def find_da_files(self):
        """Find all DA files in the repository"""
        da_files = []
        
        # Look in common locations
        search_paths = [
            "/workspaces/mtkbrute/*.bin",
            "/workspaces/mtkbrute/mtkclient/mtkclient/Loader/*.bin",
            "/workspaces/mtkbrute/mtkclient/mtkclient/payloads/*.bin"
        ]
        
        for path in search_paths:
            files = glob.glob(path)
            # Filter for likely DA files (containing "DA" in filename or specific patterns)
            for file in files:
                filename = os.path.basename(file).lower()
                if "da" in filename or "download" in filename:
                    da_files.append(file)
            
        self.log_message(f"Found {len(da_files)} potential DA files")
        return da_files
        
    def analyze_da_files(self):
        """Analyze each DA file to extract board and chipset information"""
        self.log_message("Starting DA file analysis...")
        
        # Initialize connection components
        port = Port(self.cdc, self.loglevel)
        connection = Connection(port, self.loglevel)
        
        # First try to connect to get device info
        device_info = {}
        if connection.connect():
            mtk = connection.mtk
            if mtk is not None:
                device_info["hwcode"] = mtk.config.hwcode
                device_info["hwsubcode"] = mtk.config.hwsubcode
                device_info["hwver"] = mtk.config.hwver
                device_info["swver"] = mtk.config.swver
                device_info["chipname"] = mtk.config.chipconfig.name
                
                self.log_message(f"Connected to device!")
                self.log_message(f"Device HW code: {hex(device_info['hwcode'])}")
                self.log_message(f"Device HW sub code: {hex(device_info['hwsubcode'])}")
                self.log_message(f"Device HW version: {hex(device_info['hwver'])}")
                self.log_message(f"Device SW version: {hex(device_info['swver'])}")
                self.log_message(f"Device chip name: {device_info['chipname']}")
            
            connection.close()
        else:
            self.log_message("Failed to connect to device. Please ensure device is in preloader/bootrom mode.")
            return False
        
        # Get all DA files
        da_files = self.find_da_files()
        
        # Results dictionary to store compatibility info
        results = {
            "compatible": [],
            "incompatible": [],
            "error": []
        }
        
        # Test each DA file
        for da_file in da_files:
            da_name = os.path.basename(da_file)
            self.log_message(f"\nTesting DA file: {da_name}")
            
            try:
                # Reset connection
                connection.close()
                time.sleep(1)
                
                # Try to connect
                if connection.connect():
                    mtk = connection.mtk
                    if mtk is not None:
                        # Try to use this DA file
                        try:
                            da_handler = DA_handler(mtk, self.loglevel)
                            
                            # Override the default DA file with our test file
                            original_da = da_handler.loader.da
                            da_handler.loader.da = da_file
                            
                            if da_handler.setup():
                                self.log_message(f"SUCCESS: DA file {da_name} is compatible!")
                                self.log_message(f"DA version: {da_handler.da_version}")
                                
                                # Get target config details
                                if hasattr(da_handler, 'target_config'):
                                    self.log_message(f"Target config: {da_handler.target_config}")
                                    
                                    # Extract board/chipset info if available
                                    if hasattr(da_handler.target_config, 'boardname'):
                                        self.log_message(f"Board name: {da_handler.target_config.boardname}")
                                    if hasattr(da_handler.target_config, 'chipset'):
                                        self.log_message(f"Chipset: {da_handler.target_config.chipset}")
                                
                                # Store compatibility info
                                results["compatible"].append({
                                    "file": da_name,
                                    "path": da_file,
                                    "da_version": da_handler.da_version,
                                    "target_config": str(getattr(da_handler, 'target_config', 'Unknown'))
                                })
                            else:
                                self.log_message(f"INCOMPATIBLE: DA file {da_name} setup failed")
                                results["incompatible"].append({
                                    "file": da_name,
                                    "path": da_file,
                                    "reason": "DA setup failed"
                                })
                                
                            # Restore original DA file
                            da_handler.loader.da = original_da
                            
                        except Exception as e:
                            self.log_message(f"ERROR with {da_name}: {str(e)}")
                            results["error"].append({
                                "file": da_name,
                                "path": da_file,
                                "error": str(e)
                            })
                    else:
                        self.log_message(f"Failed to get MTK object with {da_name}")
                        results["error"].append({
                            "file": da_name,
                            "path": da_file,
                            "error": "MTK object is None"
                        })
                else:
                    self.log_message(f"Failed to connect with {da_name}")
                    results["error"].append({
                        "file": da_name,
                        "path": da_file,
                        "error": "Connection failed"
                    })
            except Exception as e:
                self.log_message(f"Exception with {da_name}: {str(e)}")
                results["error"].append({
                    "file": da_name,
                    "path": da_file,
                    "error": str(e)
                })
                
            # Wait a bit before trying the next DA file
            time.sleep(1)
        
        # Summarize results
        self.log_message("\n\n=== DA ANALYSIS SUMMARY ===")
        self.log_message(f"Device HW code: {hex(device_info['hwcode'])}")
        self.log_message(f"Device chip name: {device_info['chipname']}")
        self.log_message(f"Compatible DA files: {len(results['compatible'])}")
        self.log_message(f"Incompatible DA files: {len(results['incompatible'])}")
        self.log_message(f"Error DA files: {len(results['error'])}")
        
        if results['compatible']:
            self.log_message("\nCOMPATIBLE DA FILES:")
            for da in results['compatible']:
                self.log_message(f"- {da['file']} (Version: {da['da_version']})")
        
        self.log_message(f"\nDetailed results saved to: {self.logfile}")
        return results

if __name__ == "__main__":
    print("MTK DA File Analyzer")
    print("===================")
    print("This tool will analyze DA files to confirm board and chipset compatibility.")
    print("Please connect your device in preloader/bootrom mode.")
    print("Results will be logged to the logs directory.")
    
    analyzer = DAAnalyzer(logging.INFO)
    
    print("\nStarting analysis process...")
    print("This may take some time as we test different DA files.")
    print("Check the log file for detailed results.")
    
    analyzer.analyze_da_files()
    
    print(f"\nAnalysis process completed. Results saved to: {analyzer.logfile}")