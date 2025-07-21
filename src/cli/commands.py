import click
from rich.console import Console
from rich.panel import Panel
from ..integrations.openai_integration import OpenAIInterface, ShellGPTIntegration
from ..research.techniques.prompting_plugins.meta_prompting import MetaPromptingEngine
import asyncio

console = Console()

@click.group()
def ai():
    """AI-powered commands and interactions."""
    pass

async def _run_async(coroutine):
    """Helper to run asyncio coroutines."""
    try:
        await coroutine
    except Exception as e:
        console.print(Panel(f"An error occurred: {e}", title="Error", border_style="red"))

@ai.command()
@click.option('--query', '-q', prompt='Your question', help='Natural language query for the AI.')
@click.option('--stream', is_flag=True, help='Stream the response in real-time.')
def chat(query, stream):
    """Interactive AI chat with OpenDistillery."""
    console.print(Panel.fit(f"Query: {query}", title="AI Chat", border_style="cyan"))
    
    if stream:
        asyncio.run(_run_async(_stream_chat(query)))
    else:
        asyncio.run(_run_async(_standard_chat(query)))

async def _stream_chat(query):
    """Streams the chat response."""
    interface = OpenAIInterface()
    context = {"messages": [{"role": "user", "content": query}], "system_prompt": "You are an expert AI research assistant."}
    
    async for chunk in interface.chat_completion_stream(context):
        console.print(chunk, end="")
    console.print()

async def _standard_chat(query):
    """Handles standard, non-streamed chat."""
    interface = OpenAIInterface()
    result = await interface.process_with_tools(query)
    
    if result.get("type") == "function_calls":
        console.print("Function calls executed:", style="bold yellow")
        for tool_result in result.get("tool_results", []):
            console.print(f"  - {tool_result.get('function')}: {tool_result.get('result')}")
    else:
        console.print(Panel(result.get("response", "No response."), title="AI Response", border_style="green"))

@ai.command()
@click.option('--command', '-c', prompt='Describe the task for the shell', help='Natural language description of a shell command.')
def shell(command):
    """Converts natural language to shell commands."""
    console.print(Panel.fit(f"Task: {command}", title="Shell Command Conversion", border_style="yellow"))
    asyncio.run(_run_async(_execute_shell_gpt(command)))

async def _execute_shell_gpt(command):
    """Executes the ShellGPT integration."""
    shell_gpt = ShellGPTIntegration()
    result = await shell_gpt.execute_shell_command(command)
    console.print(Panel(result.get("response", "No command generated."), title="Generated Shell Command", border_style="green"))

@ai.command()
@click.option('--problem', '-p', prompt='Research problem', help='A complex problem for the AI to analyze.')
@click.option('--technique', '-t', type=click.Choice(['meta_prompting']), default='meta_prompting', help='The research technique to use.')
def research(problem, technique):
    """Executes advanced AI research techniques."""
    console.print(Panel.fit(f"Problem: {problem}\nTechnique: {technique}", title="Research Analysis", border_style="magenta"))
    asyncio.run(_run_async(_execute_research(problem, technique)))

async def _execute_research(problem, technique):
    """Executes the specified research technique."""
    if technique == "meta_prompting":
        engine = MetaPromptingEngine()
        result = await engine.execute({"problem": problem})
        
        console.print(Panel(result.get("solution", "No solution found."), title=f"Solution (Confidence: {result.get('confidence', 0):.2%})", border_style="green"))
        if "visualization" in result:
            console.print(result["visualization"])
        console.print(Panel(result.get("meta_analysis", "No meta-analysis available."), title="Meta-Analysis", border_style="blue"))