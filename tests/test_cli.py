import pytest
from click.testing import CliRunner
from unittest.mock import patch, AsyncMock
from src.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_banner(runner):
    """Test that the main CLI entrypoint shows the banner and help."""
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "OpenDistillery - Advanced AI Research Platform" in result.output
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output

@patch('src.cli.commands.OpenAIInterface')
def test_ai_chat_command(mock_openai_interface, runner):
    """Test the 'ai chat' command with mocking."""
    mock_instance = mock_openai_interface.return_value
    mock_instance.process_with_tools = AsyncMock(return_value={
        "type": "text",
        "response": "Paris is the capital of France."
    })
    
    result = runner.invoke(cli, ['ai', 'chat', '--query', 'What is the capital of France?'])
    
    assert result.exit_code == 0
    assert "AI Response" in result.output
    assert "Paris is the capital of France." in result.output

@patch('src.cli.commands.ShellGPTIntegration')
def test_ai_shell_command(mock_shell_gpt, runner):
    """Test the 'ai shell' command with mocking."""
    mock_instance = mock_shell_gpt.return_value
    mock_instance.execute_shell_command = AsyncMock(return_value={"response": "ls -la"})
    
    result = runner.invoke(cli, ['ai', 'shell', '--command', 'list files'])
    
    assert result.exit_code == 0
    assert "Generated Shell Command" in result.output
    assert "ls -la" in result.output

@patch('src.cli.commands.MetaPromptingEngine')
def test_ai_research_command(mock_meta_engine, runner):
    """Test the 'ai research' command with mocking."""
    mock_instance = mock_meta_engine.return_value
    mock_instance.execute = AsyncMock(return_value={
        "solution": "Quantum computing will have a significant impact.",
        "confidence": 0.95
    })
    
    result = runner.invoke(cli, ['ai', 'research', '--problem', 'quantum computing impact'])
    
    assert result.exit_code == 0
    assert "Research Analysis" in result.output
    assert "Quantum computing will have a significant impact." in result.output

@patch('src.cli.prompting_commands.PromptingStrategies')
def test_prompting_apply_command(mock_strategies, runner):
    """Test the 'prompting apply' command with mocking."""
    mock_strategy = AsyncMock()
    mock_strategy.enhance_prompt = AsyncMock(return_value="[Chain-of-Thought] my test prompt\n\nLet's think step by step:")
    mock_strategies.get_strategy.return_value = mock_strategy
    mock_strategies.get_strategy_map.return_value = {'chain_of_thought': 'Chain-of-Thought'}
    
    result = runner.invoke(cli, ['prompting', 'apply', 'my test prompt', '--technique', 'chain_of_thought'])
    
    assert result.exit_code == 0
    assert "Enhanced Prompt" in result.output
    assert "Chain-of-Thought" in result.output
    assert "my test prompt" in result.output

@patch('src.cli.prompting_commands.PromptingStrategies')
def test_prompting_list_techniques_command(mock_strategies, runner):
    """Test the 'prompting list-techniques' command."""
    mock_strategies.get_strategy_map.return_value = {
        'chain_of_thought': 'Chain-of-Thought',
        'tree_of_thought': 'Tree-of-Thought'
    }
    
    result = runner.invoke(cli, ['prompting', 'list-techniques'])
    assert result.exit_code == 0
    assert "Available Prompting Techniques" in result.output
    assert "chain_of_thought" in result.output 