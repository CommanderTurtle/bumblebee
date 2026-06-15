"""
Jellyfin server setup module for bumblebee-bootstrap.

Manages Docker Compose file generation, Jellyfin container startup,
lyrics plugin installation guidance, and user-friendly setup instructions.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from bootstrap.console import console
from bootstrap.models import LibraryConfig
from rich.panel import Panel


def write_docker_compose(config: LibraryConfig) -> None:
    """
    Write a docker-compose.yml file for Jellyfin in the current directory.

    Args:
        config: LibraryConfig containing the output and jellyfin data directories.
    """
    compose_content = f"""version: "3.8"
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin-bumblebee
    ports:
      - "8096:8096"
    volumes:
      - {config.jellyfin_data_dir}:/config
      - {config.output_dir}:/media:ro
    restart: unless-stopped
"""

    compose_path = Path("docker-compose.yml")
    try:
        compose_path.write_text(compose_content, encoding="utf-8")
        console.print(f"[green]Docker Compose file written:[/green] {compose_path.resolve()}")
    except OSError as exc:
        console.print(f"[yellow]Warning:[/yellow] Could not write docker-compose.yml: {exc}")


def start_jellyfin(config: LibraryConfig) -> None:
    """
    Start the Jellyfin Docker container using docker compose.

    Args:
        config: LibraryConfig (used for potential future configuration).
    """
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            console.print("[green]Jellyfin container started successfully![/green]")
        else:
            console.print(f"[yellow]Warning:[/yellow] Docker compose output: {result.stderr}")
    except FileNotFoundError:
        console.print("[yellow]Docker not found. Please install Docker to run Jellyfin.[/yellow]")
    except subprocess.TimeoutExpired:
        console.print("[yellow]Docker compose timed out. You may need to start it manually.[/yellow]")
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Could not start Jellyfin: {exc}")


def install_lyrics_plugin(config: LibraryConfig) -> None:
    """
    Print instructions for installing the Jellyfin lyrics plugin.

    Automatic plugin installation requires authentication, so we provide
clear manual instructions instead.

    Args:
        config: LibraryConfig (reserved for future use).
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Jellyfin Lyrics Plugin — Manual Installation Required[/bold cyan]\n\n"
        "The lyrics plugin must be installed manually through the Jellyfin web UI:\n\n"
        "1. Open [link=http://localhost:8096]http://localhost:8096[/link]\n"
        "2. Log in with your Jellyfin admin account\n"
        "3. Go to [bold]Dashboard → Plugins → Catalog[/bold]\n"
        "4. Search for [bold]'Lyrics'[/bold]\n"
        "5. Install the [bold]LRC Lyrics[/bold] plugin\n"
        "6. Restart Jellyfin from the dashboard\n\n"
        "Plugin repository URL (for manual addition):\n"
        "[link=https://raw.githubusercontent.com/Felitendo/jellyfin-plugin-lyrics/master/manifest.json]"
        "https://raw.githubusercontent.com/Felitendo/jellyfin-plugin-lyrics/master/manifest.json"
        "[/link]",
        title="🎵 Lyrics Plugin",
        border_style="cyan",
    ))


def print_jellyfin_guide() -> None:
    """Print a user-friendly Jellyfin setup guide."""
    guide = """
[bold green]Jellyfin is now running![/bold green]

[bold]Quick Start Guide:[/bold]
1. Open your browser and go to: [link=http://localhost:8096]http://localhost:8096[/link]
2. Follow the initial setup wizard to create an admin account
3. Add a music library:
   - Click [bold]Libraries → Add Library[/bold]
   - Select [bold]Music[/bold]
   - Set the folder to [bold]/media[/bold] (mounted from your organized library)
   - Enable metadata downloaders and lyric fetchers
4. Install the LRC Lyrics plugin for synced lyrics support
5. Scan your library and enjoy your organized music!

[bold]Useful Commands:[/bold]
  [dim]docker logs -f jellyfin-bumblebee[/dim]  # View Jellyfin logs
  [dim]docker stop jellyfin-bumblebee[/dim]     # Stop Jellyfin
  [dim]docker start jellyfin-bumblebee[/dim]    # Start Jellyfin

[bold]Plugin Repository:[/bold]
  https://raw.githubusercontent.com/Felitendo/jellyfin-plugin-lyrics/master/manifest.json
"""
    console.print(guide)



