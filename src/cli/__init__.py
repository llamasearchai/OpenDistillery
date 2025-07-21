from .prompting_commands import prompting
from .commands import ai
import click

def show_banner():
    """Display OpenDistillery banner"""
    print("\n" + "="*60)
    print("  OpenDistillery - Advanced AI Research Platform")
    print("  Enterprise-Grade Compound AI Systems")
    print("="*60 + "\n")

@click.group()
def cli():
    """OpenDistillery - Advanced AI Research Platform"""
    show_banner()

# Register command groups
cli.add_command(ai)
cli.add_command(prompting)

if __name__ == "__main__":
    cli()