"""
OpenDistillery Prompting Commands

Advanced prompting techniques and optimization tools.
"""

import click
from rich.console import Console
from rich.panel import Panel
from ..research.techniques.prompting_strategies import PromptingStrategies
import asyncio

console = Console()

@click.group()
def prompting():
    """Advanced prompting techniques and utilities."""
    pass

async def _run_async(coroutine):
    """Helper to run asyncio coroutines."""
    try:
        await coroutine
    except Exception as e:
        console.print(Panel(f"An error occurred: {e}", title="Error", border_style="red"))

@prompting.command()
@click.argument('prompt')
@click.option('--technique', '-t', 
              type=click.Choice(list(PromptingStrategies.get_strategy_map().keys())), 
              default='chain_of_thought', 
              help='The prompting technique to apply.')
def apply(prompt, technique):
    """Applies a specified prompting technique to a prompt."""
    console.print(Panel(f"Applying [bold cyan]{technique}[/] to prompt:\n[yellow]{prompt}[/yellow]", 
                        title="Prompt Enhancement", border_style="blue"))
    asyncio.run(_run_async(_apply_technique_async(prompt, technique)))

async def _apply_technique_async(prompt, technique):
    """Asynchronously applies a prompting technique."""
    strategy = PromptingStrategies.get_strategy(technique)
    if not strategy:
        console.print(Panel(f"Unknown technique: {technique}", title="Error", border_style="red"))
        return

    enhanced_prompt = await strategy.enhance_prompt(prompt)
    console.print(Panel(enhanced_prompt, title=f"Enhanced Prompt ({technique})", border_style="green"))

@prompting.command(name='list-techniques')
def list_techniques():
    """Lists all available prompting techniques."""
    console.print(Panel("Available Prompting Techniques", title="Prompting Library", border_style="magenta"))
    for key, name in PromptingStrategies.get_strategy_map().items():
        console.print(f"- [bold cyan]{key}[/]: {name}")