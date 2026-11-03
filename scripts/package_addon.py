"""Build a portable .ankiaddon archive without profile data or build output."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUTPUT = DIST / "powerful-studies.ankiaddon"
EXCLUDED = {".git", ".pytest_cache", "__pycache__", "dist", "tests", ".idea", ".vscode"}


def include(path: Path) -> bool:
    return not any(part in EXCLUDED for part in path.parts) and path.suffix not in {".pyc", ".ankiaddon"}


def main() -> None:
    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob("*"):
            if path.is_file() and include(path.relative_to(ROOT)):
                archive.write(path, path.relative_to(ROOT))
    print(OUTPUT)


if __name__ == "__main__":
    main()
