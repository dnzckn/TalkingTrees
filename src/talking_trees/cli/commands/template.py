"""Template management commands."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

from talking_trees.cli.client import get_client

app = typer.Typer()
console = Console()


@app.command("list")
def list_templates():
    """List all available templates."""
    try:
        client = get_client()
        templates = client.list_templates()

        if not templates:
            console.print("[yellow]No templates found.[/yellow]")
            return

        table = Table(title="Behavior Tree Templates")
        table.add_column("Template ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Category", style="magenta")
        table.add_column("Parameters", style="blue")

        for template in templates:
            template_id = template.get("template_id", "N/A")
            name = template.get("name", "N/A")
            category = template.get("category", "N/A")
            params = template.get("parameters", [])
            param_count = f"{len(params)} param(s)"

            table.add_row(template_id, name, category, param_count)

        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(templates)} template(s)")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_template(
    template_id: str = typer.Argument(..., help="Template ID to retrieve"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save to file"),
    show_json: bool = typer.Option(False, "--json", help="Show raw JSON"),
):
    """Get details of a specific template."""
    try:
        client = get_client()
        template = client.get_template(template_id)

        if output:
            with open(output, "w") as f:
                json.dump(template, f, indent=2)
            console.print(f"[green] Template saved to {output}[/green]")
            return

        if show_json:
            syntax = Syntax(json.dumps(template, indent=2), "json", theme="monokai")
            console.print(syntax)
        else:
            console.print(
                Panel.fit(
                    f"[bold cyan]{template.get('name', 'N/A')}[/bold cyan]\n\n"
                    f"[bold]ID:[/bold] {template.get('template_id', 'N/A')}\n"
                    f"[bold]Category:[/bold] {template.get('category', 'N/A')}\n"
                    f"[bold]Description:[/bold] {template.get('description', 'N/A')}\n"
                    f"[bold]Tags:[/bold] {', '.join(template.get('tags', []))}",
                    title="Template Details",
                )
            )

            # Show parameters
            params = template.get("parameters", [])
            if params:
                console.print("\n[bold]Parameters:[/bold]")
                param_table = Table()
                param_table.add_column("Name", style="cyan")
                param_table.add_column("Type", style="green")
                param_table.add_column("Required", style="magenta")
                param_table.add_column("Default", style="yellow")

                for param in params:
                    name = param.get("name", "N/A")
                    param_type = param.get("type", "N/A")
                    required = "Yes" if param.get("required", False) else "No"
                    default = str(param.get("default", "-"))

                    param_table.add_row(name, param_type, required, default)

                console.print(param_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_template(
    file: Path = typer.Argument(..., help="JSON file containing template definition"),
):
    """Create a new template from a JSON file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)

        with open(file) as f:
            template_def = json.load(f)

        client = get_client()
        created_template = client.create_template(template_def)

        console.print("[green] Template created successfully[/green]")
        console.print(
            f"[bold]Template ID:[/bold] {created_template.get('template_id')}"
        )
        console.print(f"[bold]Name:[/bold] {created_template.get('name')}")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in file: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("instantiate")
def instantiate_template(
    template_id: str = typer.Argument(..., help="Template ID to instantiate"),
    tree_name: str = typer.Option(..., "--name", "-n", help="Name for the new tree"),
    params_file: Path | None = typer.Option(
        None, "--params", "-p", help="JSON file with parameters"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Prompt for parameters interactively"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Save tree to file instead of uploading"
    ),
):
    """Instantiate a tree from a template."""
    try:
        client = get_client()

        # Get template to see parameters
        template = client.get_template(template_id)
        template_params = template.get("parameters", [])

        # Load or collect parameters
        params = {}

        if params_file:
            with open(params_file) as f:
                params = json.load(f)
        elif interactive:
            console.print(
                f"[bold]Creating tree from template: {template.get('name')}[/bold]\n"
            )
            for param in template_params:
                param_name = param.get("name")
                param_type = param.get("type")
                required = param.get("required", False)
                default = param.get("default")
                description = param.get("description", "")

                prompt_text = f"{param_name} ({param_type})"
                if description:
                    prompt_text += f" - {description}"

                if not required and default is not None:
                    prompt_text += f" [default: {default}]"

                value = Prompt.ask(
                    prompt_text, default=str(default) if default is not None else ""
                )

                # Type conversion
                if value:
                    if param_type == "int":
                        params[param_name] = int(value)
                    elif param_type == "float":
                        params[param_name] = float(value)
                    elif param_type == "bool":
                        params[param_name] = value.lower() in ("true", "yes", "1")
                    else:
                        params[param_name] = value
        else:
            # Use example params or defaults
            params = template.get("example_params", {})

        # Instantiate template
        tree_def = client.instantiate_template(template_id, params, tree_name)

        if output:
            with open(output, "w") as f:
                json.dump(tree_def, f, indent=2)
            console.print(f"[green] Tree saved to {output}[/green]")
        else:
            # Upload to library
            created_tree = client.create_tree(tree_def)
            console.print("[green] Tree created from template[/green]")
            console.print(f"[bold]Tree ID:[/bold] {created_tree.get('tree_id')}")
            console.print(
                f"[bold]Name:[/bold] {created_tree.get('metadata', {}).get('name')}"
            )

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error: Invalid parameter value: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
