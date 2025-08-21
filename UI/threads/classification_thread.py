from PyQt5.QtCore import QThread, pyqtSignal

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
