import sys
import os
import argparse
from UI import ClassifierApp
from PyQt5.QtWidgets import QApplication
from classify import ImageClassifier

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
        