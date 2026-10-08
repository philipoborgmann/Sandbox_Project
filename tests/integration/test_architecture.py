"""Protect domain independence and cross-module public APIs."""

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "quont_sandbox"


def imports(path: Path) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return tuple(modules)


def test_domain_and_ports_remain_independent_of_adapters() -> None:
    protected = [*PACKAGE.glob("common/*.py")]
    for module in ("assets", "data"):
        protected.extend(
            PACKAGE / module / filename
            for filename in ("domain.py", "repositories.py", "__init__.py")
        )
    protected.extend(
        [
            PACKAGE / "assets/application.py",
            PACKAGE / "data/providers.py",
            PACKAGE / "data/storage.py",
        ]
    )
    for path in protected:
        for module in imports(path):
            assert module.split(".")[0] not in {"sqlalchemy", "typer", "fastapi", "psycopg"}, path
            assert "infrastructure" not in module.split("."), path


def test_assets_and_data_use_other_modules_public_api() -> None:
    for owner in ("assets", "data"):
        for path in (PACKAGE / owner).rglob("*.py"):
            for module in imports(path):
                parts = module.split(".")
                if parts[0] == "quont_sandbox" and len(parts) > 1:
                    if parts[1] in {"assets", "data", "common"} and parts[1] != owner:
                        assert len(parts) == 2, (path, module)
