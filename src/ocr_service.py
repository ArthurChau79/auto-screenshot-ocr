import base64
import time
from typing import Optional, Dict
import requests
from PIL import Image
import io
from config import MAX_RETRIES, RETRY_DELAY, TIMEOUT, MAX_IMAGE_SIZE, IMAGE_QUALITY

class OCRService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.timeout = TIMEOUT

    def compress_image(self, file_path: str) -> bytes:
        """Compress image before sending to API."""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Calculate new size while maintaining aspect ratio
                ratio = min(MAX_IMAGE_SIZE / img.width, MAX_IMAGE_SIZE / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                # Resize image
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save to bytes with compression
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=IMAGE_QUALITY, optimize=True)
                return output.getvalue()
                
        except Exception as e:
            print(f"Error compressing image: {e}")
            # Return original file if compression fails
            with open(file_path, 'rb') as f:
                return f.read()

    def perform_ocr(self, file_path: str) -> Optional[Dict[str, str]]:
        """Perform OCR on image with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                # Compress image before sending
                image_data = self.compress_image(file_path)
                content = base64.b64encode(image_data).decode('utf-8')
                
                # Use only TEXT_DETECTION (free feature)
                payload = {
                    "requests": [{
                        "image": {
                            "content": content
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 1
                            }
                        ],
                        "imageContext": {
                            "languageHints": ["en"]
                        }
                    }]
                }
                
                url = f'https://vision.googleapis.com/v1/images:annotate?key={self.api_key}'
                response = self.session.post(url, json=payload, timeout=self.timeout)
                
                # Log the response for debugging
                print(f"API Response Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"API Error Response: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                
                # Process the response to get the text result
                if 'responses' in data and data['responses']:
                    response = data['responses'][0]
                    
                    # Get text from textAnnotations
                    if 'textAnnotations' in response and response['textAnnotations']:
                        text = response['textAnnotations'][0].get('description', '')
                        
                        if text:
                            # Clean up the text
                            text = ' '.join(text.split())  # Remove extra whitespace
                            return {"text": text}
                        else:
                            print("No text found in the image")
                            return None
                
                return None
                
            except requests.exceptions.RequestException as e:
                print(f"API request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except Exception as e:
                print(f"OCR processing failed: {e}")
                return None
        
        return None 