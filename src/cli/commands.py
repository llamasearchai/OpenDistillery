import click
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from ..integrations.openai_integration import OpenAIInterface, ShellGPTIntegration
from ..research.techniques.prompting_plugins.meta_prompting import MetaPromptingEngine

console = Console()

@click.group()
def ai():
    """AI-powered commands and interactions"""
    pass

@ai.command()
@click.option('--query', '-q', prompt='Your question', help='Natural language query')
@click.option('--stream', is_flag=True, help='Stream response in real-time')
def chat(query, stream):
    """Interactive AI chat with OpenDistillery"""
    
    if stream:
        console.print(Panel.fit("AI Response (Streaming):", border_style="cyan"))
        asyncio.run(_stream_chat(query))
    else:
        console.print(Panel.fit("AI Response:", border_style="cyan"))
        asyncio.run(_standard_chat(query))

async def _stream_chat(query):
    """Stream chat response"""
    from ..integrations.openai_integration import ConversationContext
    
    interface = OpenAIInterface()
    context = ConversationContext(
        messages=[{"role": "user", "content": query}],
        system_prompt="You are an expert AI research assistant."
    )
    
    async for chunk in interface.chat_completion_stream(context):
        console.print(chunk, end="", style="ai")
    console.print()  # New line at end

async def _standard_chat(query):
    """Standard chat response"""
    interface = OpenAIInterface()
    result = await interface.process_with_tools(query)
    
    if result["type"] == "text":
        console.print(result["response"], style="ai")
    elif result["type"] == "function_calls":
        console.print(" Function calls executed:", style="warning")
        for tool_result in result["tool_results"]:
            console.print(f"  {tool_result['function']}: {tool_result['result']}")

@ai.command()
@click.option('--command', '-c', prompt='Describe what you want to do', 
              help='Natural language command description')
def shell(command):
    """Convert natural language to shell commands"""
    
    console.print(Panel.fit(f"🐚 Converting: {command}", border_style="yellow"))
    asyncio.run(_execute_shell_gpt(command))

async def _execute_shell_gpt(command):
    """Execute shell-gpt integration"""
    shell_gpt = ShellGPTIntegration()
    result = await shell_gpt.execute_shell_command(command)
    
    console.print(Panel.fit(
        result.get("response", "No response generated"),
        title="Generated Shell Commands",
        border_style="green"
    ))

@click.command()
@click.option('--problem', '-p', prompt='Research problem', 
              help='Complex problem to analyze')
@click.option('--technique', '-t', 
              type=click.Choice(['meta_prompting', 'tree_of_thoughts', 'chain_of_density']),
              default='meta_prompting')
def research(problem, technique):
    """Execute advanced research techniques"""
    
    console.print(Panel.fit(
                    f"Analyzing: {problem}\nUsing: {technique}",
        title="Research Analysis",
        border_style="magenta"
    ))
    
    asyncio.run(_execute_research(problem, technique))

async def _execute_research(problem, technique):
    """Execute research analysis"""
    
    if technique == "meta_prompting":
        engine = MetaPromptingEngine()
        result = await engine.execute({"problem": problem})
        
        console.print(Panel.fit(
            result["solution"],
            title=f"Solution (Confidence: {result['confidence']:.2%})",
            border_style="green"
        ))
        
        console.print(result["visualization"])
        
        console.print(Panel.fit(
            result["meta_analysis"],
            title="Meta-Analysis",
            border_style="blue"
        ))