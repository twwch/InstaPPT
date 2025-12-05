import os
import sys

# Ensure src is in path for local execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from instappt.cli import main

if __name__ == "__main__":
    main()
