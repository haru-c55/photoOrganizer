import os
import shutil
import hashlib
import datetime

class PhotoOrganizer:
    def __init__(self):
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.cr2', '.nef', '.dng', '.orf', '.rw2', '.raf'}

    def _hash_file(self, filepath):
        h = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    def _build_filename(self, date, file_format, seq, ext):
        try:
            return date.strftime(file_format).format(seq=seq) + ext
        except Exception:
            return f"IMG_{seq:04d}{ext}"

    def get_date_taken(self, filepath):
        """Date taken: PIL EXIF (JPEG/PNG) -> exifread EXIF (RAW) -> file mtime."""
        # 1) PIL handles standard formats (JPEG/PNG) quickly.
        try:
            from PIL import Image, ExifTags

            image = Image.open(filepath)
            exif = image._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass

        # 2) exifread can read EXIF from RAW files (RAF, ARW, CR2, NEF, ...).
        try:
            import logging
            import exifread
            # exifread logs "File format not recognized." for non-image files; quiet it.
            logging.getLogger('exifread').setLevel(logging.CRITICAL)

            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=False, stop_tag='EXIF DateTimeOriginal')
            value = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
            if value:
                return datetime.datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass

        # 3) Fallback to file modification time.
        timestamp = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(timestamp)

    def scan_files(self, source_dir, extensions=None):
        if extensions:
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
        Generates a list of copy operations, skipping files already in the destination (by hash).
        Returns a list of dicts: {'source': path, 'dest': path}
        Also returns a count of skipped duplicates as second value.
        """
        operations = []
        skipped = 0
        files_by_dest_folder = {}

        for filepath in files:
            date = self.get_date_taken(filepath)
            folder_name = date.strftime(folder_format)
            full_dest_folder = os.path.join(dest_dir, folder_name)

            if full_dest_folder not in files_by_dest_folder:
                files_by_dest_folder[full_dest_folder] = []

            files_by_dest_folder[full_dest_folder].append((date, filepath))

        for folder, items in files_by_dest_folder.items():
            items.sort(key=lambda x: x[0])

            # Inspect existing files in the destination folder:
            # - existing_hashes: to skip identical files already imported
            # - used_names: to avoid generating a name that collides with an existing file
            existing_hashes = set()
            used_names = set()
            existing_count = 0
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    fpath = os.path.join(folder, f)
                    if os.path.isfile(fpath):
                        used_names.add(f.lower())
                        if os.path.splitext(f)[1].lower() in self.supported_extensions:
                            existing_hashes.add(self._hash_file(fpath))
                            existing_count += 1

            # Start numbering after existing files, but always verify the name is free.
            seq = existing_count + 1
            for date, source_path in items:
                if existing_hashes:
                    src_hash = self._hash_file(source_path)
                    if src_hash in existing_hashes:
                        skipped += 1
                        continue
                    existing_hashes.add(src_hash)

                ext = os.path.splitext(source_path)[1].lower()

                # Find a filename that collides with neither an existing file
                # nor a name already assigned in this run.
                filename = self._build_filename(date, file_format, seq, ext)
                while filename.lower() in used_names:
                    seq += 1
                    candidate = self._build_filename(date, file_format, seq, ext)
                    if candidate == filename:
                        # Format does not vary with seq; disambiguate with a suffix.
                        base, e = os.path.splitext(filename)
                        candidate = f"{base}_{seq}{e}"
                    filename = candidate

                used_names.add(filename.lower())
                dest_path = os.path.join(folder, filename)
                operations.append({'source': source_path, 'dest': dest_path})
                seq += 1

        return operations, skipped

    def execute_copy(self, operation):
        source = operation['source']
        dest = operation['dest']

        os.makedirs(os.path.dirname(dest), exist_ok=True)

        # Safety net: dest names are made collision-free in generate_operations,
        # so an existing dest here means an unexpected clash. Never overwrite.
        if os.path.exists(dest):
            return False

        shutil.copy2(source, dest)
        return True
