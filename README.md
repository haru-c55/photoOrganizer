# Photo Organizer

A Python application to organize photos based on EXIF date taken.

## Features
- Organizes photos into folders by date (e.g., `2023/10/27`).
- Renames files sequentially (e.g., `IMG_0001.jpg`).
- Supports various image formats (JPG, PNG, ARW, CR2, etc.).
- Modern GUI with progress tracking.

## Build Instructions

### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### Windows
To build the executable on Windows:

```powershell
# Install dependencies
pip install -r requirements.txt

# Build using the spec file
pyinstaller PhotoOrganizer.spec --clean --noconfirm
```
The executable will be located in `dist/PhotoOrganizer.exe`.

### Linux
To build the executable on Linux:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the build script
sh build_linux.sh
```
The executable will be located in `dist/PhotoOrganizer`.
