import os
import argparse
import pandas as pd
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
from sklearn.preprocessing import LabelEncoder
from pathlib import Path


class FeedbackDataset(Dataset):
    """Dataset class for user feedback data"""
    def __init__(self, csv_path, transform=None):
        """
        Initialize the dataset with feedback data
        
        Args:
            csv_path: Path to the CSV file containing feedback data
            transform: Image transformations to apply
        """
        self.data = pd.read_csv(csv_path)
        self.transform = transform
        
        # Get unique classes
        self.classes = self.data['label'].unique()
        
        print(f"Loaded {len(self.data)} samples with {len(self.classes)} classes")
        print(f"Classes: {self.classes}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        # Get image path and label
        image_path = self.data.iloc[idx]['image_path']
        label = self.data.iloc[idx]['label']
        
        # Check if path is relative
        if not os.path.isabs(image_path):
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_path)
            
        # Load image
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            # Provide a dummy image in case of error
            image = Image.new('RGB', (224, 224), color=(128, 128, 128))
        
        # Apply transform if any
        if self.transform:
            image = self.transform(image)
        
        # Convert label to index (mapping is consistent with our 3 classes)
        if label == "Truck":
            label_idx = 0
        elif label == "Minitruck":
            label_idx = 1
        else:  # Car
            label_idx = 2
        
        return image, label_idx


def retrain_model(feedback_csv, original_model_path, original_encoder_path, output_dir, 
                  epochs=5, batch_size=8, learning_rate=0.001):
    """
    Retrain the model with user feedback data
    
    Args:
        feedback_csv: Path to the CSV file containing feedback data
        original_model_path: Path to the original model weights
        original_encoder_path: Path to the original label encoder
        output_dir: Directory to save the retrained model
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate for training
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Define transformations
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    # Create dataset
    dataset = FeedbackDataset(feedback_csv, transform=transform)
    
    # Create dataloader
    dataloader = DataLoader(
        dataset, 
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )
    
    # Load the original model
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, len(dataset.classes))
    
    # Load weights if available
    try:
        model.load_state_dict(torch.load(original_model_path, map_location=device, weights_only=True))
        print(f"Loaded original model weights from {original_model_path}")
    except Exception as e:
        print(f"Error loading original model weights: {e}")
        print("Starting with fresh model weights")
    
    model.to(device)
    
    # Set up optimizer and criterion
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = torch.nn.CrossEntropyLoss()
    
    # Training loop
    print(f"Starting training for {epochs} epochs...")
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for i, (images, labels) in enumerate(dataloader):
            images, labels = images.to(device), labels.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            # Statistics
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            if (i + 1) % 5 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Step [{i+1}/{len(dataloader)}], "
                      f"Loss: {running_loss / (i+1):.4f}, "
                      f"Accuracy: {100 * correct / total:.2f}%")
    
    print("Training complete!")
    
    # Save the retrained model
    output_model_path = os.path.join(output_dir, "retrained_model_weights.pth")
    torch.save(model.state_dict(), output_model_path)
    print(f"Retrained model saved to {output_model_path}")
    
    # Create and save a new label encoder
    le = LabelEncoder()
    le.fit(dataset.classes)
    output_encoder_path = os.path.join(output_dir, "retrained_label_encoder.pth")
    torch.save(le, output_encoder_path)
    print(f"Retrained label encoder saved to {output_encoder_path}")
    
    return output_model_path, output_encoder_path


def main():
    parser = argparse.ArgumentParser(description='Retrain Model with User Feedback')
    parser.add_argument('--feedback', type=str, required=True,
                        help='Path to the feedback CSV file')
    parser.add_argument('--model', type=str, default='pt/model_weights.pth',
                        help='Path to the original model weights')
    parser.add_argument('--encoder', type=str, default='pt/label_encoder.pth',
                        help='Path to the original label encoder')
    parser.add_argument('--output', type=str, default='pt/retrained',
                        help='Directory to save the retrained model')
    parser.add_argument('--epochs', type=int, default=5,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=8,
                        help='Batch size for training')
    parser.add_argument('--lr', type=float, default=0.001,
                        help='Learning rate for training')
    
    args = parser.parse_args()
    
    retrain_model(
        args.feedback,
        args.model,
        args.encoder,
        args.output,
        args.epochs,
        args.batch_size,
        args.lr
    )


if __name__ == '__main__':
    main()
