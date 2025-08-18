#!/usr/bin/env python3
"""
Launch script for the Enhanced NL2DAX Streamlit Interface with Advanced Visualizations

This script launches the enhanced Streamlit interface that includes comprehensive 
international portfolio visualizations based on our test question suite.

Features launched:
- Geographic world maps and regional analysis
- Multi-currency portfolio treemaps and dashboards
- Risk analytics with concentration monitoring
- Interactive filters and drill-down capabilities
- Advanced chart library (maps, sunbursts, gauges, etc.)

Usage:
    python launch_enhanced_streamlit.py
    
Requirements:
    - All dependencies from requirements.txt
    - Enhanced international dataset
    - Working NL2DAX pipeline

Author: NL2DAX Development Team
Date: August 16, 2025
"""

import sys
import subprocess
import os
from pathlib import Path

def check_and_install_dependencies():
    """Check and install required dependencies for enhanced visualizations"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✅ All packages installed successfully!")
    else:
        print("✅ All required packages are available!")

def launch_enhanced_interface():
    """Launch the enhanced Streamlit interface"""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    enhanced_ui_path = current_dir / "streamlit_enhanced_ui.py"
    
    if not enhanced_ui_path.exists():
        print(f"❌ Enhanced UI file not found: {enhanced_ui_path}")
        return False
    
    print("🚀 Launching Enhanced NL2DAX Interface...")
    print("🌍 Features include:")
    print("   • Geographic world maps and regional analysis")
    print("   • Multi-currency portfolio visualizations")
    print("   • Risk analytics and concentration monitoring")
    print("   • Interactive dashboards and drill-down capabilities")
    print("   • Advanced chart library (treemaps, sunbursts, gauges)")
    print()
    print("🔗 The interface will open in your default web browser")
    print("🔍 Try the international test questions from our comprehensive suite!")
    print()
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(enhanced_ui_path),
            '--server.port=8501',
            '--server.address=localhost'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch Streamlit interface: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Shutting down Enhanced NL2DAX Interface...")
        return True
    
    return True

def main():
    """Main function to check dependencies and launch interface"""
    
    print("🌍 Enhanced NL2DAX International Portfolio Analysis")
    print("=" * 55)
    print()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    check_and_install_dependencies()
    print()
    
    # Launch interface
    success = launch_enhanced_interface()
    
    if success:
        print("\n✅ Enhanced interface launched successfully!")
        print("📈 Explore international portfolio visualizations")
        print("🌐 Test with geographic and multi-currency queries")
    else:
        print("\n❌ Failed to launch enhanced interface")
        print("🔧 Please check your environment and dependencies")

if __name__ == "__main__":
    main()