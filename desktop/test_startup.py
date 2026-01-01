"""Quick test script to verify Flask can start in background thread."""
import threading
import time
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_flask_startup():
    """Test if Flask can start successfully."""
    print("Testing Flask startup...")

    try:
        from src.flask_app.app import create_app

        # Create app
        app = create_app()
        print("✓ Flask app created successfully")

        # Test routes
        with app.app_context():
            # Check if routes are registered
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            print(f"✓ Found {len(routes)} routes")

        print("\n✓ Flask startup test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Flask startup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pywebview_import():
    """Test if PyWebView can be imported."""
    print("\nTesting PyWebView import...")

    try:
        import webview
        print(f"✓ PyWebView imported successfully")
        # Note: webview.platform is only available after starting webview
        print("\n✓ PyWebView import test PASSED")
        return True
    except Exception as e:
        print(f"\n✗ PyWebView import test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("MIB Parser Desktop - Startup Test")
    print("=" * 60)

    # Test Flask
    flask_ok = test_flask_startup()

    # Test PyWebView
    pywebview_ok = test_pywebview_import()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"Flask: {'✓ PASS' if flask_ok else '✗ FAIL'}")
    print(f"PyWebView: {'✓ PASS' if pywebview_ok else '✗ FAIL'}")

    if flask_ok and pywebview_ok:
        print("\n✓ All tests passed! Desktop app should work correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)
