#!/usr/bin/env python3
"""
Quick test script to verify API server functionality
"""

import subprocess
import sys
import time
import requests
import os

def test_api_server():
    print("🚀 Testing API Server Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("api_server.py"):
        print("❌ Error: api_server.py not found. Make sure you're in the correct directory.")
        return False
    
    if not os.path.exists("classify.py"):
        print("❌ Error: classify.py not found. Make sure you're in the correct directory.")
        return False
    
    print("✅ Found required files")
    
    # Test 1: Start API server
    print("\n📡 Starting API server...")
    try:
        # Start the server process
        process = subprocess.Popen([
            sys.executable, "api_server.py", 
            "--port", "5000",
            "--host", "127.0.0.1"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("⏳ Waiting for server to start...")
        time.sleep(3)  # Give server time to start
        
        # Test 2: Health check
        print("🏥 Testing health endpoint...")
        try:
            response = requests.get("http://127.0.0.1:5000/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        print("✅ API server is working correctly!")
        
        # Stop the server
        print("🛑 Stopping server...")
        process.terminate()
        process.wait(timeout=5)
        
        return True
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def check_pytorch_warnings():
    print("\n🔍 Checking for PyTorch warnings...")
    
    # Test classify.py imports
    try:
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import the classifier (this will trigger torch.load)
            from classify import ImageClassifier
            
            # Check for PyTorch warnings
            pytorch_warnings = [warning for warning in w if 'torch.load' in str(warning.message)]
            
            if pytorch_warnings:
                print("⚠️  Found PyTorch warnings:")
                for warning in pytorch_warnings:
                    print(f"   - {warning.message}")
                return False
            else:
                print("✅ No PyTorch warnings found")
                return True
                
    except Exception as e:
        print(f"❌ Error checking PyTorch warnings: {e}")
        return False

if __name__ == "__main__":
    print("🧪 API Server Test Suite")
    print("=" * 50)
    
    # Test PyTorch warnings
    pytorch_ok = check_pytorch_warnings()
    
    # Test API server
    api_ok = test_api_server()
    
    print("\n📋 Test Results:")
    print("=" * 50)
    print(f"PyTorch warnings: {'✅ PASS' if pytorch_ok else '❌ FAIL'}")
    print(f"API server: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if pytorch_ok and api_ok:
        print("\n🎉 All tests passed! Your API server is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Start the API server: python api_server.py --port 5000")
        print("   2. Open api_test_ui.html in your browser")
        print("   3. Or run the GUI: python classifier_gui.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
