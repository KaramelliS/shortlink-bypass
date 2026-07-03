#!/usr/bin/env python3
"""
Entry point for `pip install shortlink-bypass`
"""
import sys
from pathlib import Path

# Add the script directory to path
script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from bypass import main

if __name__ == "__main__":
    main()
