# Vehicle Classification API Documentation

This document provides detailed information on using the Vehicle Classification API, which identifies vehicles as Truck, Minitruck, or Car from images.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Classify Image](#classify-image)
  - [Health Check](#health-check)
  - [Statistics](#statistics)
  - [CORS Test](#cors-test)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
  - [cURL](#curl)
  - [Python](#python)
  - [JavaScript](#javascript)
- [Rate Limiting](#rate-limiting)
- [Web UI](#web-ui)
- [Deployment](#deployment)

## Overview

The Vehicle Classification API uses a deep learning model (ResNet50) to classify vehicle images. The model has been trained to recognize different vehicle types and maps them to three categories:

- **Truck**: Large commercial trucks and heavy vehicles
- **Minitruck**: Smaller trucks, buses, and fire engines
- **Car**: Personal vehicles, cars, and other smaller vehicles

The API accepts image uploads and returns classification results with confidence scores.

## Authentication

All API endpoints (except `/api/health`) require authentication using an API key.

- **Header Name**: `X-API-Key`
- **Value**: Your API key (provided separately)

Example:
```
X-API-Key: your_api_key_here
```

To obtain an API key, please contact the system administrator. The API key should be kept secret and not shared publicly.

## API Endpoints

### Classify Image

Classifies a vehicle image and returns the predicted category.

- **URL**: `/api/classify`
- **Method**: `POST`
- **Auth Required**: Yes
- **Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| image | File | Yes | The image file to classify (PNG, JPG, JPEG, GIF) |

**Success Response**:

- **Code**: 200 OK
- **Content Example**:
```json
{
  "success": true,
  "class_name": "Car",
  "confidence": 0.95,
  "original_class": "sedan",
  "timestamp": "2025-08-23T10:15:30.123456"
}
```

**Error Responses**:

- **Code**: 400 Bad Request
  - Missing image file or invalid file format
- **Code**: 401 Unauthorized
  - Missing or invalid API key
- **Code**: 500 Internal Server Error
  - Server error or classification failure

### Health Check

Checks if the API service is up and running.

- **URL**: `/api/health`
- **Method**: `GET`
- **Auth Required**: No

**Success Response**:

- **Code**: 200 OK
- **Content Example**:
```json
{
  "status": "healthy",
  "classifier_loaded": true,
  "timestamp": "2025-08-23T10:15:30.123456"
}
```

### Statistics

Provides usage statistics for the API service.

- **URL**: `/api/stats`
- **Method**: `GET`
- **Auth Required**: Yes

**Success Response**:

- **Code**: 200 OK
- **Content Example**:
```json
{
  "status": "running",
  "uptime_seconds": 86400,
  "uptime_human": "1d 0h 0m",
  "requests_total": 1000,
  "requests_successful": 950,
  "requests_failed": 50,
  "success_rate": 95.0,
  "timestamp": "2025-08-23T10:15:30.123456"
}
```

### CORS Test

Simple endpoint to test CORS functionality.

- **URL**: `/api/test-cors`
- **Method**: `GET`
- **Auth Required**: No

**Success Response**:

- **Code**: 200 OK
- **Content Example**:
```json
{
  "message": "CORS is working!",
  "timestamp": "2025-08-23T10:15:30.123456",
  "method": "GET"
}
```

## Response Formats

All API responses are in JSON format with the following standard structure:

**Success Response**:
```json
{
  "success": true,
  "class_name": "Car",
  "confidence": 0.95,
  "original_class": "sedan",
  "timestamp": "2025-08-23T10:15:30.123456"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Error message details"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- **200**: Request successful
- **400**: Bad request (missing parameters, invalid file format)
- **401**: Unauthorized (missing or invalid API key)
- **500**: Internal server error

All error responses include a descriptive message to help troubleshoot the issue.

## Code Examples

### cURL

```bash
# Classify an image
curl -X POST "http://your-server:5000/api/classify" \
  -H "X-API-Key: your_api_key_here" \
  -F "image=@/path/to/your/vehicle/image.jpg"

# Check API health
curl "http://your-server:5000/api/health"

# Get API statistics
curl "http://your-server:5000/api/stats" \
  -H "X-API-Key: your_api_key_here"
```

### Python

```python
import requests

# API configuration
API_URL = "http://your-server:5000/api/classify"
API_KEY = "your_api_key_here"
IMAGE_PATH = "/path/to/your/vehicle/image.jpg"

# Set up headers and files
headers = {
    "X-API-Key": API_KEY
}
files = {
    "image": open(IMAGE_PATH, "rb")
}

# Make the request
response = requests.post(API_URL, headers=headers, files=files)

# Process the response
if response.status_code == 200:
    result = response.json()
    print(f"Classification: {result['class_name']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Original class: {result['original_class']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### JavaScript

```javascript
// Using Fetch API
async function classifyImage(imageFile) {
  const apiUrl = 'http://your-server:5000/api/classify';
  const apiKey = 'your_api_key_here';
  
  const formData = new FormData();
  formData.append('image', imageFile);
  
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey
      },
      body: formData
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log(`Classification: ${result.class_name}`);
      console.log(`Confidence: ${result.confidence.toFixed(2)}`);
      console.log(`Original class: ${result.original_class}`);
      return result;
    } else {
      console.error(`Error: ${result.error}`);
      return null;
    }
  } catch (error) {
    console.error('API request failed:', error);
    return null;
  }
}

// Usage example
const fileInput = document.getElementById('imageInput');
fileInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (file) {
    classifyImage(file)
      .then(result => {
        if (result) {
          // Process successful result
          displayResult(result);
        }
      });
  }
});
```

## Rate Limiting

While the API does not currently implement strict rate limiting, please use it responsibly and avoid sending excessive requests. The system administrator may implement rate limiting in the future to ensure fair usage.

## Web UI

A web user interface is available for testing the API:

- **URL**: `/`
- **API Testing Interface**: `/api-test`

The web UI provides a simple way to upload images for classification without writing code.

## Deployment

The API service can be deployed in the following ways:

### 1. Direct Execution

```bash
python web_server.py --host 0.0.0.0 --port 5000
```

### 2. Windows Service

Use the provided batch scripts to install and manage the API as a Windows service:

- `install_service.bat`: Install as Windows service
- `run_service.bat`: Run the service
- `stop_service.bat`: Stop the service
- `uninstall_service.bat`: Uninstall the service

### 3. Environment Configuration

Create a `.env` file with the following configuration:

```
API_KEY=your_secret_api_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url  # Optional for logging
```

## Additional Information

- **Image Size Limits**: Maximum file size is 16MB
- **Supported Image Formats**: PNG, JPG, JPEG, GIF
- **Classification Time**: Typically under 1 second per image
- **Service Logs**: Available in the `logs` directory

For additional support or to report issues, please contact the system administrator.
