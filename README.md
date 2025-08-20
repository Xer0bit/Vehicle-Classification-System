# Image Classification System

This repository contains code for an intelligent image classification system based on a pre-trained ResNet50 model.

## Project Structure

```
G:/Bitlogicx/Classification/v2/
├── classify.py       # Main classification script
├── demo.py          # Demo script to quickly test the classifier
├── train.ipynb      # Notebook used for training (reference only)
├── dataset/         # Contains training, validation and test data
│   ├── test/        # Test images
│   ├── train/       # Training images (organized by class)
│   └── val/         # Validation images (organized by class)
└── pt/              # Contains saved model weights and label encoder
    ├── label_encoder.pth
    └── model_weights.pth
```

## Requirements

- Python 3.6+
- PyTorch
- torchvision
- numpy
- matplotlib
- Pillow (PIL)

Install the required packages:

```bash
pip install torch torchvision numpy matplotlib pillow
```

## Usage

### Quick Demo

Run the demo script to see the classifier in action:

```bash
python demo.py
```

This will:
1. Initialize the classifier using the pre-trained model
2. Classify a single test image and display it with the prediction
3. Classify multiple test images and display them with predictions

### Using the Classification Script

The main classification script `classify.py` can be used in several ways:

#### 1. Classify a Single Image

```bash
python classify.py --image path/to/your/image.jpg --show
```

#### 2. Classify All Images in a Directory

```bash
python classify.py --dir path/to/your/image/folder --show --max_display 25
```

#### 3. Command Line Options

- `--image`: Path to a single image to classify
- `--dir`: Path to a directory containing images to classify
- `--model`: Path to model weights (default: pt/model_weights.pth)
- `--encoder`: Path to label encoder (default: pt/label_encoder.pth)
- `--show`: Flag to display images with predictions
- `--max_display`: Maximum number of images to display (default: 25)
- `--map`: Enable class mapping to consolidate classes into three categories (Truck, Minitruck, Car)
  - Truck: heavy truck, bus, truck
  - Minitruck: fire engine, mini truck
  - Car: all other vehicle types

## Using the Classifier in Your Own Code

You can also import and use the `ImageClassifier` class in your own Python code:

```python
from classify import ImageClassifier

# Initialize the classifier (standard classification)
classifier = ImageClassifier(
    model_path="pt/model_weights.pth",
    label_encoder_path="pt/label_encoder.pth"
)

# Initialize the classifier with class mapping (Truck, Minitruck, Car)
mapped_classifier = ImageClassifier(
    model_path="pt/model_weights.pth",
    label_encoder_path="pt/label_encoder.pth",
    use_mapping=True  # Enable class mapping
)

# Classify a single image (standard)
class_name, confidence, _ = classifier.predict_single_image(
    image_path="path/to/your/image.jpg",
    show_image=True
)
print(f"Prediction: {class_name} (Confidence: {confidence:.2f})")

# Classify a single image (with mapping)
mapped_class, confidence, original_class = mapped_classifier.predict_single_image(
    image_path="path/to/your/image.jpg",
    show_image=True
)
print(f"Prediction: {mapped_class} (Original: {original_class}, Confidence: {confidence:.2f})")

# Process a directory of images
results = classifier.process_directory(
    directory_path="path/to/your/images",
    show_results=True,
    max_display=25
)

# Process a directory of images with class mapping
mapped_results = mapped_classifier.process_directory(
    directory_path="path/to/your/images",
    show_results=True,
    max_display=25
)
```

## Model Information

The classification model is based on ResNet50 pre-trained on ImageNet and fine-tuned on custom data. The model has been trained to classify images into multiple categories.
