from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QListWidget, QComboBox,
    QProgressBar, QMessageBox, QSplitter, QGroupBox, QRadioButton,
    QScrollArea, QButtonGroup, QGridLayout, QFrame, QTabWidget,
    QSpinBox, QCheckBox, QSizePolicy, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
import os
import sys
from pathlib import Path
import subprocess
import time
import hmac
import hashlib
import requests
from datetime import datetime
from classify import ImageClassifier
from .utils.feedback_database import FeedbackDatabase
from .utils.env_manager import EnvManager
from .widgets.image_thumbnail import ImageThumbnail
from .threads.classification_thread import ImageClassificationThread

class ClassifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Image Classifier with Reinforcement Learning")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize data
        self.classifier = None
        self.current_image = None
        self.image_paths = []
        self.current_results = {}
        self.feedback_db = FeedbackDatabase()
        
        # Initialize environment manager
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.env_manager = EnvManager(base_dir)
        
        # API Server state
        self.api_server_process = None
        self.api_server_running = False
        self.api_monitoring_timer = QTimer()
        self.api_monitoring_timer.timeout.connect(self.update_api_stats)
        self.api_monitoring_timer.start(5000)  # Update every 5 seconds
        
        # Setup UI
        self.setup_ui()
        
        # Initialize classifier
        self.initialize_classifier()
    
    def initialize_classifier(self):
        """Initialize the image classifier"""
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Paths to model and label encoder
            model_path = os.path.join(base_dir, "pt", "model_weights.pth")
            encoder_path = os.path.join(base_dir, "pt", "label_encoder.pth")
            
            self.classifier = ImageClassifier(model_path, encoder_path, use_mapping=True)
            self.statusBar().showMessage("Classifier initialized successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize classifier: {str(e)}")
            self.statusBar().showMessage("Classifier initialization failed")

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_classifier_tab()
        self.create_batch_tab()
        self.create_stats_tab()
        self.create_api_tab()
        
        # Create API Documentation tab
        self.create_api_docs_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.classifier_tab, "Single Image Classification")
        self.tab_widget.addTab(self.batch_tab, "Batch Classification")
        self.tab_widget.addTab(self.stats_tab, "Feedback Statistics")
        self.tab_widget.addTab(self.api_tab, "API Management")
        self.tab_widget.addTab(self.api_docs_tab, "API Documentation")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready")

    def update_api_stats(self):
        """Update API statistics display"""
        if not hasattr(self, 'api_stats_text') or not hasattr(self, 'api_server_running'):
            return
            
        if not self.api_server_running:
            self.api_stats_text.setText("API server is not running")
            return
            
        try:
            # Check if required inputs exist
            if not hasattr(self, 'port_input') or not hasattr(self, 'ssl_checkbox'):
                return
                
            # First try health check (no auth required)
            port = self.port_input.value()
            use_ssl = self.ssl_checkbox.isChecked()
            base_url = f"http{'s' if use_ssl else ''}://localhost:{port}"
            
            try:
                health_response = requests.get(f"{base_url}/api/health", verify=False, timeout=5)
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    
                    # Try to get detailed stats if we have credentials
                    stats_text = f"""API Server Status
=================

Status: {health_data.get('status', 'unknown')}
Classifier Loaded: {health_data.get('classifier_loaded', 'unknown')}
Last Health Check: {health_data.get('timestamp', 'unknown')}

"""
                    
                    # Try to get detailed stats with authentication
                    if hasattr(self, 'api_key_input') and hasattr(self, 'api_secret_input'):
                        api_key = self.api_key_input.text()
                        api_secret = self.api_secret_input.text()
                        
                        if api_key and api_secret:
                            try:
                                # Generate authentication headers
                                timestamp = datetime.utcnow().isoformat()
                                message = f"GET\\n/api/stats\\n{timestamp}\\n"
                                signature = hmac.new(
                                    api_secret.encode(),
                                    message.encode(),
                                    hashlib.sha256
                                ).hexdigest()
                                
                                headers = {
                                    'X-API-Key': api_key,
                                    'X-API-Signature': signature,
                                    'X-API-Timestamp': timestamp
                                }
                                
                                stats_response = requests.get(
                                    f"{base_url}/api/stats", 
                                    headers=headers, 
                                    verify=False, 
                                    timeout=5
                                )
                                
                                if stats_response.status_code == 200:
                                    stats_data = stats_response.json()
                                    stats_text += f"""Detailed Statistics
==================

Uptime: {stats_data.get('uptime_human', 'unknown')}
Total Requests: {stats_data.get('requests_total', 0)}
Successful Requests: {stats_data.get('requests_successful', 0)}
Failed Requests: {stats_data.get('requests_failed', 0)}
Success Rate: {stats_data.get('success_rate', 0):.1f}%
"""
                                else:
                                    stats_text += f"Detailed stats unavailable (Status: {stats_response.status_code})"
                                    
                            except Exception as auth_error:
                                stats_text += f"Authentication failed: {str(auth_error)}"
                        else:
                            stats_text += "Set API credentials to view detailed statistics"
                    
                    self.api_stats_text.setText(stats_text)
                else:
                    self.api_stats_text.setText(f"API server responded with status: {health_response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                self.api_stats_text.setText("Cannot connect to API server")
            except requests.exceptions.Timeout:
                self.api_stats_text.setText("API server timeout")
                
        except Exception as e:
            self.api_stats_text.setText(f"Error checking API status: {str(e)}")

    def create_api_tab(self):
        """Create the tab for API management"""
        self.api_tab = QWidget()
        layout = QVBoxLayout(self.api_tab)
        
        # Server Control Group
        server_group = QGroupBox("API Server Control")
        server_layout = QHBoxLayout(server_group)
        
        self.start_api_btn = QPushButton("Start API Server")
        self.start_api_btn.clicked.connect(self.toggle_api_server)
        
        self.server_status_label = QLabel("Status: Stopped")
        self.server_status_label.setStyleSheet("color: red;")
        
        server_layout.addWidget(self.start_api_btn)
        server_layout.addWidget(self.server_status_label)
        server_layout.addStretch()
        
        # API Credentials Group
        credentials_group = QGroupBox("API Credentials")
        credentials_layout = QGridLayout(credentials_group)
        
        # API Key
        credentials_layout.addWidget(QLabel("API Key:"), 0, 0)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter API Key")
        self.api_key_input.setText(self.env_manager.get_api_key() or "")
        credentials_layout.addWidget(self.api_key_input, 0, 1)
        
        # API Secret
        credentials_layout.addWidget(QLabel("API Secret:"), 1, 0)
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("Enter API Secret")
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        self.api_secret_input.setText(self.env_manager.get_api_secret() or "")
        credentials_layout.addWidget(self.api_secret_input, 1, 1)
        
        # Show/Hide Secret Button
        self.show_secret_btn = QPushButton("Show")
        self.show_secret_btn.setCheckable(True)
        self.show_secret_btn.toggled.connect(self.toggle_secret_visibility)
        credentials_layout.addWidget(self.show_secret_btn, 1, 2)
        
        # Save Credentials Button
        save_credentials_btn = QPushButton("Save Credentials")
        save_credentials_btn.clicked.connect(self.save_credentials)
        credentials_layout.addWidget(save_credentials_btn, 2, 0, 1, 3)
        
        # API Settings Group
        settings_group = QGroupBox("API Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Port setting
        settings_layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(5000)
        settings_layout.addWidget(self.port_input, 0, 1)
        
        # SSL/TLS Toggle
        self.ssl_checkbox = QCheckBox("Enable SSL/TLS")
        self.ssl_checkbox.setChecked(True)
        settings_layout.addWidget(self.ssl_checkbox, 1, 0, 1, 2)
        
        # CORS settings
        self.cors_checkbox = QCheckBox("Enable CORS")
        settings_layout.addWidget(self.cors_checkbox, 2, 0, 1, 2)
        
        settings_layout.addWidget(QLabel("Allowed Origins:"), 3, 0)
        self.cors_origins = QLineEdit("*")
        settings_layout.addWidget(self.cors_origins, 3, 1)
        
        # Rate Limiting
        settings_layout.addWidget(QLabel("Rate Limit (req/min):"), 4, 0)
        self.rate_limit = QSpinBox()
        self.rate_limit.setRange(0, 1000)
        self.rate_limit.setValue(60)
        settings_layout.addWidget(self.rate_limit, 4, 1)
        
        # Apply Settings Button
        self.apply_settings_btn = QPushButton("Apply Settings")
        self.apply_settings_btn.clicked.connect(self.apply_api_settings)
        settings_layout.addWidget(self.apply_settings_btn, 5, 0, 1, 2)
        
        # API Statistics Group
        stats_group = QGroupBox("API Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.api_stats_text = QTextEdit()
        self.api_stats_text.setReadOnly(True)
        stats_layout.addWidget(self.api_stats_text)
        
        # Add all groups to main layout
        layout.addWidget(server_group)
        layout.addWidget(credentials_group)
        layout.addWidget(settings_group)
        layout.addWidget(stats_group)

    def toggle_api_server(self):
        """Start or stop the API server"""
        if not self.api_server_running:
            try:
                # Prepare command with current settings
                port = self.port_input.value()
                
                # Start server process (simplified - only port and debug supported)
                cmd = f"python web_server.py --port {port}"
                self.api_server_process = subprocess.Popen(cmd.split())
                
                self.api_server_running = True
                self.server_status_label.setText("Status: Running")
                self.server_status_label.setStyleSheet("color: green;")
                self.start_api_btn.setText("Stop API Server")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start API server: {str(e)}")
                
        else:
            try:
                if self.api_server_process:
                    self.api_server_process.terminate()
                    self.api_server_process = None
                
                self.api_server_running = False
                self.server_status_label.setText("Status: Stopped")
                self.server_status_label.setStyleSheet("color: red;")
                self.start_api_btn.setText("Start API Server")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to stop API server: {str(e)}")

    def apply_api_settings(self):
        """Apply new API settings"""
        if self.api_server_running:
            reply = QMessageBox.question(
                self,
                "Restart Required",
                "Changing settings requires restarting the API server. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.toggle_api_server()  # Stop
                self.toggle_api_server()  # Start with new settings
    
    def toggle_secret_visibility(self, checked):
        """Toggle the visibility of the API secret key"""
        if checked:
            self.api_secret_input.setEchoMode(QLineEdit.Normal)
            self.show_secret_btn.setText("Hide")
        else:
            self.api_secret_input.setEchoMode(QLineEdit.Password)
            self.show_secret_btn.setText("Show")
            
    def save_credentials(self):
        """Save API credentials to .env file"""
        try:
            self.env_manager.save_credentials(
                self.api_key_input.text(),
                self.api_secret_input.text()
            )
            self.statusBar().showMessage("API credentials saved successfully", 3000)
            
            # Update documentation examples
            self.update_api_examples()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save credentials: {str(e)}"
            )
                
    def create_classifier_tab(self):
        """Create the tab for single image classification"""
        self.classifier_tab = QWidget()
        layout = QVBoxLayout(self.classifier_tab)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Left side - Load image button
        load_btn = QPushButton("Load Image")
        load_btn.clicked.connect(self.load_single_image)
        
        # Center - Class selection
        class_group = QGroupBox("Correct Class")
        class_layout = QVBoxLayout(class_group)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(["Truck", "Minitruck", "Car"])
        
        self.submit_btn = QPushButton("Submit Correction")
        self.submit_btn.clicked.connect(self.submit_single_correction)
        self.submit_btn.setEnabled(False)
        
        class_layout.addWidget(self.class_combo)
        class_layout.addWidget(self.submit_btn)
        
        # Right side - Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.use_mapping_cb = QCheckBox("Use Class Mapping")
        self.use_mapping_cb.setChecked(True)
        self.use_mapping_cb.toggled.connect(self.toggle_mapping)
        
        options_layout.addWidget(self.use_mapping_cb)
        
        # Add to controls layout
        controls_layout.addWidget(load_btn)
        controls_layout.addWidget(class_group)
        controls_layout.addWidget(options_group)
        
        # Image display area
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setMinimumSize(400, 400)
        self.image_display.setStyleSheet("border: 2px solid #cccccc; background-color: #f0f0f0;")
        self.image_display.setText("Load an image to classify")
        
        # Prediction display
        self.prediction_display = QLabel()
        self.prediction_display.setAlignment(Qt.AlignCenter)
        self.prediction_display.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333333;")
        self.prediction_display.setText("No prediction yet")
        
        # Add to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.image_display)
        layout.addWidget(self.prediction_display)
        
    def create_batch_tab(self):
        """Create the tab for batch image classification"""
        self.batch_tab = QWidget()
        layout = QVBoxLayout(self.batch_tab)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        load_folder_btn = QPushButton("Load Image Folder")
        load_folder_btn.clicked.connect(self.load_image_folder)
        
        self.export_btn = QPushButton("Export Corrections")
        self.export_btn.clicked.connect(self.export_corrections)
        self.export_btn.setEnabled(False)
        
        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 100)
        self.batch_progress.setValue(0)
        
        controls_layout.addWidget(load_folder_btn)
        controls_layout.addWidget(self.export_btn)
        
        # Results area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        
        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        
        self.results_scroll.setWidget(self.results_container)
        
        # Add to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.batch_progress)
        layout.addWidget(self.results_scroll)
        
    def create_stats_tab(self):
        """Create the tab for feedback statistics"""
        self.stats_tab = QWidget()
        layout = QVBoxLayout(self.stats_tab)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_stats)
        
        prepare_retrain_btn = QPushButton("Prepare for Retraining")
        prepare_retrain_btn.clicked.connect(self.prepare_for_retraining)
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(prepare_retrain_btn)
        
        # Stats display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        
        # Add to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.stats_text)
        
        # Initial refresh
        self.refresh_stats()
        
    def load_single_image(self):
        """Load a single image for classification"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        
        if file_path:
            self.current_image = file_path
            
            # Display the image
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.image_display.width(), self.image_display.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_display.setPixmap(scaled_pixmap)
            
            # Classify the image
            self.classify_current_image()
            
    def classify_current_image(self):
        """Classify the current image"""
        if not self.current_image or not self.classifier:
            return
        
        try:
            class_name, confidence, original_class = self.classifier.predict_single_image(self.current_image)
            
            # Update display
            if self.classifier.use_mapping and original_class:
                display_text = f"Prediction: {class_name} (Original: {original_class})\nConfidence: {confidence:.2f}"
            else:
                display_text = f"Prediction: {class_name}\nConfidence: {confidence:.2f}"
                
            self.prediction_display.setText(display_text)
            self.submit_btn.setEnabled(True)
            
            # Select the predicted class in the combo box
            index = self.class_combo.findText(class_name)
            if index >= 0:
                self.class_combo.setCurrentIndex(index)
            
        except Exception as e:
            self.prediction_display.setText(f"Error: {str(e)}")
            self.submit_btn.setEnabled(False)
            
    def toggle_mapping(self, checked):
        """Toggle class mapping"""
        if self.classifier:
            self.classifier.use_mapping = checked
            
            # If we have a current image, reclassify it
            if self.current_image:
                self.classify_current_image()
                
    def submit_single_correction(self):
        """Submit a correction for the current image"""
        if not self.current_image:
            return
            
        corrected_class = self.class_combo.currentText()
        
        # Get original prediction
        if self.classifier.use_mapping:
            _, _, original_class = self.classifier.predict_single_image(self.current_image)
            if original_class is None:
                original_class = "Unknown"
        else:
            original_class, confidence, _ = self.classifier.predict_single_image(self.current_image)
        
        # Get confidence
        _, confidence, _ = self.classifier.predict_single_image(self.current_image)
        
        # Check if this is actually a correction
        predicted_class = self.classifier.predict_single_image(self.current_image)[0]
        
        if corrected_class != predicted_class:
            # Add to feedback database
            self.feedback_db.add_correction(
                self.current_image, 
                original_class, 
                corrected_class, 
                confidence
            )
            
            QMessageBox.information(
                self, 
                "Correction Submitted", 
                f"Correction saved: {Path(self.current_image).name}\n"
                f"Original: {predicted_class} -> Corrected: {corrected_class}"
            )
        else:
            QMessageBox.information(
                self,
                "No Correction",
                f"No correction made (prediction already {corrected_class})"
            )
            
    def load_image_folder(self):
        """Load a folder of images for batch classification"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        
        if folder_path:
            # Find all images in the folder
            extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff']
            image_paths = []
            
            for ext in extensions:
                image_paths.extend(list(Path(folder_path).glob(ext)))
                image_paths.extend(list(Path(folder_path).glob(ext.upper())))
            
            self.image_paths = [str(p) for p in image_paths]
            
            if not self.image_paths:
                QMessageBox.warning(self, "No Images", "No image files found in the selected folder.")
                return
                
            # Clear previous results
            self.clear_batch_results()
            
            # Start classification in background
            self.statusBar().showMessage(f"Processing {len(self.image_paths)} images...")
            self.batch_progress.setValue(0)
            
            self.classification_thread = ImageClassificationThread(self.classifier, self.image_paths)
            self.classification_thread.update_progress.connect(self.update_batch_progress)
            self.classification_thread.result_ready.connect(self.display_batch_results)
            self.classification_thread.start()
            
    def clear_batch_results(self):
        """Clear the batch results area"""
        # Clear the layout
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
    def update_batch_progress(self, current, total):
        """Update the batch progress bar"""
        percentage = int(current / total * 100)
        self.batch_progress.setValue(percentage)
        self.statusBar().showMessage(f"Processing image {current} of {total}...")
        
    def display_batch_results(self, results):
        """Display the batch classification results"""
        self.current_results = results
        self.statusBar().showMessage(f"Classified {len(results)} images")
        
        # Clear the results area
        self.clear_batch_results()
        
        # Populate with results
        row, col = 0, 0
        max_cols = 3  # Number of thumbnails per row
        
        for image_path, (class_name, confidence, original_class) in results.items():
            # Create thumbnail widget
            thumbnail = ImageThumbnail(image_path, class_name, confidence, original_class)
            thumbnail.correction_made.connect(self.handle_batch_correction)
            
            self.results_layout.addWidget(thumbnail, row, col)
            
            # Update position for next thumbnail
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Enable the export button
        self.export_btn.setEnabled(True)
        
    def handle_batch_correction(self, image_path, original_class, corrected_class, confidence):
        """Handle a correction from the batch view"""
        self.feedback_db.add_correction(image_path, original_class, corrected_class, confidence)
        
        # Update the status bar
        self.statusBar().showMessage(f"Correction saved for {Path(image_path).name}", 3000)
        
        # Refresh stats if the stats tab is active
        if self.tab_widget.currentIndex() == 2:
            self.refresh_stats()
            
    def export_corrections(self):
        """Export the feedback data for retraining"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Retraining Data", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Add .csv extension if not present
                if not file_path.lower().endswith('.csv'):
                    file_path += '.csv'
                    
                output_path = self.feedback_db.export_for_retraining(file_path)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Retraining data exported to {output_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export retraining data: {str(e)}"
                )
                
    def create_api_docs_tab(self):
        """Create the tab for API documentation"""
        self.api_docs_tab = QWidget()
        layout = QVBoxLayout(self.api_docs_tab)
        
        # Create documentation browser
        docs_text = QTextEdit()
        docs_text.setReadOnly(True)
        
        # Example box
        example_group = QGroupBox("Live Example")
        example_layout = QVBoxLayout(example_group)
        
        # API Key display
        key_layout = QHBoxLayout()
        self.example_key_label = QLabel("API Key: None")
        copy_key_btn = QPushButton("Copy Key")
        copy_key_btn.clicked.connect(lambda: self.copy_to_clipboard(self.get_current_api_key()))
        key_layout.addWidget(self.example_key_label)
        key_layout.addWidget(copy_key_btn)
        example_layout.addLayout(key_layout)
        
        # Curl command display
        curl_label = QLabel("cURL Command:")
        self.curl_text = QTextEdit()
        self.curl_text.setReadOnly(True)
        self.curl_text.setMaximumHeight(100)
        copy_curl_btn = QPushButton("Copy cURL Command")
        copy_curl_btn.clicked.connect(lambda: self.copy_to_clipboard(self.curl_text.toPlainText()))
        
        example_layout.addWidget(curl_label)
        example_layout.addWidget(self.curl_text)
        example_layout.addWidget(copy_curl_btn)
        
        # Python example display
        python_label = QLabel("Python Example:")
        self.python_text = QTextEdit()
        self.python_text.setReadOnly(True)
        self.python_text.setMaximumHeight(200)
        copy_python_btn = QPushButton("Copy Python Code")
        copy_python_btn.clicked.connect(lambda: self.copy_to_clipboard(self.python_text.toPlainText()))
        
        example_layout.addWidget(python_label)
        example_layout.addWidget(self.python_text)
        example_layout.addWidget(copy_python_btn)
        
        # Documentation content
        docs_content = """# Image Classification API Documentation

## Authentication

The API uses a combination of API key and HMAC signature for security. Each request must include:

1. `X-API-Key`: Your API key
2. `X-API-Signature`: HMAC signature of the request
3. `X-API-Timestamp`: Current Unix timestamp

## Endpoints

### 1. Image Classification

**Endpoint:** `/api/classify`
**Method:** POST
**Content-Type:** multipart/form-data

**Parameters:**
- `image`: Image file to classify

**Response:**
```json
{
    "class_name": "Car",
    "confidence": 0.95,
    "original_class": "Vehicle",
    "timestamp": "2025-08-21T10:30:00"
}
```

### 2. Health Check

**Endpoint:** `/api/health`
**Method:** GET

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-08-21T10:30:00"
}
```

## Error Responses

The API returns appropriate HTTP status codes and error messages:

```json
{
    "error": "Error message here"
}
```

Common status codes:
- 400: Bad Request
- 401: Unauthorized
- 500: Internal Server Error

## Security Notes

1. Keep your API key secure
2. Use HTTPS for all API calls
3. Signatures expire after 5 minutes
4. Monitor API usage patterns
"""
        
        docs_text.setMarkdown(docs_content)
        
        # Add everything to main layout
        layout.addWidget(docs_text)
        layout.addWidget(example_group)
        
        # Update examples when API settings change
        self.update_api_examples()
        
    def get_current_api_key(self):
        """Get the current API key without the label prefix"""
        if hasattr(self, 'current_key_label'):
            return self.current_key_label.text().replace("Current API Key: ", "")
        return "None"

    def copy_to_clipboard(self, text):
        """Copy text to clipboard with visual feedback"""
        if text and text != "None":
            cb = QApplication.clipboard()
            cb.setText(text)
            
            # Show temporary message in status bar
            self.statusBar().showMessage("Copied to clipboard!", 2000)
            
    def update_api_examples(self):
        """Update the API usage examples with current settings"""
        try:
            # Get current credentials
            api_key = self.api_key_input.text() if hasattr(self, 'api_key_input') else "your_api_key"
            self.example_key_label.setText(f"API Key: {api_key}")
            
            # Get current server settings
            port = self.port_input.value() if hasattr(self, 'port_input') else 5000
            use_ssl = self.ssl_checkbox.isChecked() if hasattr(self, 'ssl_checkbox') else True
            
            # Base URL
            base_url = f"http{'s' if use_ssl else ''}://localhost:{port}"
            
            # Update curl command with proper authentication
            curl_cmd = f"""#!/bin/bash

# Your API credentials
API_KEY="{api_key}"
API_SECRET="{self.api_secret_input.text() if hasattr(self, 'api_secret_input') else 'your_api_secret'}"
IMAGE_PATH="/path/to/your/image.jpg"
API_URL="{base_url}/api/classify"

# Get current timestamp
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Generate signature (method + path + timestamp)
SIGNATURE=$(echo -n "POST\\n/api/classify\\n$TIMESTAMP\\n" | \\
  openssl dgst -sha256 -hmac "$API_SECRET" -binary | \\
  xxd -p -c 256)

# Send request
curl -X POST "$API_URL" \\
  -H "X-API-Key: $API_KEY" \\
  -H "X-API-Signature: $SIGNATURE" \\
  -H "X-API-Timestamp: $TIMESTAMP" \\
  -F "image=@$IMAGE_PATH" \\
  -k  # Remove in production"""
            
            self.curl_text.setPlainText(curl_cmd)
            
            # Update Python example
            python_code = f"""import requests
import hmac
import hashlib
from datetime import datetime

def classify_image(image_path, api_key, api_secret, base_url="{base_url}"):
    \"\"\"
    Classify an image using the API with HMAC authentication.
    
    Args:
        image_path (str): Path to the image file
        api_key (str): Your API key
        api_secret (str): Your API secret
        base_url (str): Base URL of the API
        
    Returns:
        dict: Classification results
    \"\"\"
    # Prepare timestamp in ISO format
    timestamp = datetime.utcnow().isoformat()
    
    # Create message for signature (method + path + timestamp)
    message = f"POST\\n/api/classify\\n{{timestamp}}\\n"
    
    # Generate HMAC signature
    signature = hmac.new(
        api_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Prepare headers
    headers = {{
        'X-API-Key': api_key,
        'X-API-Signature': signature,
        'X-API-Timestamp': timestamp
    }}
    
    # Send request
    with open(image_path, 'rb') as f:
        response = requests.post(
            f'{{base_url}}/api/classify',
            headers=headers,
            files={{'image': f}},
            verify=False  # Remove in production
        )
        
    return response.json()

# Example usage
api_key = '{api_key}'
api_secret = 'your_api_secret'  # Never hardcode this in production
image_path = 'path/to/image.jpg'

try:
    result = classify_image(image_path, api_key, api_secret)
    print('Classification result:', result)
except Exception as e:
    print('Error:', str(e))"""
            
            self.python_text.setPlainText(python_code)
            
        except Exception as e:
            print(f"Error updating API examples: {e}")
    
    def refresh_stats(self):
        """Refresh the feedback statistics display"""
        stats = self.feedback_db.get_stats()
        
        # Format stats as text
        stats_text = (
            f"Feedback Statistics\n"
            f"=================\n\n"
            f"Total corrections: {stats['total_corrections']}\n"
            f"Last updated: {stats['last_updated']}\n\n"
            f"Corrections by class:\n"
        )
        
        for class_name, count in stats['class_counts'].items():
            stats_text += f"  - {class_name}: {count}\n"
        
        self.stats_text.setText(stats_text)
        
    def prepare_for_retraining(self):
        """Prepare the corrected data for retraining"""
        # Check if we have any corrections
        stats = self.feedback_db.get_stats()
        if stats['total_corrections'] == 0:
            QMessageBox.warning(
                self,
                "No Corrections",
                "No corrections available for retraining. Please provide some feedback first."
            )
            return
        
        # Export the data
        try:
            output_path = self.feedback_db.export_for_retraining()
            
            QMessageBox.information(
                self,
                "Retraining Data Prepared",
                f"Retraining data prepared and exported to {output_path}.\n\n"
                f"You can now use this file to retrain your model."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to prepare retraining data: {str(e)}"
            )

    # Import the rest of the methods from the original classifier_gui.py
    # All the methods from create_classifier_tab(), create_batch_tab(), 
    # create_stats_tab(), create_api_tab(), etc.
