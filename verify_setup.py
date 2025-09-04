"""
TicketFlow AI - Setup Verification Script
Run this to make sure everything is working properly
"""

import sys
import importlib

def test_import(package_name, friendly_name=None):
    """Test if a package can be imported"""
    if friendly_name is None:
        friendly_name = package_name
    
    try:
        importlib.import_module(package_name)
        print(f"✅ {friendly_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {friendly_name} - FAILED: {e}")
        return False

def main():
    print("🎫 TicketFlow AI - Setup Verification")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version >= (3, 8):
        print("✅ Python version is compatible")
    else:
        print("❌ Python version too old (need 3.8+)")
        return
    
    print("\n📦 Testing Package Imports:")
    print("-" * 30)
    
    # Test essential packages
    packages_to_test = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pymysql", "PyMySQL"),
        ("openai", "OpenAI"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests"),
        ("dotenv", "Python-dotenv"),
        ("pytidb", "TiDB"),
    ]
    
    success_count = 0
    total_count = len(packages_to_test)
    
    for package, friendly in packages_to_test:
        if test_import(package, friendly):
            success_count += 1
    
    print("\n📊 Results:")
    print("-" * 20)
    print(f"Successfully imported: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All packages working perfectly!")
        print("\n🚀 Ready to start building TicketFlow AI!")
        
        # Test some basic functionality
        print("\n🔧 Testing Basic Functionality:")
        test_basic_functionality()
        
    else:
        print("⚠️  Some packages missing. Install them with:")
        print("pip install <package-name>")

def test_basic_functionality():
    """Test basic functionality of key packages"""
    
    try:
        # Test NumPy
        import numpy as np
        test_array = np.array([1, 2, 3, 4, 5])
        print(f"✅ NumPy array creation: {test_array}")
        
        # Test Pandas
        import pandas as pd
        test_df = pd.DataFrame({"id": [1, 2, 3], "status": ["new", "processing", "resolved"]})
        print(f"✅ Pandas DataFrame: {len(test_df)} rows")
        
        # Test Pydantic (dataclass alternative)
        from pydantic import BaseModel
        
        class TestTicket(BaseModel):
            id: str
            title: str
            status: str = "new"
        
        ticket = TestTicket(id="123", title="Test ticket")
        print(f"✅ Pydantic model: {ticket.id} - {ticket.title}")
        
        # Test async (basic)
        import asyncio
        
        async def test_async():
            return "Async working!"
        
        result = asyncio.run(test_async())
        print(f"✅ Async/await: {result}")
        
        print("\n🎯 Core functionality verified!")
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")

if __name__ == "__main__":
    main()