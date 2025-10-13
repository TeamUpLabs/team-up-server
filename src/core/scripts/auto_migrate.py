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
import traceback
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from sqlalchemy import text, inspect, Table as SATable, Column as SAColumn, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.schema import CreateTable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Resolve project root (this script is expected under <project_root>/scripts/)
# Use current working directory as project root to avoid path issues
import os
PROJECT_ROOT = os.getcwd()  # Current working directory should be project root
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Clean up any duplicate paths in sys.path
unique_paths = []
for path in sys.path:
    if path not in unique_paths:
        unique_paths.append(path)

# Add our required paths
required_paths = [PROJECT_ROOT, SRC_DIR]
for path in required_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import the app's database module with better error handling
console = Console()
try:
    from src.core.database.database import Base, engine
except ImportError as e:
    console.print(f"[red]❌ Failed to import database module: {e}[/red]")
    console.print("[yellow]Please ensure your database configuration is correct.[/yellow]")
    sys.exit(1)

app = typer.Typer(add_help_option=True, rich_markup_mode="rich")


class ChangeType(Enum):
    """Types of database changes that can be detected."""
    CREATE_TABLE = "create_table"
    ADD_COLUMN = "add_column"
    SET_NOT_NULL = "set_not_null"
    TYPE_CHANGE = "type_change"
    WARN = "warn"
    INFO = "info"


@dataclass
class DatabaseChange:
    """Represents a database change to be applied."""
    change_type: ChangeType
    description: str
    sql: Optional[str] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None

    def __post_init__(self):
        if self.change_type == ChangeType.ADD_COLUMN and self.table_name and self.column_name:
            self.table_name = self.table_name
            self.column_name = self.column_name


class DatabaseInspector:
    """Handles database inspection and schema comparison."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)

    def get_existing_tables(self) -> set[str]:
        """Get all existing table names from database."""
        return set(self.inspector.get_table_names())

    def get_existing_columns(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get existing columns for a table."""
        return {col["name"]: col for col in self.inspector.get_columns(table_name)}

    def get_model_tables(self) -> Dict[str, SATable]:
        """Get all tables defined in SQLAlchemy models."""
        return {table.name: table for table in Base.metadata.sorted_tables}


class ModelImporter:
    """Handles dynamic importing of model modules."""

    def __init__(self, project_root: str, src_dir: str):
        self.project_root = project_root
        self.src_dir = src_dir
        self.models_dir = os.path.join(src_dir, 'api', 'v1', 'models')

    def import_all_models(self) -> None:
        """Import all model modules to populate Base.metadata."""
        console.print("[dim]📦 Importing model modules...[/dim]")

        # Ensure paths are in sys.path
        if self.src_dir not in sys.path:
            sys.path.insert(0, self.src_dir)
        if self.models_dir not in sys.path:
            sys.path.insert(0, self.models_dir)

        # Import models package first
        try:
            importlib.import_module('src.api.v1.models')
        except ImportError as e:
            console.print(f"[yellow]⚠️  Warning: Could not import main models package: {e}[/yellow]")

        # Dynamically discover and import all model files
        self._import_models_recursively(self.models_dir, 'src.api.v1.models')

        console.print(f"[green]✅ Successfully imported models[/green]")

    def _import_models_recursively(self, directory: str, package_prefix: str) -> None:
        """Recursively import all Python files in the models directory."""
        if not os.path.exists(directory):
            console.print(f"[yellow]⚠️  Models directory not found: {directory}[/yellow]")
            return

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)

            if os.path.isfile(item_path) and item.endswith('.py') and not item.startswith('__'):
                module_name = item[:-3]  # Remove .py extension
                full_module_name = f"{package_prefix}.{module_name}"

                try:
                    importlib.import_module(full_module_name)
                except ImportError as e:
                    console.print(f"[yellow]⚠️  Warning: Could not import {full_module_name}: {e}[/yellow]")
                    console.print(f"[dim]   Traceback: {traceback.format_exc()}[/dim]")

            elif os.path.isdir(item_path) and not item.startswith('__'):
                submodule_prefix = f"{package_prefix}.{item}"
                self._import_models_recursively(item_path, submodule_prefix)


