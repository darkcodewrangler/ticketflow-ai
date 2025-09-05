"""Test PyTiDB installation and basic functionality"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_pytidb_import():
    print("🧪 Testing PyTiDB Installation")
    print("=" * 40)
    
    try:
        # Test basic imports
        from pytidb import TiDBClient
        from pytidb.schema import TableModel, Field, VectorField
        from pytidb.datatype import TEXT, JSON
        print("✅ PyTiDB imports successful")
        
        # Test configuration
        from ticketflow.config import config
        if config.validate():
            print("✅ Configuration valid")
        else:
            print("❌ Configuration validation failed")
            return False
            
        print("\n🎉 PyTiDB installation successful!")
        print("Ready to create PyTiDB models and tables!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install 'pytidb[models]'")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_pytidb_import()