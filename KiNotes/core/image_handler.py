"""
KiNotes Image Handler - Manages image storage and retrieval.

This module handles:
- Saving images from clipboard/files to .kinotes/images/
- Generating unique filenames with timestamps
- Returning relative markdown paths
- Loading images for display in visual editor
- Resolving paths for PDF export

Usage:
    from core.image_handler import ImageHandler
    
    handler = ImageHandler(kinotes_dir)
    rel_path = handler.save_from_clipboard(wx_bitmap)
    abs_path = handler.resolve_path("./images/screenshot_20251217.png")
    wx_image = handler.load_image(rel_path)
"""

import os
import datetime
import hashlib

# Import config - handle both plugin and standalone contexts
try:
    from .defaultsConfig import IMAGE_DEFAULTS, debug_print, debug_module
except ImportError:
    from defaultsConfig import IMAGE_DEFAULTS, debug_print, debug_module


class ImageHandler:
    """Handles image storage and retrieval for KiNotes."""
    
    def __init__(self, kinotes_dir):
        """
        Initialize image handler.
        
        Args:
            kinotes_dir: Path to .kinotes directory (e.g., /project/.kinotes)
        """
        self.kinotes_dir = kinotes_dir
        self.images_dir = os.path.join(kinotes_dir, IMAGE_DEFAULTS['folder_name'])
        self._ensure_images_dir()
    
    def _ensure_images_dir(self):
        """Create images directory if it doesn't exist."""
        if not os.path.exists(self.images_dir):
            try:
                os.makedirs(self.images_dir, exist_ok=True)
                debug_module('image', f"Created images dir: {self.images_dir}")
            except Exception as e:
                debug_module('image', f"Error creating dir: {e}")
    
    def _generate_filename(self, prefix="image", ext="png"):
        """
        Generate unique filename with timestamp.
        
        Args:
            prefix: Filename prefix (e.g., "screenshot", "paste")
            ext: File extension without dot
        
        Returns:
            Unique filename like "screenshot_20251217_143052.png"
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{ext}"
        
        # Add counter if file exists (rare edge case)
        full_path = os.path.join(self.images_dir, filename)
        if os.path.exists(full_path):
            counter = 1
            while os.path.exists(full_path):
                filename = f"{prefix}_{timestamp}_{counter}.{ext}"
                full_path = os.path.join(self.images_dir, filename)
                counter += 1
        
        return filename
    
    def save_from_wx_image(self, wx_image, prefix="image"):
        """
        Save wx.Image to images folder.
        
        Args:
            wx_image: wx.Image object
            prefix: Filename prefix
        
        Returns:
            Relative markdown path like "./images/image_20251217.png"
            or None on failure
        """
        try:
            import wx
            
            if not wx_image or not wx_image.IsOk():
                debug_module('image', "Invalid wx.Image")
                return None
            
            # Resize if too large
            wx_image = self._resize_if_needed(wx_image)
            
            # Generate filename and save
            filename = self._generate_filename(prefix, IMAGE_DEFAULTS['default_format'])
            full_path = os.path.join(self.images_dir, filename)
            
            # Save as PNG (best for screenshots)
            if wx_image.SaveFile(full_path, wx.BITMAP_TYPE_PNG):
                debug_module('image', f"Saved: {filename}")
                return f"./{IMAGE_DEFAULTS['folder_name']}/{filename}"
            else:
                debug_module('image', "SaveFile failed")
                return None
                
        except Exception as e:
            debug_module('image', f"Save error: {e}")
            return None
    
    def save_from_bitmap(self, wx_bitmap, prefix="paste"):
        """
        Save wx.Bitmap to images folder.
        
        Args:
            wx_bitmap: wx.Bitmap object (from clipboard)
            prefix: Filename prefix
        
        Returns:
            Relative markdown path or None on failure
        """
        try:
            import wx
            
            if not wx_bitmap or not wx_bitmap.IsOk():
                debug_module('image', "Invalid wx.Bitmap")
                return None
            
            # Convert bitmap to image
            wx_image = wx_bitmap.ConvertToImage()
            return self.save_from_wx_image(wx_image, prefix)
            
        except Exception as e:
            debug_module('image', f"Bitmap save error: {e}")
            return None
    
    def save_from_file(self, source_path, prefix="imported"):
        """
        Copy image file to images folder.
        
        Args:
            source_path: Absolute path to source image
            prefix: Filename prefix
        
        Returns:
            Relative markdown path or None on failure
        """
        try:
            import shutil
            
            if not os.path.exists(source_path):
                debug_module('image', f"Source not found: {source_path}")
                return None
            
            # Get extension from source
            ext = os.path.splitext(source_path)[1].lower().lstrip('.')
            if ext not in IMAGE_DEFAULTS['supported_formats']:
                debug_module('image', f"Unsupported format: {ext}")
                return None
            
            # Check file size
            size_kb = os.path.getsize(source_path) / 1024
            if size_kb > IMAGE_DEFAULTS['max_size_kb']:
                debug_module('image', f"File too large: {size_kb:.0f}KB > {IMAGE_DEFAULTS['max_size_kb']}KB")
                return None
            
            # Generate filename and copy
            filename = self._generate_filename(prefix, ext)
            dest_path = os.path.join(self.images_dir, filename)
            shutil.copy2(source_path, dest_path)
            
            debug_module('image', f"Copied: {filename}")
            return f"./{IMAGE_DEFAULTS['folder_name']}/{filename}"
            
        except Exception as e:
            debug_module('image', f"File copy error: {e}")
            return None
    
    def _resize_if_needed(self, wx_image):
        """
        Resize image if dimensions exceed max.
        
        Args:
            wx_image: wx.Image object
        
        Returns:
            Resized wx.Image (or original if small enough)
        """
        try:
            import wx
            
            max_dim = IMAGE_DEFAULTS['max_dimension']
            width = wx_image.GetWidth()
            height = wx_image.GetHeight()
            
            if width <= max_dim and height <= max_dim:
                return wx_image
            
            # Calculate new size maintaining aspect ratio
            if width > height:
                new_width = max_dim
                new_height = int(height * (max_dim / width))
            else:
                new_height = max_dim
                new_width = int(width * (max_dim / height))
            
            debug_module('image', f"Resizing: {width}x{height} -> {new_width}x{new_height}")
            return wx_image.Scale(new_width, new_height, wx.IMAGE_QUALITY_HIGH)
            
        except Exception as e:
            debug_module('image', f"Resize error: {e}")
            return wx_image
    
    def resolve_path(self, relative_path):
        """
        Convert relative markdown path to absolute path.
        
        Args:
            relative_path: Path like "./images/file.png"
        
        Returns:
            Absolute path or None if not found
        """
        if not relative_path:
            return None
        
        # Handle ./images/ prefix
        if relative_path.startswith('./'):
            rel = relative_path[2:]  # Remove "./"
        else:
            rel = relative_path
        
        abs_path = os.path.join(self.kinotes_dir, rel)
        
        if os.path.exists(abs_path):
            return abs_path
        
        debug_module('image', f"Path not found: {abs_path}")
        return None
    
    def load_wx_image(self, relative_path, max_width=None):
        """
        Load image as wx.Image for display.
        
        Args:
            relative_path: Path like "./images/file.png"
            max_width: Maximum width for display (scales proportionally)
        
        Returns:
            wx.Image object or None on failure
        """
        try:
            import wx
            
            abs_path = self.resolve_path(relative_path)
            if not abs_path:
                return None
            
            wx_image = wx.Image(abs_path, wx.BITMAP_TYPE_ANY)
            if not wx_image.IsOk():
                debug_module('image', f"Failed to load: {abs_path}")
                return None
            
            # Scale for display if max_width specified
            if max_width and wx_image.GetWidth() > max_width:
                scale = max_width / wx_image.GetWidth()
                new_height = int(wx_image.GetHeight() * scale)
                wx_image = wx_image.Scale(max_width, new_height, wx.IMAGE_QUALITY_HIGH)
            
            return wx_image
            
        except Exception as e:
            debug_module('image', f"Load error: {e}")
            return None
    
    def load_wx_bitmap(self, relative_path, max_width=None):
        """
        Load image as wx.Bitmap for display in RichTextCtrl.
        
        Args:
            relative_path: Path like "./images/file.png"
            max_width: Maximum width for display
        
        Returns:
            wx.Bitmap object or None on failure
        """
        try:
            import wx
            
            wx_image = self.load_wx_image(relative_path, max_width)
            if wx_image:
                return wx.Bitmap(wx_image)
            return None
            
        except Exception as e:
            debug_module('image', f"Bitmap load error: {e}")
            return None
    
    def get_image_bytes(self, relative_path):
        """
        Get raw image bytes for PDF embedding.
        
        Args:
            relative_path: Path like "./images/file.png"
        
        Returns:
            Tuple (bytes, mime_type) or (None, None) on failure
        """
        try:
            abs_path = self.resolve_path(relative_path)
            if not abs_path:
                return None, None
            
            ext = os.path.splitext(abs_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
            }
            
            with open(abs_path, 'rb') as f:
                data = f.read()
            
            return data, mime_types.get(ext, 'image/png')
            
        except Exception as e:
            debug_print(f"[KiNotes Image] Read bytes error: {e}")
            return None, None
    
    def list_images(self):
        """
        List all images in the images folder.
        
        Returns:
            List of relative paths like ["./images/img1.png", "./images/img2.jpg"]
        """
        images = []
        if not os.path.exists(self.images_dir):
            return images
        
        for filename in os.listdir(self.images_dir):
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            if ext in IMAGE_DEFAULTS['supported_formats']:
                images.append(f"./{IMAGE_DEFAULTS['folder_name']}/{filename}")
        
        return sorted(images)
    
    def delete_image(self, relative_path):
        """
        Delete an image file.
        
        Args:
            relative_path: Path like "./images/file.png"
        
        Returns:
            True on success, False on failure
        """
        try:
            abs_path = self.resolve_path(relative_path)
            if abs_path and os.path.exists(abs_path):
                os.remove(abs_path)
                debug_print(f"[KiNotes Image] Deleted: {relative_path}")
                return True
            return False
        except Exception as e:
            debug_print(f"[KiNotes Image] Delete error: {e}")
            return False


def get_clipboard_image():
    """
    Get image from clipboard if available.
    
    Returns:
        wx.Bitmap or None if no image in clipboard
    """
    try:
        import wx
        
        debug_print("[KiNotes Image] get_clipboard_image: Opening clipboard...")
        if not wx.TheClipboard.Open():
            debug_print("[KiNotes Image] get_clipboard_image: Failed to open clipboard")
            return None
        
        try:
            bitmap_format = wx.DataFormat(wx.DF_BITMAP)
            debug_print(f"[KiNotes Image] get_clipboard_image: Checking for bitmap format...")
            
            if wx.TheClipboard.IsSupported(bitmap_format):
                debug_print("[KiNotes Image] get_clipboard_image: Bitmap format supported")
                bitmap_data = wx.BitmapDataObject()
                if wx.TheClipboard.GetData(bitmap_data):
                    bitmap = bitmap_data.GetBitmap()
                    if bitmap and bitmap.IsOk():
                        debug_print(f"[KiNotes Image] get_clipboard_image: Got bitmap {bitmap.GetWidth()}x{bitmap.GetHeight()}")
                        return bitmap
                    else:
                        debug_print("[KiNotes Image] get_clipboard_image: Bitmap not ok")
                else:
                    debug_print("[KiNotes Image] get_clipboard_image: GetData failed")
            else:
                debug_print("[KiNotes Image] get_clipboard_image: Bitmap format not supported")
            return None
        finally:
            wx.TheClipboard.Close()
            
    except Exception as e:
        debug_print(f"[KiNotes Image] Clipboard error: {e}")
        return None


def is_clipboard_image():
    """
    Check if clipboard contains an image.
    
    Returns:
        True if clipboard has image data
    """
    try:
        import wx
        
        if not wx.TheClipboard.Open():
            debug_print("[KiNotes Image] is_clipboard_image: Cannot open clipboard")
            return False
        
        try:
            has_bitmap = wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_BITMAP))
            debug_print(f"[KiNotes Image] is_clipboard_image: has_bitmap={has_bitmap}")
            return has_bitmap
        finally:
            wx.TheClipboard.Close()
            
    except Exception as e:
        debug_print(f"[KiNotes Image] is_clipboard_image error: {e}")
        return False
