#!/usr/bin/env python3
"""
Python guide for fixing Power BI tenant settings for DAX 401 errors
Since this requires admin privileges, this script provides step-by-step instructions
"""

import webbrowser
from datetime import datetime

def print_header():
    print("🚀 Power BI Tenant Settings Fix Guide")
    print("=" * 60)
    print("📝 This guide will help you fix the DAX 401 error by configuring")
    print("   the required Power BI tenant settings.")
    print("=" * 60)
    print()

def print_requirements():
    print("🔐 REQUIREMENTS:")
    print("   • Power BI Administrator privileges")
    print("   • Access to Power BI Admin Portal")
    print("   • Authority to modify tenant settings")
    print()

def get_admin_confirmation():
    print("❓ Do you have Power BI Administrator privileges?")
    response = input("   Enter 'yes' to continue or 'no' for alternative options: ").lower().strip()
    return response in ['yes', 'y', 'true', '1']

def provide_alternative_options():
    print("\n🔄 ALTERNATIVE OPTIONS:")
    print()
    print("1. 👥 Contact your Power BI Administrator")
    print("   • Share this diagnostic output with them")
    print("   • Request they enable 'Dataset Execute Queries REST API'")
    print("   • Ask them to run the PowerShell script: scripts/fix_dax_tenant_settings.ps1")
    print()
    print("2. 🔗 Use XMLA Endpoint (Alternative approach)")
    print("   • Connect directly to XMLA endpoint instead of REST API")
    print("   • May work even if REST API setting is disabled")
    print("   • Update your connection method in the application")
    print()
    print("3. 📞 Escalate to IT/Power BI Support")
    print("   • Contact your organization's IT support")
    print("   • Reference Microsoft documentation on service principal setup")
    print()

def guide_manual_configuration():
    print("\n🛠️ MANUAL CONFIGURATION STEPS:")
    print("=" * 50)
    
    steps = [
        {
            "step": 1,
            "title": "Access Power BI Admin Portal",
            "actions": [
                "Go to https://app.powerbi.com",
                "Click the Settings gear icon (⚙️) in the top right",
                "Select 'Admin portal' from the dropdown",
                "If you don't see 'Admin portal', you don't have admin rights"
            ]
        },
        {
            "step": 2,
            "title": "Navigate to Tenant Settings",
            "actions": [
                "In the Admin portal, click 'Tenant settings' in the left menu",
                "This page shows all organization-wide Power BI settings"
            ]
        },
        {
            "step": 3,
            "title": "Enable Service Principal API Access",
            "actions": [
                "Scroll down to 'Developer settings' section",
                "Find 'Allow service principals to use Power BI APIs'",
                "Make sure this is ENABLED",
                "Set scope to 'Entire organization' or your service principal's security group"
            ]
        },
        {
            "step": 4,
            "title": "Enable Dataset Execute Queries REST API (CRITICAL)",
            "actions": [
                "Scroll to 'Export and sharing settings' section",
                "Find 'Dataset Execute Queries REST API'",
                "ENABLE this setting (this is the key fix!)",
                "Set scope to 'Entire organization' or your service principal's security group",
                "This setting specifically controls DAX query execution via REST API"
            ]
        },
        {
            "step": 5,
            "title": "Enable XMLA Endpoints (if using Premium)",
            "actions": [
                "Go to 'Capacity settings' in the Admin portal",
                "Select your Premium capacity",
                "Go to 'Workloads' tab",
                "Set 'XMLA Endpoint' to 'Read Write'",
                "This enables advanced dataset operations"
            ]
        },
        {
            "step": 6,
            "title": "Apply and Wait",
            "actions": [
                "Click 'Apply' for each setting you change",
                "Wait 15-20 minutes for changes to propagate",
                "Tenant setting changes can take time to take effect globally"
            ]
        }
    ]
    
    for step_info in steps:
        print(f"\n📋 STEP {step_info['step']}: {step_info['title']}")
        print("-" * 40)
        for i, action in enumerate(step_info['actions'], 1):
            print(f"   {i}. {action}")
    
    print("\n⏰ IMPORTANT: Wait 15-20 minutes after making changes!")

def provide_verification_steps():
    print(f"\n🧪 VERIFICATION STEPS:")
    print("=" * 50)
    print("After waiting 15-20 minutes, test the fix:")
    print()
    print("1. 🐍 Run Python diagnostic:")
    print("   cd /Users/arturoquiroga/GITHUB/NL2DAX/CODE")
    print("   python xmla_status_check.py")
    print()
    print("2. 🔍 Run comprehensive check:")
    print("   python diagnose_permissions.py")
    print()
    print("3. 🚀 Test main application:")
    print("   python main.py")
    print("   Try a simple query like: 'Show me the first 5 customers'")

def open_admin_portal():
    response = input("\n🌐 Would you like to open the Power BI Admin Portal now? (y/n): ").lower().strip()
    if response in ['yes', 'y', 'true', '1']:
        try:
            webbrowser.open('https://app.powerbi.com/admin-portal/tenantSettings')
            print("✅ Opening Power BI Admin Portal in your browser...")
        except:
            print("❌ Could not open browser. Please navigate to:")
            print("   https://app.powerbi.com/admin-portal/tenantSettings")

def show_tenant_setting_details():
    print(f"\n📊 CRITICAL TENANT SETTING DETAILS:")
    print("=" * 50)
    print()
    print("🎯 PRIMARY FIX:")
    print("   Setting: 'Dataset Execute Queries REST API'")
    print("   Location: Tenant Settings → Export and sharing settings")
    print("   Required: ENABLED")
    print("   Purpose: Controls DAX query execution via REST API")
    print("   Impact: Without this, ALL DAX REST API calls return 401")
    print()
    print("🔧 SUPPORTING SETTINGS:")
    print("   1. 'Allow service principals to use Power BI APIs'")
    print("      Location: Tenant Settings → Developer settings")
    print("      Purpose: Basic service principal authentication")
    print()
    print("   2. 'XMLA Endpoint' (Premium only)")
    print("      Location: Capacity Settings → Workloads")
    print("      Purpose: Advanced dataset operations")

def main():
    print_header()
    print_requirements()
    
    if get_admin_confirmation():
        show_tenant_setting_details()
        guide_manual_configuration()
        provide_verification_steps()
        open_admin_portal()
        
        print(f"\n📋 SUMMARY:")
        print("   1. ✅ Enable 'Dataset Execute Queries REST API' (CRITICAL)")
        print("   2. ✅ Verify 'Allow service principals to use Power BI APIs'")
        print("   3. ✅ Enable XMLA endpoints (if Premium)")
        print("   4. ⏰ Wait 15-20 minutes")
        print("   5. 🧪 Test with diagnostic scripts")
        
    else:
        provide_alternative_options()
    
    print(f"\n📞 SUPPORT:")
    print("   • Microsoft Docs: https://docs.microsoft.com/power-bi/developer/embedded/embed-service-principal")
    print("   • Power BI Community: https://community.powerbi.com/")
    print("   • NL2DAX Issues: https://github.com/Arturo-Quiroga-MSFT/NL2DAX/issues")
    
    print(f"\n✨ Configuration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
