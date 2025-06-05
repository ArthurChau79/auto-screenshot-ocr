import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from typing import Optional, Dict, Callable
from ocr_service import OCRService
from file_watcher import FileWatcher
import webbrowser
import sys
import os
import urllib.parse

class OCRUI:
    def __init__(self, root: tk.Tk, ocr_service: OCRService, web_presets: Dict[str, str], watch_dir: str):
        self.root = root
        self.ocr_service = ocr_service
        self.web_presets = web_presets
        self.watch_dir = watch_dir
        self.skip_confirmation = False
        
        # Hide the root window
        self.root.withdraw()
        
        # Initialize file watcher
        self.file_watcher = FileWatcher(watch_dir, self._on_new_screenshot)
        if not self.file_watcher.start():
            messagebox.showerror("Error", f"Could not start watching directory: {watch_dir}")
            self.root.destroy()
            return
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _on_new_screenshot(self, file_path: str):
        """Handle new screenshot detection."""
        try:
            # Show confirmation dialog with screenshot preview
            self.create_confirmation_dialog(
                file_path,
                on_confirm=lambda dialog=None: self._process_screenshot(file_path),
                on_cancel=lambda dialog=None: None
            )
            
        except Exception as e:
            print(f"Error handling new screenshot: {e}")
            messagebox.showerror("Error", f"Failed to handle screenshot: {e}")

    def _calculate_image_size(self, image: Image.Image, max_width: int = 800, max_height: int = 600) -> tuple:
        """Calculate optimal image size while maintaining aspect ratio."""
        width, height = image.size
        
        # Calculate scaling factors for both dimensions
        width_ratio = max_width / width
        height_ratio = max_height / height
        
        # Use the smaller ratio to ensure the image fits within bounds
        ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Ensure minimum size for very small images
        min_size = 200  # Increased minimum size
        if new_width < min_size and new_height < min_size:
            if width > height:
                new_width = min_size
                new_height = int(height * (min_size / width))
            else:
                new_height = min_size
                new_width = int(width * (min_size / height))
        
        return (new_width, new_height)

    def _calculate_window_size(self, image_size: tuple) -> tuple:
        """Calculate optimal window size based on image size."""
        # Base dimensions for the window content
        content_width = max(400, image_size[0] + 40)  # Add padding
        content_height = max(500, image_size[1] + 300)  # Add space for controls
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate maximum allowed dimensions (80% of screen)
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # Calculate final dimensions
        width = min(content_width, max_width)
        height = min(content_height, max_height)
        
        return (width, height)

    def create_confirmation_dialog(self, image_path: str, on_confirm: Callable, on_cancel: Callable):
        """Create confirmation dialog with image preview."""
        if self.skip_confirmation:
            on_confirm()
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm OCR")
        dialog.attributes('-topmost', True)  # Make window stay on top
        
        try:
            # Load and resize image
            image = Image.open(image_path)
            image_size = self._calculate_image_size(image)
            image = image.resize(image_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Calculate window size
            window_size = self._calculate_window_size(image_size)
            dialog.geometry(f"{window_size[0]}x{window_size[1]}")
            
            # Center the window on screen
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - window_size[0]) // 2
            y = (dialog.winfo_screenheight() - window_size[1]) // 2
            dialog.geometry(f"+{x}+{y}")
            
            # Create main container
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Create message label
            message_label = ttk.Label(main_frame, text="New screenshot detected. Do you want to proceed?")
            message_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            # Create image frame
            image_frame = ttk.Frame(main_frame)
            image_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            # Display image
            image_label = ttk.Label(image_frame, image=photo)
            image_label.image = photo  # Keep a reference
            image_label.grid(row=0, column=0)
            
            # Create controls frame
            controls_frame = ttk.Frame(main_frame)
            controls_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            # Create checkbox
            skip_var = tk.BooleanVar()
            skip_checkbox = ttk.Checkbutton(controls_frame, text="Don't ask again",
                                          variable=skip_var,
                                          command=lambda: setattr(self, 'skip_confirmation', skip_var.get()))
            skip_checkbox.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
            
            # Create buttons frame
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            # Create buttons
            confirm_button = ttk.Button(button_frame, text="Confirm", width=10,
                                      command=lambda: [on_confirm(dialog), dialog.destroy()])
            confirm_button.grid(row=0, column=0, padx=5)
            
            cancel_button = ttk.Button(button_frame, text="Cancel", width=10,
                                     command=lambda: [on_cancel(dialog), dialog.destroy()])
            cancel_button.grid(row=0, column=1, padx=5)
            
            # Configure grid weights
            dialog.columnconfigure(0, weight=1)
            dialog.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            controls_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)
            
        except Exception as e:
            print(f"Error creating confirmation dialog: {e}")
            messagebox.showerror("Error", "Failed to create confirmation dialog")
            dialog.destroy()
    
    def _process_screenshot(self, file_path: str):
        """Process the screenshot after confirmation."""
        try:
            # Perform OCR
            result = self.ocr_service.perform_ocr(file_path)
            if result:
                # Show result editor window
                editor = tk.Toplevel(self.root)
                editor.title("OCR Result")
                editor.attributes('-topmost', True)  # Make window stay on top
                
                try:
                    # Load and resize image
                    image = Image.open(file_path)
                    image_size = self._calculate_image_size(image)
                    image = image.resize(image_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Calculate window size
                    window_size = self._calculate_window_size(image_size)
                    editor.geometry(f"{window_size[0]}x{window_size[1]}")
                    
                    # Center the window on screen
                    editor.update_idletasks()
                    x = (editor.winfo_screenwidth() - window_size[0]) // 2
                    y = (editor.winfo_screenheight() - window_size[1]) // 2
                    editor.geometry(f"+{x}+{y}")
                    
                    # Create main container
                    main_frame = ttk.Frame(editor, padding="10")
                    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                    
                    # Create image frame
                    image_frame = ttk.Frame(main_frame)
                    image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
                    
                    # Display image
                    image_label = ttk.Label(image_frame, image=photo)
                    image_label.image = photo  # Keep a reference
                    image_label.grid(row=0, column=0)
                    
                    # Create text frame
                    text_frame = ttk.Frame(main_frame)
                    text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
                    
                    # Create text box
                    ttk.Label(text_frame, text="Recognized Text:").grid(row=0, column=0, sticky=tk.W)
                    text_box = tk.Text(text_frame, wrap=tk.WORD, width=60, height=10)
                    text_box.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
                    text_box.insert('1.0', result['text'])
                    
                    # Create web controls frame
                    web_frame = ttk.Frame(main_frame)
                    web_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
                    
                    # Create web preset dropdown
                    web_preset = ttk.Combobox(web_frame, values=list(self.web_presets.keys()), width=20)
                    web_preset.grid(row=0, column=0, padx=5)
                    web_preset.set(list(self.web_presets.keys())[0])
                    
                    # Create send button
                    send_button = ttk.Button(web_frame, text="Send", width=10,
                                           command=lambda: [self._on_send(web_preset.get(), 
                                                                        text_box.get('1.0', tk.END).strip()),
                                                          editor.destroy()])
                    send_button.grid(row=0, column=1, padx=5)
                    
                    # Create action buttons frame
                    button_frame = ttk.Frame(main_frame)
                    button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
                    
                    # Create action buttons
                    copy_button = ttk.Button(button_frame, text="Copy", width=10,
                                           command=lambda: self._on_copy(text_box.get('1.0', tk.END).strip(),
                                                                       editor))
                    copy_button.grid(row=0, column=0, padx=5)
                    
                    discard_button = ttk.Button(button_frame, text="Discard", width=10,
                                              command=lambda: self._on_discard(editor))
                    discard_button.grid(row=0, column=1, padx=5)
                    
                    exit_button = ttk.Button(button_frame, text="Exit", width=10,
                                           command=self._on_exit)
                    exit_button.grid(row=0, column=2, padx=5)
                    
                    # Configure grid weights
                    editor.columnconfigure(0, weight=1)
                    editor.rowconfigure(0, weight=1)
                    main_frame.columnconfigure(0, weight=1)
                    text_frame.columnconfigure(0, weight=1)
                    web_frame.columnconfigure(0, weight=1)
                    button_frame.columnconfigure(0, weight=1)
                    button_frame.columnconfigure(1, weight=1)
                    button_frame.columnconfigure(2, weight=1)
                    
                except Exception as e:
                    print(f"Error showing result editor: {e}")
                    messagebox.showerror("Error", "Failed to show result editor")
                    editor.destroy()
            else:
                messagebox.showerror("Error", "Failed to perform OCR on the image")
            
        except Exception as e:
            print(f"Error processing screenshot: {e}")
            messagebox.showerror("Error", f"Failed to process screenshot: {e}")

    def _on_send(self, preset_name: str, text: str = None):
        """Handle send button click."""
        try:
            if preset_name in self.web_presets:
                base_url = self.web_presets[preset_name]
                if text:
                    # Properly URL encode the text
                    encoded_text = urllib.parse.quote(text)
                    
                    url = f"{base_url}{encoded_text}"
                    
                    print(f"Opening URL: {url}")
                    webbrowser.open(url)
                else:
                    print("No text to send")
                    messagebox.showwarning("Warning", "No text selected to send")
            else:
                print(f"Unknown web preset: {preset_name}")
                messagebox.showerror("Error", f"Unknown web preset: {preset_name}")
        except Exception as e:
            print(f"Error sending to web preset: {e}")
            messagebox.showerror("Error", f"Failed to send to web preset: {e}")

    def _on_copy(self, text: str, window: Optional[tk.Toplevel] = None):
        """Handle copy button click."""
        print("Copying text to clipboard...")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if window:
            window.destroy()

    def _on_discard(self, window: Optional[tk.Toplevel] = None):
        """Handle discard button click."""
        print("Discarding screenshot...")
        if window:
            window.destroy()

    def _on_exit(self):
        """Handle exit button click or window close."""
        try:
            print("Exiting program...")
            if self.file_watcher:
                self.file_watcher.stop()
            
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # Destroy the root window
            self.root.destroy()
            
            # Force quit the application
            self.root.quit()
            
            # Force exit the program immediately
            os._exit(0)
            
        except Exception as e:
            print(f"Error during exit: {e}")
            print("Forcing exit due to error...")
            # Force exit even if there's an error
            os._exit(1)
