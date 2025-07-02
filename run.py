#!/usr/bin/env python3
"""
EVE Industry Tracker - Run Script

This script provides an easy way to start the EVE Industry Tracker application.
It handles environment setup, database initialization, and provides helpful
startup information.

Usage:
    python run.py [--dev] [--port PORT] [--host HOST]

Options:
    --dev       Run in development mode with debug enabled
    --port      Port to run the application on (default: 5000)
    --host      Host to bind to (default: 127.0.0.1)
    --init-db   Initialize the database tables
    --help      Show this help message
"""

import argparse
import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the environment and check for required files."""
    # Add current directory to Python path
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Load environment variables from .env file if it exists
    env_file = current_dir / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✓ Loaded environment variables from {env_file}")
        except ImportError:
            print("Warning: python-dotenv not installed. Environment variables not loaded.")
    
    return current_dir

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_migrate', 
        'requests', 'jwt'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install them with: pip install -r requirements.txt")
        return False
    
    print("✓ All required dependencies are installed")
    return True

def check_configuration():
    """Check if EVE SSO configuration is present."""
    client_id = os.getenv('EVE_CLIENT_ID')
    client_secret = os.getenv('EVE_CLIENT_SECRET')
    
    if not client_id or client_id == 'your_client_id_here':
        print("⚠️  EVE_CLIENT_ID not configured")
        return False
    
    if not client_secret or client_secret == 'your_client_secret_here':
        print("⚠️  EVE_CLIENT_SECRET not configured")
        return False
    
    print("✓ EVE SSO configuration found")
    return True

def initialize_database():
    """Initialize the database with required tables."""
    try:
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Database initialized successfully")
            return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def print_startup_info(host, port, debug=False):
    """Print helpful startup information."""
    print("\n" + "="*60)
    print("🚀 EVE Industry Tracker Starting Up")
    print("="*60)
    print(f"🌐 URL: http://{host}:{port}")
    print(f"🔧 Debug Mode: {'Enabled' if debug else 'Disabled'}")
    print(f"📝 Environment: {'Development' if debug else 'Production'}")
    
    # Check configuration status
    config_ok = check_configuration()
    if not config_ok:
        print("\n⚠️  CONFIGURATION WARNING:")
        print("   EVE SSO credentials are not properly configured.")
        print("   Please set EVE_CLIENT_ID and EVE_CLIENT_SECRET in your .env file")
        print("   or environment variables before using the application.")
    
    print("\n📖 Quick Start Guide:")
    print("   1. Ensure you have registered an EVE SSO application")
    print("   2. Set your EVE_CLIENT_ID and EVE_CLIENT_SECRET")
    print("   3. Navigate to the URL above and click 'Login with EVE Online'")
    print("   4. First user from each corporation becomes an admin")
    
    print("\n🛑 To stop the server: Press Ctrl+C")
    print("="*60)

def main():
    """Main function to run the EVE Industry Tracker."""
    parser = argparse.ArgumentParser(
        description="EVE Industry Tracker - Corporation Industrial Job Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--dev', 
        action='store_true',
        help='Run in development mode with debug enabled'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        help='Port to run the application on (default: 5000)'
    )
    
    parser.add_argument(
        '--host', 
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize the database and exit'
    )
    
    args = parser.parse_args()
    
    # Setup environment
    current_dir = setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        if initialize_database():
            print("Database initialization complete!")
        else:
            sys.exit(1)
        return
    
    # Import app after environment setup
    try:
        from app import app
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        print("Make sure app.py is in the current directory and all dependencies are installed.")
        sys.exit(1)
    
    # Set debug mode
    debug_mode = args.dev or os.getenv('FLASK_ENV') == 'development'
    app.config['DEBUG'] = debug_mode
    
    # Initialize database if it doesn't exist
    db_path = current_dir / 'eve_industry.db'
    if not db_path.exists():
        print("Database not found. Initializing...")
        if not initialize_database():
            sys.exit(1)
    
    # Print startup information
    print_startup_info(args.host, args.port, debug_mode)
    
    try:
        # Start the application
        app.run(
            host=args.host,
            port=args.port,
            debug=debug_mode,
            use_reloader=debug_mode
        )
    except KeyboardInterrupt:
        print("\n\n👋 EVE Industry Tracker shut down gracefully")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()