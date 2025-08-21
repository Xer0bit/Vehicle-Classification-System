from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path

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
