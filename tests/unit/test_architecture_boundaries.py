"""Clean Architecture dependency-direction and configuration tests."""
from __future__ import annotations

import ast
from pathlib import Path

from logistics_chatbot.core import config

SRC_PKG = Path(__file__).resolve().parents[2] / "src" / "logistics_chatbot"


def _collect_imports(folder: Path) -> list[tuple[str, str]]:
    imports: list[tuple[str, str]] = []
    for py_file in folder.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((py_file.name, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append((py_file.name, node.module))
    return imports


def test_domain_layer_has_no_framework_or_outer_layer_dependencies():
    """Domain entities and repository interfaces must not import presentation, infrastructure, or SDKs."""
    forbidden_prefixes = (
        "logistics_chatbot.presentation",
        "logistics_chatbot.infrastructure",
        "logistics_chatbot.application",
        "fastapi",
        "starlette",
        "groq",
        "chromadb",
        "psycopg2",
        "sqlite3",
    )
    for fname, mod in _collect_imports(SRC_PKG / "domain"):
        for bad in forbidden_prefixes:
            assert not mod.startswith(bad), f"Domain file {fname} illegally imports '{mod}'"


def test_application_layer_does_not_depend_on_presentation():
    """Application use cases and chatbot logic must stay independent of FastAPI/presentation."""
    for fname, mod in _collect_imports(SRC_PKG / "application"):
        assert not mod.startswith("logistics_chatbot.presentation"), (
            f"Application file {fname} illegally imports '{mod}'"
        )
        assert not mod.startswith("fastapi"), f"Application file {fname} imports FastAPI '{mod}'"


def test_core_paths_resolve_canonical_directories():
    """Canonical frontend, migrations, manuals, source docs, and reports directories exist."""
    assert config.TEMPLATES_DIR.exists()
    assert (config.TEMPLATES_DIR / "index.html").exists()
    assert (config.STATIC_DIR / "css" / "style.css").exists()
    assert (config.STATIC_DIR / "js" / "app.js").exists()
    assert (config.MIGRATIONS_SQL_DIR / "schema.sql").exists()
    assert (config.MIGRATIONS_SQL_DIR / "schema_v2_enterprise.sql").exists()
    assert config.KB_MANUALS_DIR.exists()
    assert config.SOURCE_DOCS_DIR.exists()
    assert config.REPORTS_DIR.exists()
