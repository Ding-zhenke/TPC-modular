"""Portable entry point from an extracted plugin; tasks stay in --workspace."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == '__main__':
    from tpc_editor.__main__ import main
    main()
