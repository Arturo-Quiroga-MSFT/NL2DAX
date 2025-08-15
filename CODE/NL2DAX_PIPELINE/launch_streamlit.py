#!/usr/bin/env python3
"""
NL2DAX Streamlit Application Launcher

This script launches the Streamlit web interface for the NL2DAX pipeline.
It handles environment setup, dependency checking, and graceful startup.

Usage:
    python launch_streamlit.py
    # or
    ./launch_streamlit.py

The application will be available at: http://localhost:8501
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly',
        'langchain',
        'langchain_openai',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Install missing dependencies"""
    print("🔧 Installing missing dependencies...")
    for package in packages:
        print(f"   📦 Installing {package}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                      capture_output=True, text=True)
    print("✅ Dependencies installed successfully!")

def setup_environment():
    """Setup environment variables and paths"""
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Check for .env file
    env_file = current_dir / '.env'
    if not env_file.exists():
        print("⚠️  Warning: .env file not found. Make sure environment variables are set:")
        print("   - AZURE_OPENAI_ENDPOINT")
        print("   - AZURE_OPENAI_API_KEY") 
        print("   - SQL_SERVER_CONNECTION_STRING")
        print("   - POWERBI_WORKSPACE_ID")
        print("   - And other required variables...")
        print()

def launch_streamlit():
    """Launch the Streamlit application"""
    current_dir = Path(__file__).parent
    streamlit_file = current_dir / 'streamlit_ui.py'
    
    if not streamlit_file.exists():
        print("❌ Error: streamlit_ui.py not found!")
        sys.exit(1)
    
    print("🚀 Launching NL2DAX Streamlit Interface...")
    print("📱 Application will be available at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application")
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(streamlit_file),
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down NL2DAX Interface...")
    except Exception as e:
        print(f"❌ Error launching Streamlit: {e}")
        sys.exit(1)

def main():
    """Main launcher function"""
    print("🔍 NL2DAX Streamlit Interface Launcher")
    print("=" * 50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        install_deps = input("📦 Install missing dependencies? (y/N): ").lower().strip()
        
        if install_deps in ['y', 'yes']:
            install_dependencies(missing)
        else:
            print("❌ Cannot proceed without required dependencies.")
            sys.exit(1)
    else:
        print("✅ All dependencies are installed!")
    
    # Setup environment
    setup_environment()
    
    # Launch application
    launch_streamlit()

if __name__ == "__main__":
    main()
