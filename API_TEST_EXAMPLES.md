# Vehicle Classification API - Test Examples

## Prerequisites
- API Server running on localhost:5000 (start with: `python api_server.py --port 5000`)
- Image file to test with

## Quick Start Commands

### 1. Health Check (No Authentication Required)
```bash
curl -X GET "http://localhost:5000/api/health" \
  -H "Content-Type: application/json"
```

### 2. Image Classification Test

#### Python Helper Script (Recommended)
Save this as `test_api.py`:
```python
import requests
import sys

def test_classification(image_path):
    # API Configuration
    API_KEY = "your_api_key"  # Replace with your API key
    API_URL = "http://localhost:5000"
    
    # Prepare headers
    headers = {
        'X-API-Key': API_KEY
    }
    
    # Send request
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                f'{API_URL}/api/classify',
                headers=headers,
                files={'image': f}
            )
            
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Generate curl command for reference
        print(f"\nEquivalent curl command:")
        print(f'curl -X POST "{API_URL}/api/classify" \\')
        print(f'  -H "X-API-Key: {API_KEY}" \\')
        print(f'  -F "image=@{image_path}"')
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_api.py <image_path>")
        sys.exit(1)
    test_classification(sys.argv[1])
```

Run with: `python test_api.py path/to/your/image.jpg`

## For Postman Collection

### Environment Variables
Create a Postman environment with these variables:
- `api_key`: your_api_key
- `base_url`: http://localhost:5000

### Making Requests in Postman

1. Set up a new POST request to `{{base_url}}/api/classify`
2. Add header: `X-API-Key: {{api_key}}`
3. In the "Body" tab:
   - Select "form-data"
   - Add a key "image" of type "File"
   - Upload your image file

### Response Format
```json
{
    "success": true,
    "class_name": "predicted_class",
    "confidence": 0.95,
    "original_class": "original_class"
}

// Create message (method + path + timestamp)
const method = pm.request.method;
const path = pm.request.url.getPath();
const message = method + "\n" + path + "\n" + timestamp + "\n";

// Generate HMAC signature
const signature = CryptoJS.HmacSHA256(message, apiSecret).toString();

// Set headers
pm.request.headers.add({
    key: "X-API-Key",
    value: pm.environment.get("api_key")
});

pm.request.headers.add({
    key: "X-API-Signature", 
    value: signature
});

pm.request.headers.add({
    key: "X-API-Timestamp",
    value: timestamp
});

console.log("Generated signature:", signature);
console.log("Timestamp:", timestamp);
```

## Quick Test Commands

### Test 1: Health Check
```bash
curl -X GET "http://localhost:5000/api/health"
```

### Test 2: Classification (replace with actual image path)
Use the Python method above to generate headers, then:
```bash
curl -X POST "http://localhost:5000/api/classify" \
  -H "X-API-Key: gyds73hg5ff5643j345" \
  -H "X-API-Signature: [GENERATED_SIGNATURE]" \
  -H "X-API-Timestamp: [GENERATED_TIMESTAMP]" \
  -F "image=@/path/to/test/image.jpg"
```

## Expected Responses

### Health Check Response:
```json
{
  "status": "healthy",
  "classifier_loaded": true,
  "timestamp": "2025-08-21T10:30:00.123456"
}
```

### Classification Response:
```json
{
  "success": true,
  "class_name": "Car",
  "confidence": 0.95,
  "original_class": "Vehicle",
  "timestamp": "2025-08-21T10:30:00.123456"
}
```

### Statistics Response:
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "uptime_human": "1h 0m",
  "requests_total": 10,
  "requests_successful": 8,
  "requests_failed": 2,
  "success_rate": 80.0,
  "timestamp": "2025-08-21T10:30:00.123456"
}
```
