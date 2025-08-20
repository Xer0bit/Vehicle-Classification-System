import os
import argparse
from classify import ImageClassifier
import matplotlib.pyplot as plt
import random
import numpy as np

def main():
    """
    Demo script to showcase the image classifier functionality
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Image Classification Demo')
    parser.add_argument('--map', action='store_true', 
                        help='Apply class mapping (Truck, Minitruck, Car)')
    args = parser.parse_args()
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to model and label encoder
    model_path = os.path.join(base_dir, "pt", "model_weights.pth")
    encoder_path = os.path.join(base_dir, "pt", "label_encoder.pth")
    
    # Path to test images directory
    test_dir = os.path.join(base_dir, "dataset", "test")
    
    print("=" * 50)
    print("Image Classification Demo")
    print("=" * 50)
    
    # Initialize the classifier with or without mapping
    classifier = ImageClassifier(model_path, encoder_path, use_mapping=args.map)
    
    # Option 1: Classify a single test image
    print("\n[Option 1] Classifying a single image...")
    # Get a random image from the test directory
    test_images = [os.path.join(test_dir, f) for f in os.listdir(test_dir) if f.endswith('.jpg')]
    if test_images:
        test_image = random.choice(test_images)
        result = classifier.predict_single_image(test_image, show_image=True)
        
        if args.map:
            class_name, confidence, original_class = result
            print(f"Prediction: {class_name} (Original: {original_class}, Confidence: {confidence:.2f})")
        else:
            class_name, confidence, _ = result
            print(f"Prediction: {class_name} (Confidence: {confidence:.2f})")
    
    # Option 2: Classify multiple images (random 10 from test directory)
    print("\n[Option 2] Classifying multiple images...")
    if len(test_images) >= 10:
        sample_images = random.sample(test_images, 10)
    else:
        sample_images = test_images
        
    if sample_images:
        classifier.predict_batch(sample_images, show_results=True, max_display=10)
    
    # Option 3: Compare standard classification vs mapped classification
    if not args.map:
        print("\n[Option 3] Comparing standard vs mapped classification...")
        mapped_classifier = ImageClassifier(model_path, encoder_path, use_mapping=True)
        
        # Select 5 random images for comparison
        compare_images = random.sample(test_images, min(5, len(test_images)))
        
        # Create a figure to show side-by-side comparison
        fig = plt.figure(figsize=(15, 10))
        
        for i, img_path in enumerate(compare_images):
            # Standard classification
            class_name, confidence, _ = classifier.predict_single_image(img_path, show_image=False)
            
            # Mapped classification
            mapped_class, mapped_conf, original_class = mapped_classifier.predict_single_image(img_path, show_image=False)
            
            # Create a 2-column subplot
            plt.subplot(len(compare_images), 2, i*2 + 1)
            img = plt.imread(img_path)
            plt.imshow(img)
            plt.title(f"Standard: {class_name}\nConfidence: {confidence:.2f}", fontsize=12)
            plt.axis('off')
            
            plt.subplot(len(compare_images), 2, i*2 + 2)
            plt.imshow(img)
            
            # Use color based on category
            title_color = mapped_classifier.category_colors.get(mapped_class, 'black')
            plt.title(f"Mapped: {mapped_class}\n(Original: {original_class})\nConfidence: {mapped_conf:.2f}", 
                     fontsize=12, color=title_color, fontweight='bold')
            
            # Add a colored border to the mapped image
            for spine in plt.gca().spines.values():
                spine.set_color(title_color)
                spine.set_linewidth(3)
                
            plt.axis('off')
        
        plt.tight_layout(pad=2.0)
        plt.subplots_adjust(wspace=0.1, hspace=0.3)
        plt.show()
    
    print("\n" + "=" * 50)
    print("Demo completed! To classify your own images, use:")
    print("python classify.py --image path/to/image.jpg --show")
    print("python classify.py --dir path/to/images/folder --show")
    print("python classify.py --image path/to/image.jpg --show --map  # Use class mapping")
    print("=" * 50)

if __name__ == "__main__":
    main()
