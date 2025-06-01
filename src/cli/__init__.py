from .enhanced_cli import theme, spinner
from .prompting_commands import prompting
from .commands import ai
import click

@click.group()
def cli():
    """🧪 OpenDistillery - Advanced AI Research Platform"""
    theme.show_banner()

# Register command groups
cli.add_command(ai)
cli.add_command(prompting)

if __name__ == "__main__":
    cli()