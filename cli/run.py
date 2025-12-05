import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

from citadel_cli.app import get_app

def main():
    app = get_app()
    app()

if __name__ == "__main__":
    main()

