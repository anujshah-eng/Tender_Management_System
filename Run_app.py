#Run_app.py
"""Application Launcher"""
import uvicorn
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run(
        "tender_management_system.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
