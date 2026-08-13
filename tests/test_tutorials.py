from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SECRET_KEY_RE = re.compile(r"(?:bfk_[A-Za-z0-9_-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})")

REPO_ROOT = Path(__file__).resolve().parent.parent
TUTORIALS = sorted(REPO_ROOT.glob("tutorials/*.py"))

SKIP_SECRET_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".marimo",
    "__pycache__",
    "data",
    "scripts",
}
SKIP_SECRET_FILES = {".env"}


def test_tutorials_exist() -> None:
    assert TUTORIALS, "expected at least one tutorials/*.py notebook"


@pytest.mark.parametrize("path", TUTORIALS, ids=lambda p: p.name)
def test_tutorial_is_marimo_app(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "app" for t in node.targets)
        for node in tree.body
    ), f"{path.name} does not assign app ="

    try:
        from marimo._ast.load import load_app
    except ImportError:
        pytest.skip("marimo is not installed")

    loaded = load_app(str(path))
    assert loaded is not None, f"{path.name} did not load as a marimo app"


def test_committed_tree_has_no_api_keys() -> None:
    offenders: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_SECRET_DIRS for part in path.parts):
            continue
        if path.name in SKIP_SECRET_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SECRET_KEY_RE.search(text):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"committed files contain API secrets: {offenders}"
