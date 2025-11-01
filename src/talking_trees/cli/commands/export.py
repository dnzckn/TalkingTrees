"""Import/export commands."""

import json
from pathlib import Path

import typer
from rich.console import Console

from talking_trees.cli.client import get_client

app = typer.Typer()
console = Console()


@app.command("tree")
def export_tree(
    tree_id: str = typer.Argument(..., help="Tree ID to export"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format (json, yaml)"
    ),
):
    """Export a tree from the library."""
    try:
        client = get_client()
        tree = client.get_tree(tree_id)

        if format == "json":
            with open(output, "w") as f:
                json.dump(tree, f, indent=2)
        elif format == "yaml":
            try:
                import yaml

                with open(output, "w") as f:
                    yaml.dump(tree, f, default_flow_style=False, sort_keys=False)
            except ImportError:
                console.print(
                    "[red]Error: PyYAML not installed. Install with: pip install pyyaml[/red]"
                )
                raise typer.Exit(1)
        else:
            console.print(f"[red]Error: Unsupported format: {format}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Tree exported to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("import")
def import_tree(
    file: Path = typer.Argument(..., help="File to import"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Import format (json, yaml)"
    ),
):
    """Import a tree into the library."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)

        # Load tree definition
        if format == "json":
            with open(file) as f:
                tree_def = json.load(f)
        elif format == "yaml":
            try:
                import yaml

                with open(file) as f:
                    tree_def = yaml.safe_load(f)
            except ImportError:
                console.print(
                    "[red]Error: PyYAML not installed. Install with: pip install pyyaml[/red]"
                )
                raise typer.Exit(1)
        else:
            console.print(f"[red]Error: Unsupported format: {format}[/red]")
            raise typer.Exit(1)

        # Create tree
        client = get_client()
        created_tree = client.create_tree(tree_def)

        console.print("[green]✓ Tree imported successfully[/green]")
        console.print(f"[bold]Tree ID:[/bold] {created_tree.get('tree_id')}")
        console.print(
            f"[bold]Name:[/bold] {created_tree.get('metadata', {}).get('name')}"
        )

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("dot")
def export_dot(
    execution_id: str = typer.Argument(..., help="Execution ID to export"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path"),
    render: bool = typer.Option(
        False, "--render", "-r", help="Render to image (requires graphviz)"
    ),
):
    """Export execution as DOT graph."""
    try:
        client = get_client()
        dot_source = client.get_dot_graph(execution_id)

        # Save DOT source
        with open(output, "w") as f:
            f.write(dot_source)

        console.print(f"[green]✓ DOT graph exported to {output}[/green]")

        # Render if requested
        if render:
            try:
                from graphviz import Source

                output_image = output.with_suffix(".png")
                src = Source(dot_source)
                src.render(
                    output.stem, directory=output.parent, format="png", cleanup=True
                )

                console.print(f"[green]✓ Image rendered to {output_image}[/green]")

            except ImportError:
                console.print(
                    "[yellow]Warning: graphviz not installed. Install with: pip install graphviz[/yellow]"
                )
            except Exception as e:
                console.print(f"[yellow]Warning: Could not render image: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("batch")
def batch_export(
    output_dir: Path = typer.Option(..., "--output", "-o", help="Output directory"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format (json, yaml)"
    ),
):
    """Export all trees from the library."""
    try:
        client = get_client()
        trees = client.list_trees()

        if not trees:
            console.print("[yellow]No trees to export.[/yellow]")
            return

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_count = 0
        for tree in trees:
            tree_id = tree.get("tree_id")
            metadata = tree.get("metadata", {})
            name = metadata.get("name", tree_id)

            # Sanitize filename
            filename = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name
            )
            filename = f"{filename}.{format}"
            output_file = output_dir / filename

            # Export
            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(tree, f, indent=2)
            elif format == "yaml":
                try:
                    import yaml

                    with open(output_file, "w") as f:
                        yaml.dump(tree, f, default_flow_style=False, sort_keys=False)
                except ImportError:
                    console.print(
                        "[red]Error: PyYAML not installed. Install with: pip install pyyaml[/red]"
                    )
                    raise typer.Exit(1)

            exported_count += 1

        console.print(
            f"[green]✓ Exported {exported_count} tree(s) to {output_dir}[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("batch-import")
def batch_import(
    input_dir: Path = typer.Argument(..., help="Directory containing tree files"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Import format (json, yaml)"
    ),
):
    """Import all trees from a directory."""
    try:
        if not input_dir.exists() or not input_dir.is_dir():
            console.print(f"[red]Error: Directory not found: {input_dir}[/red]")
            raise typer.Exit(1)

        # Find tree files
        pattern = f"*.{format}"
        files = list(input_dir.glob(pattern))

        if not files:
            console.print(f"[yellow]No {format} files found in {input_dir}[/yellow]")
            return

        client = get_client()
        imported_count = 0
        errors = []

        for file in files:
            try:
                # Load tree definition
                if format == "json":
                    with open(file) as f:
                        tree_def = json.load(f)
                elif format == "yaml":
                    try:
                        import yaml

                        with open(file) as f:
                            tree_def = yaml.safe_load(f)
                    except ImportError:
                        console.print(
                            "[red]Error: PyYAML not installed. Install with: pip install pyyaml[/red]"
                        )
                        raise typer.Exit(1)

                # Create tree
                client.create_tree(tree_def)
                imported_count += 1
                console.print(f"[green]✓ Imported: {file.name}[/green]")

            except Exception as e:
                errors.append(f"{file.name}: {e}")
                console.print(f"[red]✗ Failed: {file.name}[/red]")

        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  [green]Imported: {imported_count}[/green]")
        if errors:
            console.print(f"  [red]Failed: {len(errors)}[/red]")
            console.print("\n[bold]Errors:[/bold]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
