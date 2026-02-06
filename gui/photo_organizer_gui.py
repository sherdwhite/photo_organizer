import faulthandler
import logging
import os
import sys
import traceback

from PyQt5.QtCore import QMetaType, QObject, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from photo_organizer.organize_photos import organize

# Register QTextCursor so queued signal-slot connections that
# involve it internally (e.g. QTextEdit) don't produce the
# "Cannot queue arguments of type 'QTextCursor'" warning.
QMetaType.type("QTextCursor")

# Enable faulthandler so native crashes (segfault, etc.) print a
# Python traceback to stderr before the process dies.
faulthandler.enable()

logger = logging.getLogger(__name__)


def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler to log unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.error(f"Unhandled exception:\n{error_msg}")

    # Write to crash log
    try:
        crash_log = os.path.join(os.getcwd(), "gui_crash.log")
        with open(crash_log, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Unhandled Exception at " f"{os.popen('date').read().strip()}\n")
            f.write(f"{'='*80}\n")
            f.write(error_msg)
        print(
            f"Exception logged to: {crash_log}",
            file=sys.stderr,
        )
    except Exception:
        pass

    # Show a modal error dialog so the user sees what happened
    try:
        app = QApplication.instance()
        if app is not None:
            dlg = QMessageBox()
            dlg.setIcon(QMessageBox.Critical)
            dlg.setWindowTitle("Photo Organizer — Crash")
            dlg.setText(
                "An unexpected error occurred and the application " "needs to close."
            )
            dlg.setDetailedText(error_msg)
            dlg.setStandardButtons(QMessageBox.Ok)
            dlg.exec_()
    except Exception:
        pass


# Install global exception hook
sys.excepthook = exception_hook


class LogSignalBridge(QObject):
    """Bridge that safely relays log messages to the GUI thread.

    Qt widgets must only be modified from the main thread.  This
    object lives on the main thread and receives log text via a
    queued signal connection, so the actual QTextEdit.append()
    always runs on the GUI thread — eliminating the segfault that
    occurred when LogHandler wrote from the worker thread directly.
    """

    log_message = pyqtSignal(str)

    def __init__(self, text_widget, parent=None):
        super().__init__(parent)
        self.text_widget = text_widget
        self.message_count = 0
        self.max_messages = 1000

        # Queued connection ensures the slot runs on the main thread
        self.log_message.connect(self._append_message, Qt.QueuedConnection)

    def _append_message(self, msg: str):
        """Append a formatted log message (runs on GUI thread)."""
        try:
            if self.message_count >= self.max_messages:
                self.text_widget.clear()
                self.text_widget.append(
                    "... (Log cleared to prevent memory issues) ..."
                )
                self.message_count = 1

            self.text_widget.append(msg)
            self.message_count += 1
        except Exception:
            pass


class LogHandler(logging.Handler):
    """Custom logging handler that relays messages via a signal.

    This handler is thread-safe: it formats the record and emits
    a Qt signal.  The connected LogSignalBridge slot performs the
    actual widget update on the main thread.
    """

    def __init__(self, bridge: LogSignalBridge):
        super().__init__()
        self.bridge = bridge

    def emit(self, record):
        """Emit log record via signal (safe from any thread)."""
        try:
            msg = self.format(record)
            if record.levelno >= logging.INFO:
                self.bridge.log_message.emit(msg)
        except Exception:
            pass


class OrganizerWorker(QThread):
    """Worker thread for organizing photos to avoid blocking the GUI."""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, origin_dir: str, destination_dir: str):
        super().__init__()
        self.origin_dir = origin_dir
        self.destination_dir = destination_dir

    def run(self):
        """Run the photo organization in a separate thread."""
        try:
            # Reduce logging level to prevent overwhelming the GUI
            logging.getLogger("photo_organizer").setLevel(logging.WARNING)

            self.progress.emit("Starting photo organization...")

            # Define progress callback
            def progress_callback(message):
                self.progress.emit(message)

            # Run the organization process with progress callback
            organize(self.origin_dir, self.destination_dir, progress_callback)

            self.progress.emit("Photo organization completed successfully!")
            self.finished.emit()

        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"Error during photo organization: {e}"
            self.progress.emit(error_msg)
            self.error.emit(f"{e}\n\n--- Traceback ---\n{tb}")
        finally:
            # Restore normal logging level
            logging.getLogger("photo_organizer").setLevel(logging.INFO)


