import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from instappt.ui import launch_ui

if __name__ == "__main__":
    print("Starting InstaPPT Web UI...")
    # Launch on port 7860 by default
    launch_ui(server_name="0.0.0.0", server_port=7860)
