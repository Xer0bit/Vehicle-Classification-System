import os
import argparse
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
import matplotlib.pyplot as plt
from PIL import Image
import glob
from pathlib import Path


class ImageClassifier:
    def __init__(self, model_path, label_encoder_path, use_mapping=False):
        """
        Initialize the image classifier with the trained model and label encoder
        
        Args:
            model_path: Path to the saved model weights
            label_encoder_path: Path to the saved label encoder
            use_mapping: Whether to apply class mapping to simplify categories
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load label encoder
        self.label_encoder = torch.load(label_encoder_path)
        self.num_classes = len(self.label_encoder.classes_)
        self.classes = self.label_encoder.classes_
        print(f"Loaded label encoder with {self.num_classes} classes: {self.classes}")
        
        # Initialize model architecture
        self.model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        num_ftrs = self.model.fc.in_features
        self.model.fc = torch.nn.Linear(num_ftrs, self.num_classes)
        
        # Load trained weights
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model = self.model.to(self.device)
        self.model.eval()
        print("Model loaded successfully")
        
        # Define image transforms
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Set up class mapping
        self.use_mapping = use_mapping
        self.class_map = {
            'heavy truck': 'Truck',
            'bus': 'Minitruck',
            'truck': 'Minitruck',
            'fire engine': 'Minitruck',
            'mini truck': 'Minitruck',
            'minitruck': 'Minitruck'
        }
        # All other classes will map to 'Car'
        
        # Create color mapping for visualization
        self.category_colors = {
            'Truck': '#FF5733',     # Orange-red
            'Minitruck': '#33A1FF', # Light blue
            'Car': '#33FF57'        # Light green
        }
        
        if self.use_mapping:
            print("Using class mapping: Heavy truck/Bus -> Truck, Fire engine/Minitruck -> Minitruck, Other -> Car")
    
    def map_class(self, original_class):
        """
        Map original class to simplified category
        
        Args:
            original_class: Original class name from model prediction
            
        Returns:
            mapped_class: Mapped class name (Truck, Minitruck, or Car)
        """
        if not self.use_mapping:
            return original_class
            
        # Convert to lowercase for case-insensitive matching
        original_lower = original_class.lower()
        
        # Check for exact matches in our mapping dictionary
        for key, value in self.class_map.items():
            if key in original_lower:
                return value
                
        # If no match found, default to 'Car'
        return 'Car'
    
    def predict_single_image(self, image_path, show_image=False):
        """
        Classify a single image
        
        Args:
            image_path: Path to the image file
            show_image: Whether to display the image with its prediction
            
        Returns:
            class_name: Predicted class name
            confidence: Confidence score (probability)
            original_class: Original class name before mapping (if mapping is used)
        """
        try:
            # Load and preprocess the image
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image)
            input_batch = input_tensor.unsqueeze(0).to(self.device)
            
            # Make prediction
            with torch.no_grad():
                output = self.model(input_batch)
                
            # Get probabilities
            probabilities = torch.nn.functional.softmax(output, dim=1)[0]
            confidence, class_idx = torch.max(probabilities, 0)
            
            # Convert index to class name
            original_class = self.label_encoder.inverse_transform([class_idx.item()])[0]
            
            # Apply class mapping if enabled
            mapped_class = self.map_class(original_class)
            
            # Display image with prediction if requested
            if show_image:
                plt.figure(figsize=(8, 8))
                plt.imshow(np.array(image))
                
                # Create a more informative title
                title_text = f"Prediction: {mapped_class}"
                if self.use_mapping:
                    title_text += f" (Original: {original_class})"
                title_text += f"\nConfidence: {confidence:.2f}"
                
                # Use color based on category
                if self.use_mapping:
                    title_color = self.category_colors.get(mapped_class, 'black')
                    plt.title(title_text, fontsize=14, color=title_color, fontweight='bold')
                    
                    # Add a colored border based on the category
                    plt.gca().spines['bottom'].set_color(title_color)
                    plt.gca().spines['top'].set_color(title_color)
                    plt.gca().spines['left'].set_color(title_color)
                    plt.gca().spines['right'].set_color(title_color)
                    plt.gca().spines['bottom'].set_linewidth(5)
                    plt.gca().spines['top'].set_linewidth(5)
                    plt.gca().spines['left'].set_linewidth(5)
                    plt.gca().spines['right'].set_linewidth(5)
                else:
                    plt.title(title_text, fontsize=14)
                    
                plt.axis('off')
                plt.tight_layout()
                plt.show()
            
            result = mapped_class if self.use_mapping else original_class
            return result, confidence.item(), original_class if self.use_mapping else None
            
        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            return None, 0.0, None
    
    def predict_batch(self, image_paths, show_results=False, max_display=25):
        """
        Classify multiple images
        
        Args:
            image_paths: List of paths to image files
            show_results: Whether to display the images with their predictions
            max_display: Maximum number of images to display
            
        Returns:
            results: Dictionary mapping image paths to (class_name, confidence, original_class) tuples
        """
        results = {}
        
        for image_path in image_paths:
            class_name, confidence, original_class = self.predict_single_image(image_path, show_image=False)
            results[image_path] = (class_name, confidence, original_class)
            
            # Format the output message based on whether mapping is used
            if self.use_mapping and original_class:
                print(f"{Path(image_path).name}: {class_name} (Original: {original_class}, Confidence: {confidence:.2f})")
            else:
                print(f"{Path(image_path).name}: {class_name} (Confidence: {confidence:.2f})")
        
        # Display results if requested
        if show_results and results:
            num_to_display = min(len(results), max_display)
            
            # Calculate optimal grid size - fewer columns for better visibility
            cols = min(5, int(np.ceil(np.sqrt(num_to_display*1.5))))
            rows = int(np.ceil(num_to_display / cols))
            
            # Create a larger figure with enough space for titles
            plt.figure(figsize=(cols * 4, rows * 4))
            
            # Group the images by class for better visualization
            if self.use_mapping:
                # Get the unique mapped classes from the results
                class_counts = {}
                for image_path, (class_name, _, _) in results.items():
                    if class_name not in class_counts:
                        class_counts[class_name] = 0
                    class_counts[class_name] += 1
                print(f"\nClass distribution: {class_counts}")
            
            # Plot each image with enhanced styling
            for i, (image_path, (class_name, confidence, original_class)) in enumerate(list(results.items())[:num_to_display]):
                ax = plt.subplot(rows, cols, i + 1)
                img = Image.open(image_path).convert('RGB')
                plt.imshow(np.array(img))
                
                # Create an informative title
                if self.use_mapping and original_class:
                    title = f"{class_name}\n"
                    subtitle = f"({original_class})\n{confidence:.2f}"
                    
                    # Use colored titles and borders based on mapped category
                    title_color = self.category_colors.get(class_name, 'black')
                    
                    # Add colored border to the plot
                    for spine in ax.spines.values():
                        spine.set_color(title_color)
                        spine.set_linewidth(3)
                    
                    # Two-part title with different styling
                    plt.title(title, fontsize=12, fontweight='bold', color=title_color)
                    plt.xlabel(subtitle, fontsize=10)
                else:
                    plt.title(f"{class_name}\n{confidence:.2f}", fontsize=10)
                
                plt.axis('off')
            
            plt.tight_layout(pad=2.0)
            plt.subplots_adjust(wspace=0.3, hspace=0.3)
            plt.show()
        
        return results
    
    def process_directory(self, directory_path, show_results=False, max_display=25):
        """
        Process all images in a directory
        
        Args:
            directory_path: Path to directory containing images
            show_results: Whether to display the images with predictions
            max_display: Maximum number of images to display
            
        Returns:
            results: Dictionary mapping image paths to (class_name, confidence) tuples
        """
        # Find all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
        image_paths = []
        
        for ext in image_extensions:
            image_paths.extend(glob.glob(os.path.join(directory_path, f"*{ext}")))
            image_paths.extend(glob.glob(os.path.join(directory_path, f"*{ext.upper()}")))
        
        if not image_paths:
            print(f"No images found in {directory_path}")
            return {}
        
        print(f"Found {len(image_paths)} images in {directory_path}")
        return self.predict_batch(image_paths, show_results, max_display)


def main():
    parser = argparse.ArgumentParser(description='Image Classification Tool')
    parser.add_argument('--image', type=str, help='Path to a single image to classify')
    parser.add_argument('--dir', type=str, help='Path to directory containing images to classify')
    parser.add_argument('--model', type=str, default='pt/model_weights.pth', 
                        help='Path to model weights')
    parser.add_argument('--encoder', type=str, default='pt/label_encoder.pth', 
                        help='Path to label encoder')
    parser.add_argument('--show', action='store_true', help='Display images with predictions')
    parser.add_argument('--max_display', type=int, default=25, 
                        help='Maximum number of images to display')
    parser.add_argument('--map', action='store_true', 
                        help='Apply class mapping (Truck, Minitruck, Car)')
    
    args = parser.parse_args()
    
    # Validate paths
    model_path = args.model
    encoder_path = args.encoder
    
    # Initialize classifier with mapping if requested
    classifier = ImageClassifier(model_path, encoder_path, use_mapping=args.map)
    
    # Process according to input type
    if args.image:
        if os.path.isfile(args.image):
            class_name, confidence, original_class = classifier.predict_single_image(
                args.image, show_image=args.show)
            
            # Print the result
            if args.map and original_class:
                print(f"Prediction: {class_name} (Original: {original_class}, Confidence: {confidence:.2f})")
            else:
                print(f"Prediction: {class_name} (Confidence: {confidence:.2f})")
                
        else:
            print(f"Error: Image file {args.image} not found")
    
    elif args.dir:
        if os.path.isdir(args.dir):
            classifier.process_directory(args.dir, show_results=args.show, max_display=args.max_display)
        else:
            print(f"Error: Directory {args.dir} not found")
    
    else:
        print("Please provide either --image or --dir argument")
        parser.print_help()


if __name__ == "__main__":
    main()
