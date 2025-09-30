#!/usr/bin/env python3
"""
Auto migration utility for SQLAlchemy models without Alembic.

Capabilities:
- Import your SQLAlchemy engine and Base from src/core/database/database.py
- Dynamically import all modules in models/ so metadata is populated
- Compare live DB schema vs. model metadata
- Create missing tables
- Add missing columns (safe, additive changes only)
- Dry-run mode to preview DDL
- Optional flag to attempt setting NOT NULL after backfill

Limitations:
- Does NOT drop columns or tables automatically (prints warnings)
- Does NOT rename columns or tables (requires manual migration)
- Type changes are detected and reported, not auto-applied

Usage:
  python scripts/auto_migrate.py --help

Examples:
  # Preview what would change (no writes)
  python scripts/auto_migrate.py --dry-run

  # Apply additive changes
  python scripts/auto_migrate.py

  # Apply and try to enforce NOT NULL where models require it (after you backfilled data)
  python scripts/auto_migrate.py --enforce-not-null

Environment:
- Requires POSTGRES_URL (loaded via dotenv if present) consistent with your app.
"""
from __future__ import annotations

import os
import sys
import pkgutil
import importlib
from typing import Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from sqlalchemy import text, inspect, Table as SATable, Column as SAColumn
from sqlalchemy.engine import Engine
from sqlalchemy.sql.sqltypes import NullType

# Resolve project root (this script is expected under <project_root>/scripts/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Import the app's database module
try:
    from src.core.database.database import Base, engine
except ModuleNotFoundError:
    # Fallback: some codebases reference it as just core.database.database
    try:
        from core.database.database import Base, engine
    except ModuleNotFoundError:
        # Final fallback: try a top-level database module
        from database import Base, engine

console = Console()
app = typer.Typer(add_help_option=True)


def import_all_models() -> None:
    """Import all modules in the models/ package so that Base.metadata is fully populated."""
    # Add the src directory to path if not already there
    src_dir = os.path.join(PROJECT_ROOT, 'src')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Import models directly by manipulating the path
    models_dir = os.path.join(src_dir, 'api', 'v1', 'models')
    if models_dir not in sys.path:
        sys.path.insert(0, models_dir)

    # Import each model file manually
    model_files = [
        'user.user',
        'user.collaboration_preference',
        'user.user_tech_stack',
        'user.user_interest',
        'user.user_social_link',
        'user.user_session',
        'project.project',
        'project.project_member',
        'project.participation_request',
        'community.post',
        'community.whiteboard',
        'community.notification',
        'association_tables',
        'base'
    ]

    for model_file in model_files:
        try:
            module_path = f'api.v1.models.{model_file}'
            importlib.import_module(module_path)
        except ImportError as e:
            console.print(f"[yellow]Warning: Could not import {model_file}: {e}[/yellow]")


def _import_package_recursive(pkg_name: str) -> None:
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError:
        return
    pkg_path = os.path.dirname(pkg.__file__)  # type: ignore
    for module_info in pkgutil.iter_modules([pkg_path]):
        fqmn = f"{pkg_name}.{module_info.name}"
        if module_info.ispkg:
            _import_package_recursive(fqmn)
        else:
            importlib.import_module(fqmn)


class Change:
    def __init__(self, kind: str, description: str, sql: Optional[str] = None):
        self.kind = kind  # "create_table" | "add_column" | "warn" | "info" | "type_change"
        self.description = description
        self.sql = sql

    def __repr__(self) -> str:
        return f"Change(kind={self.kind}, description={self.description}, sql={self.sql})"


def describe_column(col: SAColumn) -> str:
    type_ = getattr(col.type, "compile", lambda dialect=None: str(col.type))(engine.dialect)
    nullable = "NULL" if col.nullable else "NOT NULL"
    default = None
    if col.server_default is not None:
        default = str(col.server_default.arg.text) if hasattr(col.server_default.arg, "text") else str(col.server_default.arg)
    return f"{col.name} {type_} {nullable}" + (f" DEFAULT {default}" if default else "")


def generate_add_column_sql(table_name: str, col: SAColumn, make_nullable_override: Optional[bool] = None) -> str:
    # Build column definition SQL manually for Postgres
    compiled_type = col.type.compile(engine.dialect) if hasattr(col.type, "compile") else str(col.type)
    nullable = col.nullable if make_nullable_override is None else make_nullable_override
    parts = [f"ALTER TABLE \"{table_name}\" ADD COLUMN \"{col.name}\" {compiled_type}"]
    if col.server_default is not None:
        default_val = str(col.server_default.arg.text) if hasattr(col.server_default.arg, "text") else str(col.server_default.arg)
        parts.append(f"DEFAULT {default_val}")
    if not nullable:
        parts.append("NOT NULL")
    return " ".join(parts) + ";"


def generate_set_not_null_sql(table_name: str, col_name: str) -> str:
    return f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{col_name}\" SET NOT NULL;"


