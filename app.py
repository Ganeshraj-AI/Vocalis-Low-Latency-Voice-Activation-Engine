import os
import sys

# Ensure vocalis root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vocalis.app import main

if __name__ == "__main__":
    main()
