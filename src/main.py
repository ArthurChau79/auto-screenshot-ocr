import os
import tkinter as tk
from ocr_service import OCRService
from ui import OCRUI
from config import load_config
import sys
import atexit

def cleanup():
    """Force cleanup when program exits."""
    print("Running cleanup...")
    try:
        # Force exit
        os._exit(0)
    except:
        pass

def main():
    """Main application entry point."""
    # Register cleanup function
    atexit.register(cleanup)
    
    try:
        # Load configuration
        config = load_config()
        print("Configuration loaded successfully")
        
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        print("Root window created")
        
        # Create OCR service
        ocr_service = OCRService(config['api_key'])
        print("OCR service initialized")
        
        # Create UI with watch directory
        app = OCRUI(root, ocr_service, config['web_presets'], config['watch_dir'])
        print("UI created successfully")
        
        # Start the application
        print("Starting main loop...")
        try:
            root.mainloop()
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt, exiting...")
            os._exit(0)
        except Exception as e:
            print(f"Error in main loop: {e}")
            os._exit(1)
        finally:
            print("Cleaning up...")
            root.quit()
            root.destroy()
            print("Main loop ended")
            os._exit(0)
        
    except Exception as e:
        print(f"Application error: {e}")
        os._exit(1)

if __name__ == "__main__":
    main() 