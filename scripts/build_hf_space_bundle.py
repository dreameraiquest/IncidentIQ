from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / ".hf-space-build"


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            ".DS_Store",
            "faiss_index",
            "*.faiss",
            "*.pkl",
        ),
    )


def build_bundle(output_dir: Path) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_file(REPO_ROOT / "app.py", output_dir / "app.py")
    copy_file(REPO_ROOT / "deploy" / "hf-space" / "README.md", output_dir / "README.md")
    copy_file(REPO_ROOT / "requirements.txt", output_dir / "requirements.txt")

    copy_tree(REPO_ROOT / "src", output_dir / "src")

    return output_dir


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    build_bundle(target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
