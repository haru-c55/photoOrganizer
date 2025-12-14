import sys
import os
import json
import threading
import concurrent.futures
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from organizer import PhotoOrganizer

class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

class PhotoOrganizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Organizer")
        self.setGeometry(100, 100, 600, 550)
        
        self.organizer = PhotoOrganizer()
        self.signals = WorkerSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.log.connect(self.append_log)
        self.signals.finished.connect(self.on_finished)
        self.signals.error.connect(self.on_error)
        
        self.init_ui()
        self.apply_styles()
        self.load_settings()
        
    def apply_styles(self):
        # Modern Font
        font = QFont("Yu Gothic UI", 10)
        QApplication.setFont(font)
        
        # Modern Styling (QSS)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #333;
                font-weight: bold;
                margin-top: 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 4px;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-family: Consolas, monospace;
            }
        """)
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Source Directory
        layout.addWidget(QLabel("Source Directory:"))
        src_layout = QHBoxLayout()
        self.entry_src = QLineEdit()
        src_layout.addWidget(self.entry_src)
        btn_src = QPushButton("Browse")
        btn_src.clicked.connect(self.browse_src)
        src_layout.addWidget(btn_src)
        layout.addLayout(src_layout)
        
        # Destination Directory
        layout.addWidget(QLabel("Destination Directory:"))
        dest_layout = QHBoxLayout()
        self.entry_dest = QLineEdit()
        dest_layout.addWidget(self.entry_dest)
        btn_dest = QPushButton("Browse")
        btn_dest.clicked.connect(self.browse_dest)
        dest_layout.addWidget(btn_dest)
        layout.addLayout(dest_layout)
        
        # Extensions
        layout.addWidget(QLabel("Extensions (comma separated):"))
        self.entry_exts = QLineEdit("jpg, jpeg, png, arw, cr2, nef, dng, orf, rw2")
        self.entry_exts.setPlaceholderText("e.g. jpg, png, arw")
        layout.addWidget(self.entry_exts)
        
        # Folder Format
        layout.addWidget(QLabel("Folder Format:"))
        self.entry_folder_fmt = QLineEdit("%Y/%m/%d")
        self.entry_folder_fmt.setPlaceholderText("e.g. %Y/%m/%d")
        layout.addWidget(self.entry_folder_fmt)
        
        # File Format
        layout.addWidget(QLabel("File Name Format:"))
        self.entry_file_fmt = QLineEdit("IMG_{seq:04d}")
        self.entry_file_fmt.setPlaceholderText("e.g. IMG_{seq:04d}")
        layout.addWidget(self.entry_file_fmt)
        
        # Help Button
        btn_help = QPushButton("Help: Format Codes")
        btn_help.setStyleSheet("background-color: #6c757d;") # Secondary color
        btn_help.clicked.connect(self.show_help)
        layout.addWidget(btn_help)
        
        # Start Button
        self.btn_start = QPushButton("Start Organization")
        self.btn_start.setStyleSheet("background-color: #28a745; font-size: 14px; padding: 12px;") # Success color
        self.btn_start.clicked.connect(self.start_process)
        layout.addWidget(self.btn_start)
        
        # Progress Bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Log Area
        layout.addWidget(QLabel("Log:"))
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        layout.addWidget(self.text_log)
        
    def browse_src(self):
        path = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if path:
            self.entry_src.setText(path)
            
    def browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if path:
            self.entry_dest.setText(path)
            
    def show_help(self):
        help_text = """
        <h3>Folder Format Codes</h3>
        <p>Uses Python's strftime format:</p>
        <ul>
            <li><b>%Y</b>: Year with century (e.g. 2023)</li>
            <li><b>%m</b>: Month as zero-padded number (01-12)</li>
            <li><b>%d</b>: Day of the month (01-31)</li>
            <li><b>%H</b>: Hour (24-hour clock)</li>
            <li><b>%M</b>: Minute</li>
            <li><b>%S</b>: Second</li>
        </ul>
        <p>Example: <code>%Y/%m/%d</code> -> 2023/10/27</p>
        
        <h3>File Name Format Codes</h3>
        <p>Uses Python's format string syntax:</p>
        <ul>
            <li><b>{seq}</b>: Sequential number</li>
            <li><b>{seq:04d}</b>: Zero-padded sequence (e.g. 0001)</li>
            <li><b>{seq:03d}</b>: Zero-padded sequence (e.g. 001)</li>
        </ul>
        <p>Example: <code>IMG_{seq:04d}</code> -> IMG_0001.jpg</p>
        """
        QMessageBox.information(self, "Format Help", help_text)

    def append_log(self, message):
        self.text_log.append(message)
        
    def update_progress(self, value):
        self.progress.setValue(value)
        
    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.append_log("Completed successfully!")
        QMessageBox.information(self, "Success", "Photo organization completed!")
        
    def on_error(self, message):
        self.btn_start.setEnabled(True)
        self.append_log(f"Error: {message}")
        QMessageBox.critical(self, "Error", f"An error occurred: {message}")
        
    def start_process(self):
        src = self.entry_src.text()
        dest = self.entry_dest.text()
        exts_str = self.entry_exts.text()
        folder_fmt = self.entry_folder_fmt.text()
        file_fmt = self.entry_file_fmt.text()
        
        if not src or not dest:
            QMessageBox.warning(self, "Error", "Please select source and destination directories.")
            return
            
        if not os.path.exists(src):
            QMessageBox.warning(self, "Error", "Source directory does not exist.")
            return
            
        # Parse extensions
        extensions = [e.strip() for e in exts_str.split(',') if e.strip()]
            
        self.btn_start.setEnabled(False)
        self.text_log.clear()
        self.append_log("Scanning files...")
        
        threading.Thread(target=self.run_organization, args=(src, dest, extensions, folder_fmt, file_fmt), daemon=True).start()
        
    def run_organization(self, src, dest, extensions, folder_fmt, file_fmt):
        try:
            files = self.organizer.scan_files(src, extensions)
            self.signals.log.emit(f"Found {len(files)} files.")
            
            if not files:
                self.signals.log.emit("No matching files found.")
                self.signals.finished.emit()
                return
                
            self.signals.log.emit("Generating operations...")
            operations = self.organizer.generate_operations(files, dest, folder_fmt, file_fmt)
            
            total = len(operations)
            self.signals.progress.emit(0)
            self.progress.setMaximum(total) 
            
            self.signals.log.emit(f"Starting copy of {total} files...")
            
            completed_count = 0
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit all tasks
                future_to_op = {executor.submit(self.organizer.execute_copy, op): op for op in operations}
                
                for future in concurrent.futures.as_completed(future_to_op):
                    op = future_to_op[future]
                    try:
                        future.result()
                        completed_count += 1
                        self.signals.progress.emit(completed_count)
                        self.signals.log.emit(f"Copied: {os.path.basename(op['source'])} -> {os.path.basename(op['dest'])}")
                    except Exception as exc:
                        self.signals.log.emit(f"Error copying {os.path.basename(op['source'])}: {exc}")

            self.signals.finished.emit()
            
        except Exception as e:
            self.signals.error.emit(str(e))

    def get_config_path(self):
        if os.name == 'nt':
            base_path = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            config_dir = os.path.join(base_path, 'PhotoOrganizer')
        else:
            config_dir = os.path.expanduser('~/.config/photoorganizer')
            
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        return os.path.join(config_dir, 'settings.json')

    def load_settings(self):
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    self.entry_src.setText(settings.get('src', ''))
                    self.entry_dest.setText(settings.get('dest', ''))
                    self.entry_exts.setText(settings.get('exts', 'jpg, jpeg, png, arw, cr2, nef, dng, orf, rw2'))
                    self.entry_folder_fmt.setText(settings.get('folder_fmt', '%Y/%m/%d'))
                    self.entry_file_fmt.setText(settings.get('file_fmt', 'IMG_{seq:04d}'))
            except Exception as e:
                print(f"Failed to load settings: {e}")

    def save_settings(self):
        settings = {
            'src': self.entry_src.text(),
            'dest': self.entry_dest.text(),
            'exts': self.entry_exts.text(),
            'folder_fmt': self.entry_folder_fmt.text(),
            'file_fmt': self.entry_file_fmt.text()
        }
        config_path = self.get_config_path()
        try:
            with open(config_path, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhotoOrganizerApp()
    window.show()
    sys.exit(app.exec_())
