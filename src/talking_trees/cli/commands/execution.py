"""Execution management commands."""

import json
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from talking_trees.cli.client import get_client

app = typer.Typer()
console = Console()


@app.command("list")
def list_executions():
    """List all active executions."""
    try:
        client = get_client()
        executions = client.list_executions()

        if not executions:
            console.print("[yellow]No active executions.[/yellow]")
            return

        table = Table(title="Active Executions")
        table.add_column("Execution ID", style="cyan", no_wrap=True)
        table.add_column("Tree ID", style="green", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Ticks", style="blue")

        for execution in executions:
            exec_id = execution.get("execution_id", "N/A")
            tree_id = execution.get("tree_id", "N/A")
            status = execution.get("root_status", "N/A")
            tick_count = execution.get("tick_count", 0)

            table.add_row(exec_id, tree_id, status, str(tick_count))

        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(executions)} execution(s)")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("run")
def run_tree(
    tree_id: str = typer.Argument(..., help="Tree ID to execute"),
    ticks: int = typer.Option(1, "--ticks", "-t", help="Number of ticks to execute"),
    auto: bool = typer.Option(False, "--auto", help="Run in AUTO mode (continuous)"),
    interval: int | None = typer.Option(
        None, "--interval", "-i", help="Run in INTERVAL mode (milliseconds)"
    ),
    monitor: bool = typer.Option(
        False, "--monitor", "-m", help="Monitor execution in real-time"
    ),
):
    """Execute a behavior tree."""
    try:
        client = get_client()

        # Create execution
        console.print(f"[cyan]Creating execution for tree {tree_id}...[/cyan]")
        execution = client.create_execution(tree_id)
        exec_id = execution.get("execution_id")
        console.print(f"[green] Execution created: {exec_id}[/green]\n")

        if auto:
            # Start AUTO mode
            console.print("[cyan]Starting AUTO mode execution...[/cyan]")
            client.start_auto(exec_id)
            console.print("[green] AUTO mode started[/green]")

            if monitor:
                _monitor_execution(client, exec_id, auto=True)
            else:
                console.print("[yellow]Press Ctrl+C to stop monitoring[/yellow]")
                try:
                    while True:
                        time.sleep(1)
                        stats = client.get_statistics(exec_id)
                        console.print(f"Ticks: {stats.get('total_ticks', 0)}", end="\r")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping execution...[/yellow]")
                    client.stop_scheduler(exec_id)
                    console.print("[green] Execution stopped[/green]")

        elif interval:
            # Start INTERVAL mode
            console.print(f"[cyan]Starting INTERVAL mode ({interval}ms)...[/cyan]")
            client.start_interval(exec_id, interval)
            console.print("[green] INTERVAL mode started[/green]")

            if monitor:
                _monitor_execution(client, exec_id, auto=False)
            else:
                console.print("[yellow]Press Ctrl+C to stop monitoring[/yellow]")
                try:
                    while True:
                        time.sleep(1)
                        stats = client.get_statistics(exec_id)
                        console.print(f"Ticks: {stats.get('total_ticks', 0)}", end="\r")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping execution...[/yellow]")
                    client.stop_scheduler(exec_id)
                    console.print("[green] Execution stopped[/green]")

        else:
            # Manual ticking
            console.print(f"[cyan]Executing {ticks} tick(s)...[/cyan]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Ticking...", total=ticks)

                for i in range(ticks):
                    result = client.tick_execution(
                        exec_id, count=1, capture_snapshot=True
                    )
                    progress.update(task, advance=1)

                    if i == ticks - 1:  # Last tick
                        root_status = result.get("root_status")
                        console.print(f"\n[bold]Final Status:[/bold] {root_status}")

            # Show statistics
            _show_statistics(client, exec_id)

    except KeyboardInterrupt:
        console.print("\n[yellow]Execution interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("tick")
def tick_execution(
    execution_id: str = typer.Argument(..., help="Execution ID to tick"),
    count: int = typer.Option(1, "--count", "-c", help="Number of ticks"),
):
    """Manually tick an existing execution."""
    try:
        client = get_client()

        console.print(f"[cyan]Ticking execution {count} time(s)...[/cyan]")
        result = client.tick_execution(execution_id, count=count, capture_snapshot=True)

        ticks_executed = result.get("ticks_executed", 0)
        root_status = result.get("root_status")

        console.print(f"[green] Executed {ticks_executed} tick(s)[/green]")
        console.print(f"[bold]Root Status:[/bold] {root_status}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("stop")
def stop_execution(
    execution_id: str = typer.Argument(..., help="Execution ID to stop"),
):
    """Stop a scheduled execution."""
    try:
        client = get_client()

        console.print(f"[cyan]Stopping execution {execution_id}...[/cyan]")
        client.stop_scheduler(execution_id)

        console.print("[green] Execution stopped[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_execution(
    execution_id: str = typer.Argument(..., help="Execution ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an execution instance."""
    try:
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete execution {execution_id}?"
            )
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)

        client = get_client()
        client.delete_execution(execution_id)

        console.print(f"[green] Execution {execution_id} deleted[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("snapshot")
def get_snapshot(
    execution_id: str = typer.Argument(..., help="Execution ID"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save to file"),
):
    """Get current snapshot of an execution."""
    try:
        client = get_client()
        snapshot = client.get_snapshot(execution_id)

        if output:
            with open(output, "w") as f:
                json.dump(snapshot, f, indent=2)
            console.print(f"[green] Snapshot saved to {output}[/green]")
        else:
            console.print(
                Panel.fit(
                    f"[bold]Tree:[/bold] {snapshot.get('tree', {}).get('tree_id', 'N/A')}\n"
                    f"[bold]Tick Count:[/bold] {snapshot.get('tick_count', 0)}\n"
                    f"[bold]Root Status:[/bold] {snapshot.get('tree', {}).get('root', {}).get('status', 'N/A')}\n"
                    f"[bold]Node States:[/bold] {len(snapshot.get('node_states', []))} node(s)",
                    title="Execution Snapshot",
                )
            )

            # Show blackboard
            blackboard = snapshot.get("blackboard", {})
            if blackboard:
                console.print("\n[bold]Blackboard:[/bold]")
                for key, value in blackboard.items():
                    console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("stats")
def show_statistics(
    execution_id: str = typer.Argument(..., help="Execution ID"),
):
    """Show execution statistics."""
    try:
        client = get_client()
        _show_statistics(client, execution_id)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _show_statistics(client, execution_id: str):
    """Helper to display execution statistics."""
    stats = client.get_statistics(execution_id)

    console.print(
        Panel.fit(
            f"[bold]Total Ticks:[/bold] {stats.get('total_ticks', 0)}\n"
            f"[bold]Total Duration:[/bold] {stats.get('total_duration_ms', 0):.2f}ms\n"
            f"[bold]Average Tick:[/bold] {stats.get('avg_tick_duration_ms', 0):.2f}ms\n"
            f"[bold]Min Tick:[/bold] {stats.get('min_tick_duration_ms', 0):.2f}ms\n"
            f"[bold]Max Tick:[/bold] {stats.get('max_tick_duration_ms', 0):.2f}ms",
            title="Execution Statistics",
        )
    )

    # Show per-node stats
    node_stats = stats.get("node_stats", {})
    if node_stats:
        console.print("\n[bold]Top 10 Nodes by Duration:[/bold]")
        table = Table()
        table.add_column("Node", style="cyan")
        table.add_column("Ticks", style="green")
        table.add_column("Avg Duration", style="magenta")
        table.add_column("Total Duration", style="yellow")

        # Sort by total duration
        sorted_nodes = sorted(
            node_stats.items(),
            key=lambda x: x[1].get("total_duration_ms", 0),
            reverse=True,
        )[:10]

        for node_id, node_stat in sorted_nodes:
            name = node_stat.get("node_name", node_id[:8])
            tick_count = node_stat.get("tick_count", 0)
            avg_duration = node_stat.get("avg_duration_ms", 0)
            total_duration = node_stat.get("total_duration_ms", 0)

            table.add_row(
                name,
                str(tick_count),
                f"{avg_duration:.2f}ms",
                f"{total_duration:.2f}ms",
            )

        console.print(table)


def _monitor_execution(client, execution_id: str, auto: bool = False):
    """Monitor execution in real-time."""
    console.print("\n[bold cyan]Monitoring Execution[/bold cyan]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

    try:
        while True:
            stats = client.get_statistics(execution_id)
            execution = client.get_execution(execution_id)

            total_ticks = stats.get("total_ticks", 0)
            root_status = execution.get("root_status", "N/A")
            avg_tick = stats.get("avg_tick_duration_ms", 0)

            console.print(
                f"[bold]Ticks:[/bold] {total_ticks:6d} | "
                f"[bold]Status:[/bold] {root_status:10s} | "
                f"[bold]Avg:[/bold] {avg_tick:6.2f}ms",
                end="\r",
            )

            time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Stopping execution...[/yellow]")
        client.stop_scheduler(execution_id)
        console.print("[green] Execution stopped[/green]")
