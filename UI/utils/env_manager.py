import os
from pathlib import Path
from dotenv import load_dotenv

class EnvManager:
    def __init__(self, base_dir):
        self.env_file = os.path.join(base_dir, '.env')
        self.ensure_env_file()
        load_dotenv(self.env_file)
        
    def ensure_env_file(self):
        """Create .env file with default values if it doesn't exist"""
        if not os.path.exists(self.env_file):
            default_env = """# API Credentials
API_KEY=
API_SECRET_KEY=

# Server Settings
API_PORT=5000
SSL_ENABLED=true
CORS_ENABLED=false
CORS_ORIGINS=*
RATE_LIMIT=60
"""
            with open(self.env_file, 'w') as f:
                f.write(default_env)
                
    def get_credentials(self):
        """Get API credentials from .env"""
        return {
            'api_key': os.getenv('API_KEY', ''),
            'api_secret_key': os.getenv('API_SECRET_KEY', '')
        }
        
    def save_credentials(self, api_key, api_secret_key):
        """Save API credentials to .env"""
        current_content = ''
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                current_content = f.read()
                
        # Update API credentials while preserving other settings
        lines = current_content.splitlines()
        updated_lines = []
        
        api_key_found = api_secret_found = False
        
        for line in lines:
            if line.startswith('API_KEY='):
                updated_lines.append(f'API_KEY={api_key}')
                api_key_found = True
            elif line.startswith('API_SECRET_KEY='):
                updated_lines.append(f'API_SECRET_KEY={api_secret_key}')
                api_secret_found = True
            else:
                updated_lines.append(line)
                
        # Add missing entries if needed
        if not api_key_found:
            updated_lines.append(f'API_KEY={api_key}')
        if not api_secret_found:
            updated_lines.append(f'API_SECRET_KEY={api_secret_key}')
            
        # Write back to file
        with open(self.env_file, 'w') as f:
            f.write('\n'.join(updated_lines))
            
    def get_api_key(self):
        """Get API key from .env"""
        return os.getenv('API_KEY', '')
        
    def get_api_secret(self):
        """Get API secret from .env"""
        return os.getenv('API_SECRET_KEY', '')