class MigrationPlanner:
    """Plans database migrations based on schema comparison."""

    def __init__(self, engine: Engine):
        self.db_inspector = DatabaseInspector(engine)
        self.model_importer = ModelImporter(PROJECT_ROOT, SRC_DIR)

    def plan_migration(self, enforce_not_null: bool = False) -> List[DatabaseChange]:
        """Compare database schema with models and plan changes."""
        console.print("[dim]🔍 Analyzing database schema...[/dim]")

        # Import all models first
        self.model_importer.import_all_models()

        # Get current state
        existing_tables = self.db_inspector.get_existing_tables()
        model_tables = self.db_inspector.get_model_tables()

        changes = []

        # 1) Create missing tables
        changes.extend(self._plan_create_tables(existing_tables, model_tables))

        # 2) Handle existing tables
        for table_name in existing_tables.intersection(model_tables.keys()):
            table_changes = self._plan_table_changes(table_name, model_tables[table_name], enforce_not_null)
            changes.extend(table_changes)

        # 3) Warn about extra tables in database
        changes.extend(self._plan_extra_tables(existing_tables, model_tables))

        console.print(f"[green]✅ Analysis complete. Found {len(changes)} changes.[/green]")
        return changes

    def _plan_create_tables(self, existing_tables: set[str], model_tables: Dict[str, SATable]) -> List[DatabaseChange]:
        """Plan creation of missing tables."""
        changes = []
        for table_name, table in model_tables.items():
            if table_name not in existing_tables:
                ddl = str(CreateTable(table).compile(dialect=self.db_inspector.engine.dialect))
                changes.append(DatabaseChange(
                    change_type=ChangeType.CREATE_TABLE,
                    description=f"Create table '{table_name}'",
                    sql=f"{ddl};",
                    table_name=table_name
                ))
        return changes

    def _plan_table_changes(self, table_name: str, table: SATable, enforce_not_null: bool) -> List[DatabaseChange]:
        """Plan changes for an existing table."""
        changes = []
        existing_columns = self.db_inspector.get_existing_columns(table_name)

        for column in table.columns:
            column_changes = self._plan_column_changes(table_name, column, existing_columns, enforce_not_null)
            changes.extend(column_changes)

        return changes

    def _plan_column_changes(self, table_name: str, column: SAColumn, existing_columns: Dict[str, Dict[str, Any]],
                           enforce_not_null: bool) -> List[DatabaseChange]:
        """Plan changes for a specific column."""
        changes = []

        if column.name not in existing_columns:
            # New column to add
            changes.extend(self._plan_add_column(table_name, column, enforce_not_null))
        else:
            # Existing column - check for type/nullability changes
            changes.extend(self._plan_column_modifications(table_name, column, existing_columns[column.name]))

        return changes

    def _plan_add_column(self, table_name: str, column: SAColumn, enforce_not_null: bool) -> List[DatabaseChange]:
        """Plan addition of a new column."""
        changes = []

        # Check if we need to make it nullable initially
        make_nullable_override = None
        if not column.nullable and column.server_default is None:
            make_nullable_override = True
            changes.append(DatabaseChange(
                change_type=ChangeType.WARN,
                description=f"Column '{table_name}.{column.name}' is NOT NULL without default. Will add as NULLABLE first.",
                table_name=table_name,
                column_name=column.name
            ))

        # Add the column
        changes.append(DatabaseChange(
            change_type=ChangeType.ADD_COLUMN,
            description=f"Add column '{table_name}.{column.name}': {self._describe_column(column)}",
            sql=self._generate_add_column_sql(table_name, column, make_nullable_override),
            table_name=table_name,
            column_name=column.name
        ))

        # Plan NOT NULL enforcement if requested
        if enforce_not_null and not column.nullable and column.server_default is None:
            changes.append(DatabaseChange(
                change_type=ChangeType.SET_NOT_NULL,
                description=f"Enforce NOT NULL for '{table_name}.{column.name}' after backfill",
                sql=self._generate_set_not_null_sql(table_name, column.name),
                table_name=table_name,
                column_name=column.name
            ))

        return changes

    def _plan_column_modifications(self, table_name: str, column: SAColumn, existing_col: Dict[str, Any]) -> List[DatabaseChange]:
        """Plan modifications for existing columns."""
        changes = []

        # Check type differences
        model_type = self._get_column_type_string(column)
        existing_type = str(existing_col.get("type", ""))

        if model_type.lower() != existing_type.lower():
            changes.append(DatabaseChange(
                change_type=ChangeType.TYPE_CHANGE,
                description=f"Type differs for '{table_name}.{column.name}': db={existing_type} vs model={model_type}",
                table_name=table_name,
                column_name=column.name
            ))

        # Check nullability differences
        existing_nullable = existing_col.get("nullable", True)
        if existing_nullable != column.nullable:
            changes.append(DatabaseChange(
                change_type=ChangeType.INFO,
                description=f"Nullability differs for '{table_name}.{column.name}': "
                           f"db={'NULL' if existing_nullable else 'NOT NULL'} vs "
                           f"model={'NULL' if column.nullable else 'NOT NULL'}",
                table_name=table_name,
                column_name=column.name
            ))

        return changes

    def _plan_extra_tables(self, existing_tables: set[str], model_tables: Dict[str, SATable]) -> List[DatabaseChange]:
        """Plan warnings for tables that exist in DB but not in models."""
        changes = []
        for table_name in sorted(existing_tables - set(model_tables.keys())):
            changes.append(DatabaseChange(
                change_type=ChangeType.WARN,
                description=f"Table '{table_name}' exists in database but not in models. Manual cleanup may be needed.",
                table_name=table_name
            ))
        return changes

    def _describe_column(self, column: SAColumn) -> str:
        """Generate a human-readable description of a column."""
        type_str = self._get_column_type_string(column)
        nullable = "NULL" if column.nullable else "NOT NULL"

        default = None
        if column.server_default is not None:
            default = str(column.server_default.arg.text) if hasattr(column.server_default.arg, "text") else str(column.server_default.arg)

        result = f"{column.name} {type_str} {nullable}"
        if default:
            result += f" DEFAULT {default}"

        return result

    def _get_column_type_string(self, column: SAColumn) -> str:
        """Get the compiled type string for a column."""
        if isinstance(column.type, NullType):
            return "NULL"
        return getattr(column.type, "compile", lambda dialect=None: str(column.type))(self.db_inspector.engine.dialect)

    def _generate_add_column_sql(self, table_name: str, column: SAColumn, make_nullable_override: Optional[bool] = None) -> str:
        """Generate SQL to add a column."""
        compiled_type = self._get_column_type_string(column)
        nullable = column.nullable if make_nullable_override is None else make_nullable_override

        parts = [f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {compiled_type}']

        if column.server_default is not None:
            default_val = str(column.server_default.arg.text) if hasattr(column.server_default.arg, "text") else str(column.server_default.arg)
            parts.append(f"DEFAULT {default_val}")

        if not nullable:
            parts.append("NOT NULL")

        return " ".join(parts) + ";"

    def _generate_set_not_null_sql(self, table_name: str, column_name: str) -> str:
        """Generate SQL to set a column to NOT NULL."""
        return f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" SET NOT NULL;'


class MigrationExecutor:
    """Executes planned database migrations."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def execute_migration(self, changes: List[DatabaseChange], dry_run: bool = True) -> None:
        """Execute the planned changes."""
        if not changes:
            console.print("[green]✨ No changes needed. Database is up-to-date with models.[/green]")
            return

        # Display planned changes
        self._display_changes(changes)

        if dry_run:
            console.print(Panel.fit("[bold yellow]🔍 DRY RUN MODE[/bold yellow]\n\nNo SQL will be executed. Use --apply to run the migration.", style="yellow"))
            return

        # Execute changes
        self._apply_changes(changes)

    def _display_changes(self, changes: List[DatabaseChange]) -> None:
        """Display the planned changes in a table."""
        table = Table(title="[bold blue]📋 Planned Database Changes[/bold blue]")
        table.add_column("Type", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Table", style="green")
        table.add_column("Column", style="yellow")
        table.add_column("SQL Preview", style="dim")

        for change in changes:
            table.add_row(
                f"[{self._get_style_for_change_type(change.change_type)}]{change.change_type.value}[/{self._get_style_for_change_type(change.change_type)}]",
                change.description,
                change.table_name or "",
                change.column_name or "",
                (change.sql or "")[:100] + ("..." if len(change.sql or "") > 100 else "")
            )

        console.print(table)

    def _get_style_for_change_type(self, change_type: ChangeType) -> str:
        """Get appropriate styling for change type."""
        styles = {
            ChangeType.CREATE_TABLE: "bold green",
            ChangeType.ADD_COLUMN: "green",
            ChangeType.SET_NOT_NULL: "yellow",
            ChangeType.TYPE_CHANGE: "red",
            ChangeType.WARN: "yellow",
            ChangeType.INFO: "blue"
        }
        return styles.get(change_type, "white")

    def _apply_changes(self, changes: List[DatabaseChange]) -> None:
        """Apply the changes to the database."""
        executable_changes = [change for change in changes if change.sql]

        if not executable_changes:
            console.print("[cyan]ℹ️  Nothing to apply (only warnings/info).[/cyan]")
            return

        console.print(f"\n[bold]🚀 Executing {len(executable_changes)} changes...[/bold]")

        with self.engine.begin() as conn:
            for change in executable_changes:
                console.print(f"[dim]▶️  Executing: {change.sql}[/dim]")
                try:
                    conn.execute(text(change.sql))
                    console.print(f"[green]✅ Successfully applied: {change.description}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to apply: {change.description}[/red]")
                    console.print(f"[red]   Error: {e}[/red]")
                    raise

        console.print("[bold green]🎉 Migration completed successfully![/bold green]")


def validate_environment() -> None:
    """Validate that required environment variables are set."""
    if not os.getenv("POSTGRES_URL"):
        console.print("[red]❌ POSTGRES_URL environment variable is not set.[/red]")
        console.print("[yellow]💡 Please set your database URL in .env file or environment variables.[/yellow]")
        sys.exit(1)

    console.print("[green]✅ Environment validation passed[/green]")


@app.command()
def migrate(
    dry_run: bool = typer.Option(True, "--dry-run", help="Preview changes without executing them"),
    enforce_not_null: bool = typer.Option(False, "--enforce-not-null", help="Enforce NOT NULL constraints after adding columns"),
    apply: bool = typer.Option(False, "--apply", help="Actually apply the changes (disables dry-run)")
) -> None:
    """Run auto-migration comparing models to the live database."""

    # Override dry_run if --apply is specified
    if apply:
        dry_run = False

    console.rule("[bold blue]🚀 Auto Migration Tool[/bold blue]")
    console.print(f"[dim]Database: {os.getenv('POSTGRES_URL', 'Not configured')[:50]}...[/dim]")

    # Validate environment
    validate_environment()

    # Plan migration
    planner = MigrationPlanner(engine)
    changes = planner.plan_migration(enforce_not_null=enforce_not_null)

    # Execute migration
    executor = MigrationExecutor(engine)
    executor.execute_migration(changes, dry_run=dry_run)

    console.print("\n[dim]💡 Tip: Use --apply flag to actually run the migration[/dim]")


@app.command()
def check():
    """Check database connection and model import status."""
    console.rule("[bold blue]🔍 Database Check[/bold blue]")

    # Validate environment
    validate_environment()

    # Test database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            console.print("[green]✅ Database connection successful[/green]")
    except Exception as e:
        console.print(f"[red]❌ Database connection failed: {e}[/red]")
        return

    # Test model import
    try:
        importer = ModelImporter(PROJECT_ROOT, SRC_DIR)
        importer.import_all_models()
        console.print(f"[green]✅ Successfully imported {len(Base.metadata.tables)} tables[/green]")
    except Exception as e:
        console.print(f"[red]❌ Model import failed: {e}[/red]")


if __name__ == "__main__":
    app()
