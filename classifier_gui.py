import sys
import os
import json
import torch
import numpy as np
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QListWidget, QComboBox,
    QProgressBar, QMessageBox, QSplitter, QGroupBox, QRadioButton,
    QScrollArea, QButtonGroup, QGridLayout, QFrame, QTabWidget,
    QSpinBox, QCheckBox, QSizePolicy, QTextEdit, QLineEdit
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer

# Import our classifier
from classify import ImageClassifier

class FeedbackDatabase:
    """
    Class to manage user feedback data for reinforcement learning
    """
    def __init__(self, data_dir="feedback_data"):
        self.data_dir = data_dir
        self.feedback_file = os.path.join(data_dir, "user_feedback.json")
        self.corrected_images_dir = os.path.join(data_dir, "corrected_images")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.corrected_images_dir, exist_ok=True)
        
        # Load existing feedback if any
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'r') as f:
                self.feedback_data = json.load(f)
        else:
            self.feedback_data = {
                "metadata": {
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_corrections": 0
                },
                "corrections": {}  # image_path -> {original_class, corrected_class, confidence}
            }
            self._save_data()
    
    def add_correction(self, image_path, original_class, corrected_class, confidence):
        """Add a correction to the feedback database"""
        # Get relative path if image is inside project
        rel_path = os.path.relpath(image_path) if os.path.commonpath([image_path, os.getcwd()]) == os.getcwd() else image_path
        
        self.feedback_data["corrections"][rel_path] = {
            "original_class": original_class,
            "corrected_class": corrected_class,
            "confidence": confidence,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.feedback_data["metadata"]["total_corrections"] += 1
        self.feedback_data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save changes
        self._save_data()
        
        # Optionally copy the image to corrected images directory
        try:
            dst_dir = os.path.join(self.corrected_images_dir, corrected_class)
            os.makedirs(dst_dir, exist_ok=True)
            
            # Generate a unique filename
            filename = os.path.basename(image_path)
            base, ext = os.path.splitext(filename)
            dst_path = os.path.join(dst_dir, f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}")
            
            # Copy the file
            shutil.copy2(image_path, dst_path)
        except Exception as e:
            print(f"Error copying file to corrected images directory: {e}")
    
    def _save_data(self):
        """Save feedback data to JSON file"""
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=4)
    
    def export_for_retraining(self, output_path=None):
        """Export the data in a format suitable for retraining"""
        if output_path is None:
            output_path = os.path.join(self.data_dir, f"retraining_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        # Convert to pandas dataframe
        data = []
        for img_path, correction in self.feedback_data["corrections"].items():
            data.append({
                "image_path": img_path,
                "label": correction["corrected_class"],
                "original_prediction": correction["original_class"],
                "confidence": correction["confidence"]
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return output_path
    
    def get_stats(self):
        """Get statistics about corrections"""
        stats = {
            "total_corrections": self.feedback_data["metadata"]["total_corrections"],
            "last_updated": self.feedback_data["metadata"]["last_updated"],
            "class_counts": {}
        }
        
        # Count corrections per class
        for _, correction in self.feedback_data["corrections"].items():
            corrected_class = correction["corrected_class"]
            if corrected_class in stats["class_counts"]:
                stats["class_counts"][corrected_class] += 1
            else:
                stats["class_counts"][corrected_class] = 1
        
        return stats


class ImageClassificationThread(QThread):
    """Thread for running image classification in the background"""
    update_progress = pyqtSignal(int, int)  # current, total
    result_ready = pyqtSignal(object)  # results dictionary
    
    def __init__(self, classifier, image_paths):
        super().__init__()
        self.classifier = classifier
        self.image_paths = image_paths
        
    def run(self):
        results = {}
        total = len(self.image_paths)
        
        for i, image_path in enumerate(self.image_paths):
            try:
                class_name, confidence, original_class = self.classifier.predict_single_image(image_path)
                results[image_path] = (class_name, confidence, original_class)
                self.update_progress.emit(i + 1, total)
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
                results[image_path] = ("Error", 0.0, None)
        
        self.result_ready.emit(results)


class ImageThumbnail(QFrame):
    """Custom widget for displaying an image thumbnail with prediction and feedback controls"""
    correction_made = pyqtSignal(str, str, str, float)  # image_path, original_class, corrected_class, confidence
    
    def __init__(self, image_path, prediction, confidence, original_class=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.prediction = prediction
        self.confidence = confidence
        self.original_class = original_class
        self.corrected_class = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        
        # Load image and create thumbnail
        try:
            pixmap = QPixmap(self.image_path)
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        except Exception as e:
            self.image_label.setText(f"Error loading image: {str(e)}")
        
        # Prediction info
        self.info_label = QLabel(f"{Path(self.image_path).name}\n"
                               f"Prediction: {self.prediction}\n"
                               f"Confidence: {self.confidence:.2f}")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        
        # Original class info (if mapping is used)
        if self.original_class:
            self.original_label = QLabel(f"Original class: {self.original_class}")
            self.original_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.original_label)
        
        # Correction controls
        correction_layout = QVBoxLayout()
        correction_label = QLabel("Correct class:")
        correction_label.setAlignment(Qt.AlignCenter)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(["Truck", "Minitruck", "Car"])
        try:
            self.class_combo.setCurrentText(self.prediction)
        except:
            pass
        
        self.submit_btn = QPushButton("Submit Correction")
        self.submit_btn.clicked.connect(self.submit_correction)
        
        correction_layout.addWidget(correction_label)
        correction_layout.addWidget(self.class_combo)
        correction_layout.addWidget(self.submit_btn)
        
        # Add to main layout
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(self.info_label)
        main_layout.addLayout(correction_layout)
        
        # Style
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 5px;
            }
            QLabel {
                font-size: 10pt;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
    
    def submit_correction(self):
        """Handle submission of a correction"""
        self.corrected_class = self.class_combo.currentText()
        
        if self.corrected_class != self.prediction:
            # Visual feedback for correction
            self.submit_btn.setText("✓ Corrected")
            self.submit_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            self.submit_btn.setEnabled(False)
            
            # Emit signal with correction info
            self.correction_made.emit(
                self.image_path, 
                self.original_class if self.original_class else self.prediction,
                self.corrected_class,
                self.confidence
            )
        else:
            # No change
            self.submit_btn.setText("No Change")
            self.submit_btn.setStyleSheet("background-color: #888888; color: white;")
            self.submit_btn.setEnabled(False)


class ClassifierApp(QMainWindow):
    """Main application window"""
    
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
        
        # Setup UI
        self.setup_ui()
        
        # Initialize classifier
        self.initialize_classifier()
    
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
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.classifier_tab, "Single Image Classification")
        self.tab_widget.addTab(self.batch_tab, "Batch Classification")
        self.tab_widget.addTab(self.stats_tab, "Feedback Statistics")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
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
    
    def initialize_classifier(self):
        """Initialize the image classifier"""
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Paths to model and label encoder
            model_path = os.path.join(base_dir, "pt", "model_weights.pth")
            encoder_path = os.path.join(base_dir, "pt", "label_encoder.pth")
            
            self.classifier = ImageClassifier(model_path, encoder_path, use_mapping=True)
            self.statusBar().showMessage("Classifier initialized successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize classifier: {str(e)}")
            self.statusBar().showMessage("Classifier initialization failed")
    
    def toggle_mapping(self, checked):
        """Toggle class mapping"""
        if self.classifier:
            self.classifier.use_mapping = checked
            
            # If we have a current image, reclassify it
            if self.current_image:
                self.classify_current_image()
    
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
                
            # Set colors based on class
            if self.classifier.use_mapping:
                color = self.classifier.category_colors.get(class_name, '#333333')
                self.prediction_display.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {color};")
            
        except Exception as e:
            self.prediction_display.setText(f"Error: {str(e)}")
            self.submit_btn.setEnabled(False)
    
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


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Interactive Image Classifier with Reinforcement Learning')
    parser.add_argument('--model', type=str, default='pt/model_weights.pth',
                        help='Path to the model weights')
    parser.add_argument('--encoder', type=str, default='pt/label_encoder.pth',
                        help='Path to the label encoder')
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create the main window
    window = ClassifierApp()
    
    # Override model paths if provided
    if hasattr(window, 'classifier') and window.classifier:
        if args.model != 'pt/model_weights.pth' or args.encoder != 'pt/label_encoder.pth':
            try:
                # Re-initialize with the specified model
                window.classifier = ImageClassifier(args.model, args.encoder, use_mapping=True)
                window.statusBar().showMessage(f"Using custom model: {args.model}")
            except Exception as e:
                print(f"Error loading custom model: {e}")
    
    # Show the window
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