class PhotoOrganizerGUI(QMainWindow):
    """Main GUI window for the Photo Organizer application."""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.log_handler = None
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Photo Organizer")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("Photo Organizer")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Directory selection group
        dir_group = QGroupBox("Directory Selection")
        dir_layout = QGridLayout(dir_group)

        # Origin directory
        origin_label = QLabel("Source Directory:")
        self.origin_path = QLineEdit()
        self.origin_path.setPlaceholderText(
            "Select folder containing photos to organize..."
        )
        origin_browse_btn = QPushButton("Browse...")
        origin_browse_btn.clicked.connect(self.browse_origin_directory)

        dir_layout.addWidget(origin_label, 0, 0)
        dir_layout.addWidget(self.origin_path, 0, 1)
        dir_layout.addWidget(origin_browse_btn, 0, 2)

        # Destination directory
        dest_label = QLabel("Destination Directory:")
        self.dest_path = QLineEdit()
        self.dest_path.setPlaceholderText(
            "Select folder where organized photos will be stored..."
        )
        dest_browse_btn = QPushButton("Browse...")
        dest_browse_btn.clicked.connect(self.browse_destination_directory)

        dir_layout.addWidget(dest_label, 1, 0)
        dir_layout.addWidget(self.dest_path, 1, 1)
        dir_layout.addWidget(dest_browse_btn, 1, 2)

        main_layout.addWidget(dir_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.organize_btn = QPushButton("Start Organizing")
        self.organize_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        )
        self.organize_btn.clicked.connect(self.start_organizing)

        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)

        button_layout.addWidget(self.organize_btn)
        button_layout.addWidget(self.clear_log_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log output group
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_group)

        # Status bar
        self.statusBar().showMessage("Ready to organize photos")

        # Permanent progress label on the right side of the status bar
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Consolas", 9))
        self.statusBar().addPermanentWidget(self.progress_label)

    def setup_logging(self):
        """Set up logging to redirect to the GUI text widget."""
        # Create signal bridge (lives on main thread, owns the widget update)
        self.log_bridge = LogSignalBridge(self.log_text, parent=self)

        # Create custom handler that emits via the bridge signal
        self.log_handler = LogHandler(self.log_bridge)
        self.log_handler.setLevel(logging.WARNING)

        # Format the log messages
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        self.log_handler.setFormatter(formatter)

        # Add handler to photo_organizer specific loggers only
        photo_organizer_logger = logging.getLogger("photo_organizer")
        photo_organizer_logger.addHandler(self.log_handler)
        photo_organizer_logger.setLevel(logging.INFO)

        # Prevent propagation to root logger to avoid duplicate messages
        photo_organizer_logger.propagate = False

    def browse_origin_directory(self):
        """Open dialog to select origin directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Source Directory", "", QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.origin_path.setText(directory)

    def browse_destination_directory(self):
        """Open dialog to select destination directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Destination Directory", "", QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.dest_path.setText(directory)

    def validate_inputs(self) -> bool:
        """Validate user inputs before starting organization."""
        origin = self.origin_path.text().strip()
        destination = self.dest_path.text().strip()

        if not origin:
            QMessageBox.warning(
                self, "Invalid Input", "Please select a source directory."
            )
            return False

        if not destination:
            QMessageBox.warning(
                self, "Invalid Input", "Please select a destination directory."
            )
            return False

        if not os.path.exists(origin):
            QMessageBox.warning(
                self, "Invalid Input", "Source directory does not exist."
            )
            return False

        if not os.path.isdir(origin):
            QMessageBox.warning(
                self, "Invalid Input", "Source path is not a directory."
            )
            return False

        if origin == destination:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Source and destination directories cannot be the same.",
            )
            return False

        return True

    def start_organizing(self):
        """Start the photo organization process."""
        if not self.validate_inputs():
            return

        origin = self.origin_path.text().strip()
        destination = self.dest_path.text().strip()

        # Create destination directory if it doesn't exist
        try:
            os.makedirs(destination, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Could not create destination directory: {e}"
            )
            return

        # Disable controls during processing
        self.organize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Organizing photos...")

        # Clear previous log
        self.log_text.clear()

        # Start worker thread
        self.worker = OrganizerWorker(origin, destination)
        self.worker.finished.connect(self.on_organization_finished)
        self.worker.error.connect(self.on_organization_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()

    def on_organization_finished(self):
        """Handle completion of photo organization."""
        self.organize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.statusBar().showMessage("Photo organization completed successfully!")

        QMessageBox.information(
            self, "Success", "Photo organization completed successfully!"
        )

    def on_organization_error(self, error_msg: str):
        """Handle errors during photo organization.

        Shows a modal dialog with an OK button.  The full traceback
        is available via the 'Show Details...' button.
        """
        self.organize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.statusBar().showMessage("Error occurred during organization")

        # Split short summary from full traceback (if present)
        if "\n\n--- Traceback ---\n" in error_msg:
            summary, details = error_msg.split("\n\n--- Traceback ---\n", 1)
        else:
            summary = error_msg
            details = ""

        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Photo Organizer — Error")
        dlg.setText("An error occurred during photo organization.")
        dlg.setInformativeText(summary)
        if details:
            dlg.setDetailedText(details)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def on_progress_update(self, message: str):
        """Handle progress updates.

        Per-file 'Processing file ...' messages only update the
        status bar label (bottom-right). Other messages (Found,
        Complete, etc.) are also appended to the log text area.
        """
        self.progress_label.setText(message)

        # Only append non-per-file messages to the log to avoid spam
        if not message.startswith("Processing file "):
            self.log_text.append(message)

    def clear_log(self):
        """Clear the log text area."""
        self.log_text.clear()
        self.statusBar().showMessage("Log cleared")

    def closeEvent(self, event):
        """Handle application close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Close Application",
                "Photo organization is in progress. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def run_gui():
    """Run the Photo Organizer GUI application."""
    try:
        logger.info("Initializing QApplication...")
        app = QApplication(sys.argv)
        app.setApplicationName("Photo Organizer")
        logger.info("QApplication initialized successfully")

        # Set application style
        logger.info("Setting application style...")
        app.setStyle("Fusion")
        logger.info("Application style set successfully")

        logger.info("Creating PhotoOrganizerGUI window...")
        window = PhotoOrganizerGUI()
        logger.info("Window created successfully")

        logger.info("Showing window...")
        window.show()
        logger.info("Window shown successfully")

        logger.info("Starting event loop...")
        return app.exec()

    except Exception as e:
        error_msg = (
            f"Fatal error during GUI initialization: {e}\n{traceback.format_exc()}"
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)

        # Try to write to a crash log file
        try:
            crash_log = os.path.join(os.getcwd(), "gui_crash.log")
            with open(crash_log, "w") as f:
                f.write(error_msg)
            print(f"\nCrash details written to: {crash_log}")
        except Exception as log_error:
            print(f"Could not write crash log: {log_error}")

        return 1


if __name__ == "__main__":
    run_gui()
