# Photo Organizer

Python application that automatically organizes your photos and videos by their creation date, extracting metadata from EXIF data and file headers. Available in both command-line and GUI versions.

## Features

- 📁 **Automatic Organization**: Sorts photos and videos into Year/Month folder structure
- 🖼️ **Multi-Format Support**: Handles JPEG, PNG, GIF, WebP, TIFF, BMP, HEIC/HEIF, RAW (CR2, CR3, NEF, ARW, DNG, ORF, RW2, RAF), MOV, MP4, AVI, M4V, MKV, WebM, 3GP, and more
- 📅 **Smart Date Detection**: 6-level fallback chain — EXIF, Pillow, XMP metadata, filename patterns, and filesystem timestamps
- 🖥️ **Dual Interface**: Command-line tool and modern GUI interface
- 🔍 **Real-time Logging**: See what's happening during organization
- ✅ **Safe Operations**: Handles duplicates and file conflicts gracefully

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/photo_organizer.git
cd photo_organizer
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows (Git Bash):
source .venv/Scripts/activate
# On Windows (Command Prompt):
.venv\Scripts\activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg (optional, **recommended** for fast video processing):
```bash
# Fedora/RHEL:
sudo dnf install ffmpeg
# Debian/Ubuntu:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg
# Windows:
winget install FFmpeg
```

> Without FFmpeg the app still works — it falls back to the hachoir library, which is slower on large video files.

## Usage

### GUI Interface (Recommended)

Launch the graphical interface:
```bash
python run.py --gui
```

Or use the launcher script:
```bash
python launch_gui.py
```

The GUI provides:
- 📂 **Folder Selection**: Easy browse buttons for source and destination
- ▶️ **Start Button**: One-click organization process
- 📊 **Progress Tracking**: Real-time progress with status updates
- 📝 **Live Logging**: See exactly what files are being processed
- ⚠️ **Error Handling**: Clear error messages and validation

### Command Line Interface

For automated workflows or advanced users:

```bash
# Use default directories (from utils.py)
python run.py

# Specify custom directories
python run.py -o /path/to/photos -d /path/to/organized

# Show help
python run.py --help

# Show version
python run.py --version
```

## Output Structure

Photos are organized into this structure:
```
destination_folder/
├── 2023/
│   ├── 01/          # January 2023
│   ├── 02/          # February 2023
│   └── ...
├── 2024/
│   ├── 01/
│   └── ...
└── Unknown/         # Files without extractable dates
```

## Supported File Types

| Type | Extensions | Metadata Source |
|------|------------|----------------|
| Photos | `.jpg`, `.jpeg` | EXIF data |
| HEIC/HEIF | `.heic`, `.heif` | EXIF via pillow-heif |
| Images | `.png`, `.gif`, `.webp`, `.tiff`, `.tif`, `.bmp`, `.mpo`, `.avif` | Pillow metadata / EXIF |
| JPEG 2000 | `.jp2`, `.j2k` | EXIF via Pillow |
| RAW | `.dng`, `.cr2`, `.cr3`, `.nef`, `.arw`, `.orf`, `.rw2`, `.raf` | EXIF via exifread |
| Videos | `.mov`, `.mp4`, `.avi`, `.m4v`, `.3gp`, `.mkv`, `.webm` | ffprobe (hachoir fallback) |

## Development

### Running Tests

```bash
pytest photo_organizer/tests/
```

### Running Tests with Coverage

```bash
pytest --cov=photo_organizer photo_organizer/tests/
```

### Development Helper

Use the development script for common tasks:

```bash
# Run tests
python dev.py test

# Create test data for GUI testing
python dev.py testdata

# Launch GUI for testing
python dev.py gui

# Run CLI with test data
python dev.py cli

# Run linting (if available)
python dev.py lint
```

### Project Structure

```
photo_organizer/
├── photo_organizer/           # Main package
│   ├── __init__.py
│   ├── main.py               # Entry point with CLI/GUI selection
│   ├── organize_photos.py    # Core organization logic
│   ├── exif.py              # EXIF data extraction (exif lib + Pillow fallback)
│   ├── date_utils.py        # Date validation, XMP parsing, filesystem dates
│   ├── utils.py             # Command line argument parsing
│   ├── error_handling.py    # Error handling utilities
│   ├── log.py               # Logging configuration
│   ├── file_operations.py   # File system operations
│   ├── file_types/          # Consolidated file extractors
│   │   ├── __init__.py      # Unified registry interface
│   │   ├── video_extractors.py  # Video formats (ffprobe + hachoir fallback)
│   │   ├── image_extractors.py  # Image formats (PNG, GIF, WebP, TIFF, etc.)
│   │   ├── raw_extractors.py    # Camera RAW formats (CR2, NEF, ARW, DNG, etc.)
│   │   └── heif_extractor.py    # HEIC/HEIF support (iPhone photos)
│   └── tests/               # Test suite
├── gui/                     # GUI application
│   └── photo_organizer_gui.py
├── run.py                   # Main launcher
├── launch_gui.py           # GUI-only launcher
├── dev.py                  # Development helper script
└── requirements.txt        # Python dependencies
```

## Requirements

- Python 3.7+
- PySide6 (for GUI)
- Pillow (image processing)
- pillow-heif (HEIC/HEIF support)
- exif (EXIF data)
- exifread (RAW format metadata)
- hachoir (video metadata fallback)
- **Optional**: FFmpeg (`ffprobe`) for fast video metadata extraction

## License

GNU General Public License v3.0 - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Troubleshooting

### GUI Won't Start
- Ensure PySide6 is installed: `pip install PySide6`
- Check Python version (3.7+ required)

### Files Not Being Organized
- Check file permissions in source directory
- Verify files have EXIF data or metadata
- Check logs for specific error messages

### Performance Issues
- Install FFmpeg for fast video processing (`ffprobe`)
- For large directories, use command-line interface
- Ensure adequate disk space in destination
- Close other applications that might lock files