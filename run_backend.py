from __future__ import annotations

import sys
from pathlib import Path

import uvicorn


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    backend_dir = repo_root / "backend"

    # Ensure `import app` resolves to backend when launched from repo root.
    sys.path.insert(0, str(backend_dir))

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    main()
