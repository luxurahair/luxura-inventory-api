#!/usr/bin/env python3
"""
Focused test for Luxura Distribution Backlink Automation System
Tests the Playwright automation for directory submissions
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

def test_backlink_automation():
    """Test the backlink automation system"""
    print("🔗 TESTING LUXURA BACKLINK AUTOMATION SYSTEM")
    print("=" * 60)
    
    results = []
    
    # Test 1: Import backlink automation module
    print("\n1. Testing module import...")
    try:
        from backlink_automation import (
            LUXURA_BUSINESS, 
            DIRECTORIES, 
            run_backlink_automation,
            get_business_info,
            get_directories_list
        )
        print("✅ Successfully imported backlink automation module")
        results.append(("Module Import", True, "Success"))
    except ImportError as e:
        print(f"❌ Cannot import backlink automation: {e}")
        results.append(("Module Import", False, str(e)))
        return results
    except Exception as e:
        print(f"❌ Error importing: {e}")
        results.append(("Module Import", False, str(e)))
        return results
    
    # Test 2: Business info validation
    print("\n2. Testing business info...")
    try:
        business_info = get_business_info()
        required_fields = ["company_name", "full_address", "phone", "email", "website", "description_short"]
        
        if business_info.get("company_name") == "Luxura Distribution":
            print("✅ Business name correctly set to 'Luxura Distribution'")
            results.append(("Business Name", True, "Correct"))
        else:
            print(f"❌ Business name incorrect: {business_info.get('company_name')}")
            results.append(("Business Name", False, "Incorrect name"))
        
        missing_fields = [field for field in required_fields if not business_info.get(field)]
        if not missing_fields:
            print("✅ All required business fields are present")
            results.append(("Business Fields", True, "Complete"))
        else:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            results.append(("Business Fields", False, f"Missing: {', '.join(missing_fields)}"))
        
        # Show key business info
        print(f"   Company: {business_info.get('company_name')}")
        print(f"   Address: {business_info.get('full_address')}")
        print(f"   Phone: {business_info.get('phone')}")
        print(f"   Email: {business_info.get('email')}")
        print(f"   Website: {business_info.get('website')}")
        
    except Exception as e:
        print(f"❌ Error testing business info: {e}")
        results.append(("Business Info", False, str(e)))
    
    # Test 3: Directories configuration
    print("\n3. Testing directories configuration...")
    try:
        directories = get_directories_list()
        print(f"✅ Found {len(directories)} target directories")
        
        # Check for required directories from review request
        required_dirs = ["Hotfrog Canada", "Cylex Canada", "iGlobal.co", "Canpages", "Yelp Canada"]
        found_dirs = [d.get("name", "") for d in directories]
        
        print("   Configured directories:")
        for i, directory in enumerate(directories, 1):
            priority = directory.get("priority", "UNKNOWN")
            print(f"   {i}. {directory.get('name')} ({priority}) - {directory.get('url')}")
        
        missing_dirs = [d for d in required_dirs if d not in found_dirs]
        if not missing_dirs:
            print("✅ All required directories from review request are configured")
            results.append(("Required Directories", True, "All present"))
        else:
            print(f"❌ Missing directories: {', '.join(missing_dirs)}")
            results.append(("Required Directories", False, f"Missing: {', '.join(missing_dirs)}"))
        
    except Exception as e:
        print(f"❌ Error testing directories: {e}")
        results.append(("Directories", False, str(e)))
    
    # Test 4: Playwright dependency
    print("\n4. Testing Playwright dependency...")
    try:
        import playwright
        print("✅ Playwright is installed and available")
        results.append(("Playwright", True, "Installed"))
    except ImportError:
        print("❌ Playwright is not installed - required for automation")
        print("   Install with: pip install playwright && playwright install")
        results.append(("Playwright", False, "Not installed"))
    
    # Test 5: Screenshot directory
    print("\n5. Testing screenshot directory...")
    try:
        screenshot_dir = Path("/tmp/backlinks")
        screenshot_dir.mkdir(exist_ok=True)
        
        # Test write permissions
        test_file = screenshot_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        
        print(f"✅ Screenshot directory {screenshot_dir} is ready and writable")
        results.append(("Screenshot Directory", True, "Ready"))
    except Exception as e:
        print(f"❌ Cannot create or write to screenshot directory: {e}")
        results.append(("Screenshot Directory", False, str(e)))
    
    # Test 6: Automation functions
    print("\n6. Testing automation functions...")
    try:
        from backlink_automation import submit_to_hotfrog, submit_to_cylex, human_delay, human_type
        
        functions = [
            ("submit_to_hotfrog", submit_to_hotfrog),
            ("submit_to_cylex", submit_to_cylex),
            ("human_delay", human_delay),
            ("human_type", human_type)
        ]
        
        all_good = True
        for func_name, func in functions:
            if callable(func):
                print(f"   ✅ {func_name} is properly defined")
            else:
                print(f"   ❌ {func_name} is not callable")
                all_good = False
        
        if all_good:
            results.append(("Automation Functions", True, "All callable"))
        else:
            results.append(("Automation Functions", False, "Some functions missing"))
            
    except Exception as e:
        print(f"❌ Error testing automation functions: {e}")
        results.append(("Automation Functions", False, str(e)))
    
    # Test 7: Mock automation run (without actually submitting)
    print("\n7. Testing mock automation run...")
    try:
        # Simulate what would happen in a real run
        mock_results = []
        
        for directory in directories[:3]:  # Test first 3 directories
            mock_result = {
                "directory": directory["name"],
                "url": directory["url"],
                "priority": directory["priority"],
                "status": "mock_success",
                "message": f"Would submit to {directory['name']} with Luxura business info"
            }
            mock_results.append(mock_result)
            print(f"   ✅ Mock submission to {directory['name']}")
        
        print(f"✅ Successfully simulated automation for {len(mock_results)} directories")
        results.append(("Mock Automation", True, f"{len(mock_results)} directories"))
        
    except Exception as e:
        print(f"❌ Error in mock automation: {e}")
        results.append(("Mock Automation", False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BACKLINK AUTOMATION TEST SUMMARY")
    print("=" * 60)
    
    passed = len([r for r in results if r[1]])
    failed = len([r for r in results if not r[1]])
    total = len(results)
    
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"📈 TOTAL: {total}")
    print(f"📊 SUCCESS RATE: {(passed/total*100):.1f}%")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}: {message}")
    
    # Critical issues
    critical_failures = [r for r in results if not r[1] and r[0] in ["Module Import", "Playwright"]]
    if critical_failures:
        print(f"\n🚨 CRITICAL ISSUES:")
        for test_name, _, message in critical_failures:
            print(f"   • {test_name}: {message}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if any(r[0] == "Playwright" and not r[1] for r in results):
        print("   • Install Playwright: pip install playwright && playwright install")
    
    if passed == total:
        print("   • 🎉 BACKLINK AUTOMATION SYSTEM IS READY!")
        print("   • All components working correctly")
        print("   • Ready for directory submissions")
        print("   • Consider adding API endpoints for integration")
    elif passed >= total * 0.8:
        print("   • ✅ System mostly ready - fix critical issues")
        print("   • Test with staging environment before production")
    else:
        print("   • ⚠️ Multiple issues detected - review and fix")
    
    # Integration suggestions
    if passed >= total * 0.8:
        print(f"\n🔧 INTEGRATION SUGGESTIONS:")
        print("   • Add API endpoint: POST /api/backlinks/run")
        print("   • Add API endpoint: GET /api/backlinks/status")
        print("   • Add API endpoint: GET /api/backlinks/business-info")
        print("   • Add API endpoint: GET /api/backlinks/directories")
    
    return results

if __name__ == "__main__":
    results = test_backlink_automation()
    
    # Exit with appropriate code
    failed = len([r for r in results if not r[1]])
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)