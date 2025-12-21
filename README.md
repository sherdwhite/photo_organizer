# Photo Organizer

A powerful Python application that automatically organizes your photos and videos by their creation date, extracting metadata from EXIF data and file headers. Available in both command-line and GUI versions.

## Features

- 📁 **Automatic Organization**: Sorts photos and videos into Year/Month folder structure
- 🖼️ **Multi-Format Support**: Handles JPEG, PNG, GIF, MOV, MP4, AVI, M4V, 3GP files
- 📅 **Smart Date Detection**: Uses EXIF data, file metadata, and creation dates
- 🖥️ **Dual Interface**: Command-line tool and modern GUI interface
- 🔍 **Real-time Logging**: See what's happening during organization
- ✅ **Safe Operations**: Handles duplicates and file conflicts gracefully
- 🛡️ **Error Handling**: Robust error handling with detailed logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/photo_organizer.git
cd photo_organizer
```

2. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (Git Bash):
source venv/Scripts/activate
# On Windows (Command Prompt):
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install system dependencies (Fedora/RHEL):
```bash
# Required for building gevent's C extensions
sudo dnf install gcc python3-devel
```

> **Note for Fedora/RHEL users**: The `gevent` package requires compiling C extensions. You must install `gcc` and `python3-devel` before running pip install.
>
> **For other Linux distributions**:
> - Debian/Ubuntu: `sudo apt install build-essential python3-dev`
> - Arch: `sudo pacman -S base-devel`

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

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
| PNG Images | `.png` | File metadata |
| GIF Images | `.gif` | File metadata |
| Videos | `.mov`, `.mp4`, `.avi`, `.m4v`, `.3gp` | Container metadata |

## Development

### Running Tests

```bash
pytest photo_organizer/tests/
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
│   ├── exif.py              # EXIF data extraction
│   ├── utils.py             # Command line argument parsing
│   ├── error_handling.py    # Error handling utilities
│   ├── log.py               # Logging configuration
│   ├── file_operations.py   # File system operations
│   ├── file_types/          # Consolidated file extractors
│   │   ├── __init__.py      # Unified registry interface
│   │   ├── video_extractors.py  # Video formats (MOV, MP4, AVI, M4V, 3GP)
│   │   └── image_extractors.py  # Image formats (PNG, GIF)
│   └── tests/               # Test suite
├── gui/                     # GUI application
│   └── photo_organizer_gui.py
├── run.py                   # Main launcher
├── launch_gui.py           # GUI-only launcher
├── dev.py                  # Development helper script
└── requirements.txt        # Dependencies
```

## Requirements

- Python 3.7+
- PyQt6 (for GUI)
- Pillow (image processing)
- hachoir (video metadata)
- exif (EXIF data)
- gevent (async operations)

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
- Ensure PyQt6 is installed: `pip install PyQt6`
- Check Python version (3.7+ required)

### Files Not Being Organized
- Check file permissions in source directory
- Verify files have EXIF data or metadata
- Check logs for specific error messages

### Performance Issues
- For large directories, use command-line interface
- Ensure adequate disk space in destination
- Close other applications that might lock files