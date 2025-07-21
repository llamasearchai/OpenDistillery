from .prompting_commands import prompting
from .commands import ai
import click

def show_banner():
    """Displays the OpenDistillery banner."""
    banner = """
    ============================================================
      OpenDistillery - Advanced AI Research Platform
      Enterprise-Grade Compound AI Systems
    ============================================================
    """
    click.echo(banner)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """OpenDistillery - Advanced AI Research Platform."""
    if ctx.invoked_subcommand is None:
        show_banner()
        click.echo(ctx.get_help())

# Register command groups
cli.add_command(ai)
cli.add_command(prompting)

if __name__ == "__main__":
    cli()