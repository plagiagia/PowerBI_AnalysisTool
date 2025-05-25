#!/usr/bin/env python3
"""
Setup script for Power BI Analysis Tool
Creates a .env file from template if it doesn't exist
"""

import os

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    
    env_template = """# Power BI Analysis Tool Configuration
# Copy this file to .env and update with your actual values

# OpenAI Configuration (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000

# Flask Configuration
SECRET_KEY=your_very_secure_secret_key_here
FLASK_ENV=development

# Feature Flags (optional)
ENABLE_AI_FEATURES=true
ENABLE_SOURCE_EXPLORER=true
ENABLE_DAX_EXPLORER=true
ENABLE_LINEAGE_VIEW=true
"""

    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ Created .env file from template")
        print("📝 Please edit .env file and add your OpenAI API key and other configurations")
    else:
        print("⚠️  .env file already exists - skipping creation")

if __name__ == "__main__":
    create_env_file() 