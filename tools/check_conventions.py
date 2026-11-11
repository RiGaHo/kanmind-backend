"""Check function length limits and disallow print calls."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".venv", "frontend", ".git", "__pycache__"}


def inspect_file(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = node.end_lineno - node.lineno + 1
            assert length <= 14, f"{path}:{node.lineno}: {length} lines"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "print", f"{path}:{node.lineno}: print()"


def main():
    for path in ROOT.rglob("*.py"):
        if not EXCLUDED.intersection(path.relative_to(ROOT).parts):
            inspect_file(path)


if __name__ == "__main__":
    main()
