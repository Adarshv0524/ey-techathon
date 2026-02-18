from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "frontend.main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
    )


if __name__ == "__main__":
    main()
