import sys
from pathlib import Path

# make `import llm_redteam` work without installing
SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))
