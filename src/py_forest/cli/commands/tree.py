"""Tree management commands."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from py_forest.cli.client import get_client

app = typer.Typer()
console = Console()


@app.command("list")
def list_trees(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter by name"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Filter by tags (comma-separated)"),
):
    """List all trees in the library."""
    try:
        client = get_client()

        if name or tags:
            tag_list = tags.split(",") if tags else None
            trees = client.search_trees(name=name, tags=tag_list)
        else:
            trees = client.list_trees()

        if not trees:
            console.print("[yellow]No trees found.[/yellow]")
            return

        table = Table(title="Behavior Trees")
        table.add_column("Tree ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Version", style="magenta")
        table.add_column("Tags", style="blue")

        for tree in trees:
            tree_id = tree.get("tree_id", "N/A")
            metadata = tree.get("metadata", {})
            name = metadata.get("name", "N/A")
            version = metadata.get("version", "N/A")
            tags = ", ".join(metadata.get("tags", []))

            table.add_row(tree_id, name, version, tags)

        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(trees)} tree(s)")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_tree(
    tree_id: str = typer.Argument(..., help="Tree ID to retrieve"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save to file"),
    show_json: bool = typer.Option(False, "--json", help="Show raw JSON"),
):
    """Get details of a specific tree."""
    try:
        client = get_client()
        tree = client.get_tree(tree_id)

        if output:
            with open(output, "w") as f:
                json.dump(tree, f, indent=2)
            console.print(f"[green]✓ Tree saved to {output}[/green]")
            return

        if show_json:
            syntax = Syntax(json.dumps(tree, indent=2), "json", theme="monokai")
            console.print(syntax)
        else:
            metadata = tree.get("metadata", {})
            console.print(Panel.fit(
                f"[bold cyan]{metadata.get('name', 'N/A')}[/bold cyan]\n\n"
                f"[bold]ID:[/bold] {tree.get('tree_id', 'N/A')}\n"
                f"[bold]Version:[/bold] {metadata.get('version', 'N/A')}\n"
                f"[bold]Description:[/bold] {metadata.get('description', 'N/A')}\n"
                f"[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}\n"
                f"[bold]Author:[/bold] {metadata.get('author', 'N/A')}",
                title="Tree Details"
            ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_tree(
    file: Path = typer.Argument(..., help="JSON file containing tree definition"),
):
    """Create a new tree from a JSON file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)

        with open(file) as f:
            tree_def = json.load(f)

        client = get_client()
        created_tree = client.create_tree(tree_def)

        console.print(f"[green]✓ Tree created successfully[/green]")
        console.print(f"[bold]Tree ID:[/bold] {created_tree.get('tree_id')}")
        console.print(f"[bold]Name:[/bold] {created_tree.get('metadata', {}).get('name')}")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in file: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_tree(
    tree_id: str = typer.Argument(..., help="Tree ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a tree from the library."""
    try:
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete tree {tree_id}?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        client = get_client()
        client.delete_tree(tree_id)

        console.print(f"[green]✓ Tree {tree_id} deleted successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
def validate_tree(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="JSON file to validate"),
    tree_id: Optional[str] = typer.Option(None, "--id", help="Tree ID from library to validate"),
):
    """Validate a tree definition."""
    if not file and not tree_id:
        console.print("[red]Error: Either --file or --id must be provided[/red]")
        raise typer.Exit(1)

    try:
        client = get_client()

        if file:
            if not file.exists():
                console.print(f"[red]Error: File not found: {file}[/red]")
                raise typer.Exit(1)

            with open(file) as f:
                tree_def = json.load(f)

            result = client.validate_tree(tree_def)
        else:
            result = client.validate_tree_file(tree_id)

        is_valid = result.get("is_valid", False)
        error_count = result.get("error_count", 0)
        warning_count = result.get("warning_count", 0)
        issues = result.get("issues", [])

        if is_valid:
            console.print("[green]✓ Tree is valid[/green]")
        else:
            console.print("[red]✗ Tree has validation errors[/red]")

        if error_count > 0:
            console.print(f"\n[red bold]Errors: {error_count}[/red bold]")
            for issue in issues:
                if issue.get("level") == "error":
                    console.print(f"  [red]• {issue.get('message')}[/red]")
                    if issue.get("node_path"):
                        console.print(f"    Path: {issue.get('node_path')}")

        if warning_count > 0:
            console.print(f"\n[yellow bold]Warnings: {warning_count}[/yellow bold]")
            for issue in issues:
                if issue.get("level") == "warning":
                    console.print(f"  [yellow]• {issue.get('message')}[/yellow]")

        if not is_valid:
            raise typer.Exit(1)

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in file: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
