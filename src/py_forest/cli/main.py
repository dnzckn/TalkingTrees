"""Main CLI entry point for PyForest."""

import typer
from pathlib import Path
from typing import Optional

from py_forest.cli import commands

app = typer.Typer(
    name="pyforest",
    help="PyForest - Behavior Tree Management CLI",
    add_completion=True,
)

# Register command groups
app.add_typer(commands.tree_app, name="tree", help="Tree management commands")
app.add_typer(commands.template_app, name="template", help="Template commands")
app.add_typer(commands.exec_app, name="exec", help="Execution commands")
app.add_typer(commands.export_app, name="export", help="Import/export commands")


@app.command()
def version():
    """Show PyForest version."""
    typer.echo("PyForest version 0.1.0")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set config key (format: key=value)"),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Set API base URL"),
):
    """Manage CLI configuration."""
    from py_forest.cli.config import get_config, save_config

    config_obj = get_config()

    if show:
        typer.echo(f"API URL: {config_obj.api_url}")
        typer.echo(f"Default timeout: {config_obj.timeout}s")
        typer.echo(f"Config file: {config_obj.config_path}")
        return

    if api_url:
        config_obj.api_url = api_url
        save_config(config_obj)
        typer.secho(f"✓ API URL set to: {api_url}", fg=typer.colors.GREEN)

    if set_key:
        if "=" not in set_key:
            typer.secho("Error: Format should be key=value", fg=typer.colors.RED)
            raise typer.Exit(1)

        key, value = set_key.split("=", 1)
        if key == "api_url":
            config_obj.api_url = value
        elif key == "timeout":
            config_obj.timeout = int(value)
        else:
            typer.secho(f"Error: Unknown config key: {key}", fg=typer.colors.RED)
            raise typer.Exit(1)

        save_config(config_obj)
        typer.secho(f"✓ {key} set to: {value}", fg=typer.colors.GREEN)


@app.command()
def profile(
    tree_id: str = typer.Argument(..., help="Tree ID to profile"),
    ticks: int = typer.Option(100, "--ticks", "-t", help="Number of ticks to execute"),
    warmup: int = typer.Option(10, "--warmup", "-w", help="Warmup ticks (not included in stats)"),
):
    """Profile a behavior tree's performance."""
    import time
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from py_forest.cli.client import get_client

    console = Console()

    try:
        client = get_client()

        console.print(f"[cyan]Creating execution for tree {tree_id}...[/cyan]")
        execution = client.create_execution(tree_id)
        exec_id = execution.get("execution_id")

        # Warmup phase
        if warmup > 0:
            console.print(f"\n[yellow]Warming up ({warmup} ticks)...[/yellow]")
            client.tick_execution(exec_id, count=warmup)

        # Profiling phase
        console.print(f"\n[cyan]Profiling ({ticks} ticks)...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Profiling...", total=ticks)

            start_time = time.perf_counter()

            # Execute ticks in batches for better API efficiency
            batch_size = 10
            for i in range(0, ticks, batch_size):
                remaining = min(batch_size, ticks - i)
                client.tick_execution(exec_id, count=remaining)
                progress.update(task, advance=remaining)

            end_time = time.perf_counter()

        total_time = (end_time - start_time) * 1000  # Convert to ms

        # Get statistics
        stats = client.get_statistics(exec_id)

        # Display results
        console.print("\n" + "=" * 70)
        console.print(Panel.fit(
            f"[bold]Tree ID:[/bold] {tree_id}\n"
            f"[bold]Total Ticks:[/bold] {stats.get('total_ticks', 0)}\n"
            f"[bold]Wall Clock Time:[/bold] {total_time:.2f}ms\n"
            f"[bold]Tree Execution Time:[/bold] {stats.get('total_duration_ms', 0):.2f}ms\n"
            f"[bold]Average Tick:[/bold] {stats.get('avg_tick_duration_ms', 0):.4f}ms\n"
            f"[bold]Min Tick:[/bold] {stats.get('min_tick_duration_ms', 0):.4f}ms\n"
            f"[bold]Max Tick:[/bold] {stats.get('max_tick_duration_ms', 0):.4f}ms\n"
            f"[bold]Throughput:[/bold] {(ticks / total_time * 1000):.2f} ticks/sec",
            title="Performance Profile"
        ))

        # Show per-node statistics
        node_stats = stats.get("node_stats", {})
        if node_stats:
            console.print("\n[bold]Top 10 Nodes by Total Duration:[/bold]")
            table = Table()
            table.add_column("Node", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Ticks", style="magenta")
            table.add_column("Avg (ms)", style="yellow")
            table.add_column("Total (ms)", style="red")
            table.add_column("% of Total", style="blue")

            # Sort by total duration
            sorted_nodes = sorted(
                node_stats.items(),
                key=lambda x: x[1].get("total_duration_ms", 0),
                reverse=True
            )[:10]

            total_duration = stats.get('total_duration_ms', 1)

            for node_id, node_stat in sorted_nodes:
                name = node_stat.get("node_name", node_id[:12])
                node_type = node_stat.get("node_type", "N/A")
                tick_count = node_stat.get("tick_count", 0)
                avg_duration = node_stat.get("avg_duration_ms", 0)
                node_total = node_stat.get("total_duration_ms", 0)
                percentage = (node_total / total_duration * 100) if total_duration > 0 else 0

                table.add_row(
                    name,
                    node_type,
                    str(tick_count),
                    f"{avg_duration:.4f}",
                    f"{node_total:.2f}",
                    f"{percentage:.1f}%"
                )

            console.print(table)

        # Cleanup
        client.delete_execution(exec_id)
        console.print(f"\n[dim]Execution {exec_id} cleaned up[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Profiling interrupted[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
