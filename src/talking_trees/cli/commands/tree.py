"""Tree management commands."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from talking_trees.cli.client import get_client

app = typer.Typer()
console = Console()


@app.command("list")
def list_trees(
    name: str | None = typer.Option(None, "--name", "-n", help="Filter by name"),
    tags: str | None = typer.Option(
        None, "--tags", "-t", help="Filter by tags (comma-separated)"
    ),
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
    output: Path | None = typer.Option(None, "--output", "-o", help="Save to file"),
    show_json: bool = typer.Option(False, "--json", help="Show raw JSON"),
):
    """Get details of a specific tree."""
    try:
        client = get_client()
        tree = client.get_tree(tree_id)

        if output:
            with open(output, "w") as f:
                json.dump(tree, f, indent=2)
            console.print(f"[green] Tree saved to {output}[/green]")
            return

        if show_json:
            syntax = Syntax(json.dumps(tree, indent=2), "json", theme="monokai")
            console.print(syntax)
        else:
            metadata = tree.get("metadata", {})
            console.print(
                Panel.fit(
                    f"[bold cyan]{metadata.get('name', 'N/A')}[/bold cyan]\n\n"
                    f"[bold]ID:[/bold] {tree.get('tree_id', 'N/A')}\n"
                    f"[bold]Version:[/bold] {metadata.get('version', 'N/A')}\n"
                    f"[bold]Description:[/bold] {metadata.get('description', 'N/A')}\n"
                    f"[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}\n"
                    f"[bold]Author:[/bold] {metadata.get('author', 'N/A')}",
                    title="Tree Details",
                )
            )

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

        console.print("[green] Tree created successfully[/green]")
        console.print(f"[bold]Tree ID:[/bold] {created_tree.get('tree_id')}")
        console.print(
            f"[bold]Name:[/bold] {created_tree.get('metadata', {}).get('name')}"
        )

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

        console.print(f"[green] Tree {tree_id} deleted successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("diff")
def diff(
    file_a: str = typer.Argument(..., help="Path to first tree JSON"),
    file_b: str = typer.Argument(..., help="Path to second tree JSON"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON patch"),
):
    """Compare two tree files and show differences."""
    from talking_trees.sdk import TalkingTrees

    tt = TalkingTrees()
    tree_a = tt.load_tree(file_a)
    tree_b = tt.load_tree(file_b)

    if json_output:
        import dataclasses

        from talking_trees.core.diff import TreeDiffer

        differ = TreeDiffer()
        diff_result = differ.diff_trees(tree_a, tree_b)
        typer.echo(json.dumps(dataclasses.asdict(diff_result), indent=2, default=str))
    else:
        diff_text = tt.diff_trees(tree_a, tree_b, verbose=True)
        typer.echo(diff_text)


@app.command("merge")
def merge(
    base: str = typer.Argument(..., help="Base tree JSON file"),
    ours: str = typer.Argument(..., help="Our modified tree JSON"),
    theirs: str = typer.Argument(..., help="Their modified tree JSON"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Three-way merge of tree files."""
    from talking_trees.core.diff import three_way_merge
    from talking_trees.sdk import TalkingTrees

    tt = TalkingTrees()
    base_tree = tt.load_tree(base)
    ours_tree = tt.load_tree(ours)
    theirs_tree = tt.load_tree(theirs)

    result = three_way_merge(base_tree, ours_tree, theirs_tree)

    if result.has_conflicts:
        typer.secho(f"CONFLICTS ({len(result.conflicts)}):", fg=typer.colors.RED)
        for c in result.conflicts:
            typer.echo(
                f"  Node '{c.node_name}' [{c.property_name}]: "
                f"base={c.base_value}, ours={c.ours_value}, theirs={c.theirs_value}"
            )
        raise typer.Exit(1)

    out_path = output or "merged.json"
    tt.save_tree(result.merged_tree, out_path)
    typer.secho(f"Merged tree saved to {out_path}", fg=typer.colors.GREEN)


@app.command("flatten")
def flatten(
    tree_path: str = typer.Argument(..., help="Path to tree JSON file"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Flatten all subtree references into a single tree file."""
    from talking_trees.sdk import TalkingTrees

    tt = TalkingTrees()
    tree = tt.load_tree(tree_path)
    flat = tt.flatten_tree(tree)

    out_path = output or tree_path.replace(".json", "_flat.json")
    tt.save_tree(flat, out_path)
    typer.echo(f"Flattened tree saved to {out_path}")


@app.command("validate")
def validate_tree(
    file: Path | None = typer.Option(
        None, "--file", "-f", help="JSON file to validate"
    ),
    tree_id: str | None = typer.Option(
        None, "--id", help="Tree ID from library to validate"
    ),
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
            console.print("[green] Tree is valid[/green]")
        else:
            console.print("[red][X] Tree has validation errors[/red]")

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
