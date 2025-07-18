"""pytest configuration file to set up Python path and fixtures"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# This ensures that imports like "from src.agents.multi_agent_system import ..." work correctly