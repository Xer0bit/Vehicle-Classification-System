import os
import json
import pandas as pd
from datetime import datetime
import shutil
from pathlib import Path

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