def compare_and_plan(engine: Engine, enforce_not_null: bool = False) -> List[Change]:
    inspector = inspect(engine)

    changes: List[Change] = []

    existing_tables = set(inspector.get_table_names())
    model_tables: Dict[str, SATable] = {t.name: t for t in Base.metadata.sorted_tables}

    # 1) Create missing tables
    for tname, table in model_tables.items():
        if tname not in existing_tables:
            ddl = str(CreateTableCompiler(engine.dialect, table))
            changes.append(Change(
                kind="create_table",
                description=f"Create table {tname}",
                sql=ddl
            ))

    # 2) For existing tables, add missing columns; detect type or nullable changes
    for tname in existing_tables.intersection(model_tables.keys()):
        cols_existing = {col["name"]: col for col in inspector.get_columns(tname)}
        table = model_tables[tname]
        for col in table.columns:
            if col.name not in cols_existing:
                # If the model says NOT NULL but there's no default, we cannot add as NOT NULL directly if table has rows
                # Safer: add as NULLABLE, then allow enforcing later
                make_nullable_override = None
                if not col.nullable and col.server_default is None:
                    make_nullable_override = True
                    changes.append(Change(
                        kind="warn",
                        description=(
                            f"Column {tname}.{col.name} is NOT NULL without default. Will add as NULLABLE; "
                            f"backfill required before enforcing NOT NULL."
                        )
                    ))
                changes.append(Change(
                    kind="add_column",
                    description=f"Add column {tname}.{col.name}: {describe_column(col)}",
                    sql=generate_add_column_sql(tname, col, make_nullable_override=make_nullable_override)
                ))
                if enforce_not_null and (not col.nullable) and (col.server_default is None):
                    changes.append(Change(
                        kind="info",
                        description=f"Enforce NOT NULL for {tname}.{col.name} after backfill",
                        sql=generate_set_not_null_sql(tname, col.name)
                    ))
            else:
                # Compare types and nullability (informational only)
                existing = cols_existing[col.name]
                existing_type = existing.get("type")
                # Attempt to compare by compiled type string
                model_type = getattr(col.type, "compile", lambda dialect=None: str(col.type))(engine.dialect)
                existing_type_str = str(existing_type)
                if isinstance(col.type, NullType):
                    pass
                elif existing_type_str.lower() != model_type.lower():
                    changes.append(Change(
                        kind="type_change",
                        description=(
                            f"Type differs for {tname}.{col.name}: db={existing_type_str} vs model={model_type}. "
                            f"Manual migration recommended."
                        )
                    ))
                # Nullability difference
                if bool(existing.get("nullable", True)) != bool(col.nullable):
                    changes.append(Change(
                        kind="info",
                        description=(
                            f"Nullability differs for {tname}.{col.name}: db={'NULL' if existing.get('nullable', True) else 'NOT NULL'} "
                            f"vs model={'NULL' if col.nullable else 'NOT NULL'}. Manual review recommended."
                        )
                    ))

    # 3) Warn about tables present in DB but not in models
    for tname in sorted(existing_tables - set(model_tables.keys())):
        changes.append(Change(
            kind="warn",
            description=f"Table {tname} exists in DB but not in models. Skipping (no drops)."
        ))

    return changes


def apply_changes(engine: Engine, changes: List[Change], dry_run: bool) -> None:
    if not changes:
        console.print("[green]No changes needed. Database is up-to-date with models.[/green]")
        return

    table = Table(title="Planned actions")
    table.add_column("Kind")
    table.add_column("Description")
    table.add_column("SQL")

    for ch in changes:
        table.add_row(ch.kind, ch.description, ch.sql or "")

    console.print(table)

    if dry_run:
        console.print(Panel.fit("Dry-run mode: no SQL will be executed.", style="yellow"))
        return

    write_sql = [ch for ch in changes if ch.sql]
    if not write_sql:
        console.print("[cyan]Nothing to apply (only warnings/info).[/cyan]")
        return

    with engine.begin() as conn:
        for ch in write_sql:
            console.print(f"[bold]Executing:[/bold] {ch.sql}")
            conn.execute(text(ch.sql))
    console.print("[green]Migration completed successfully.[/green]")


class CreateTableCompiler:
    """Very small helper to serialize a Table create statement for Postgres.
    We rely on SQLAlchemy's DDL compiler by leveraging the Table's .compile with create prefix.
    """

    def __init__(self, dialect, table: SATable):
        self.dialect = dialect
        self.table = table

    def __str__(self) -> str:
        # Generate CREATE TABLE ... including columns and constraints
        from sqlalchemy.schema import CreateTable
        return str(CreateTable(self.table).compile(dialect=self.dialect)).rstrip("\n") + ";"


@app.command()
def migrate(dry_run: bool = typer.Option(False, help="Preview SQL without executing"),
            enforce_not_null: bool = typer.Option(False, help="After adding columns that are NOT NULL without defaults, also plan a SET NOT NULL (assumes you will backfill)")):
    """Run auto-migration comparing models to the live database."""
    console.rule("Auto Migration")

    # Ensure models are imported
    import_all_models()

    # Plan
    changes = compare_and_plan(engine, enforce_not_null=enforce_not_null)

    # Apply
    apply_changes(engine, changes, dry_run=dry_run)


if __name__ == "__main__":
    app()
