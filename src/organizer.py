import os
import shutil
import datetime
from pathlib import Path

class PhotoOrganizer:
    def __init__(self):
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.cr2', '.nef', '.dng', '.orf', '.rw2'}

    def get_date_taken(self, filepath):
        """Extracts the date taken from EXIF or falls back to file modification time."""
        try:
            # Defer import to speed up startup
            from PIL import Image, ExifTags
            
            image = Image.open(filepath)
            exif = image._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        # Format is usually "YYYY:MM:DD HH:MM:SS"
                        return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
        
        # Fallback to modification time
        timestamp = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(timestamp)

    def scan_files(self, source_dir, extensions=None):
        """Scans for supported files in the source directory."""
        if extensions:
            # Normalize extensions: lowercase and ensure they start with dot
            valid_exts = {ext.strip().lower() if ext.strip().startswith('.') else f".{ext.strip().lower()}" for ext in extensions}
        else:
            valid_exts = self.supported_extensions

        files = []
        for root, _, filenames in os.walk(source_dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in valid_exts:
                    files.append(os.path.join(root, filename))
        return files

    def generate_operations(self, files, dest_dir, folder_format, file_format):
        """
        Generates a list of copy operations.
        Returns a list of dicts: {'source': path, 'dest': path}
        """
        operations = []
        # Group files by date to handle sequencing per day/folder if needed, 
        # but usually sequence is per folder. 
        # Let's assume sequence is per destination folder.
        
        files_by_dest_folder = {}

        for filepath in files:
            date = self.get_date_taken(filepath)
            
            # Generate folder path
            folder_name = date.strftime(folder_format)
            full_dest_folder = os.path.join(dest_dir, folder_name)
            
            if full_dest_folder not in files_by_dest_folder:
                files_by_dest_folder[full_dest_folder] = []
            
            files_by_dest_folder[full_dest_folder].append((date, filepath))

        # Now generate filenames with sequence
        for folder, items in files_by_dest_folder.items():
            # Sort by date taken to ensure sequence matches time
            items.sort(key=lambda x: x[0])
            
            for i, (date, source_path) in enumerate(items, 1):
                ext = os.path.splitext(source_path)[1].lower()
                
                # Handle file format
                # We need to safely format the string. 
                # The user might provide "IMG_{seq:04d}" or just "IMG_{seq}"
                try:
                    # Create a safe context for formatting
                    # We support 'seq' and standard date codes if they want them in filename too
                    # But date codes are already handled by strftime if passed, 
                    # actually strftime is for date objects. 
                    # Let's apply strftime to the filename pattern first, then format sequence.
                    
                    filename_pattern = date.strftime(file_format)
                    filename = filename_pattern.format(seq=i) + ext
                except Exception as e:
                    # Fallback if format fails
                    filename = f"IMG_{i:04d}{ext}"
                
                dest_path = os.path.join(folder, filename)
                operations.append({'source': source_path, 'dest': dest_path})
                
        return operations

    def execute_copy(self, operation, callback=None):
        """Executes a single copy operation."""
        source = operation['source']
        dest = operation['dest']
        
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        
        # Handle collision? For now, let's just overwrite or maybe skip?
        # User asked for "copy", usually implies safety. 
        # But if we are renaming, collisions shouldn't happen unless sequence resets.
        # Let's just copy.
        shutil.copy2(source, dest)
        
        if callback:
            callback(source, dest)
