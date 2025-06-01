"""
OpenDistillery Command Line Interface
Production-ready CLI for managing OpenDistillery systems, experiments, and deployments.
"""

import asyncio
import click
import json
import yaml
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .core.compound_system import SystemBuilder, SystemRequirements, SystemArchitecture, ModelConfiguration
from .agents.base_agent import BaseAgent, AgentCapability, SpecializedAgent
from .agents.orchestrator import AgentOrchestrator
from .research.experiment_runner import ExperimentRunner, ExperimentConfiguration
from .api.enterprise_api import EnterpriseAPI
from .integrations.salesforce_integration import SalesforceAIIntegration, SalesforceConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="1.0.0")
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """OpenDistillery: Advanced Compound AI Systems for Enterprise Workflow Transformation"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    if config:
        with open(config, 'r') as f:
            if config.endswith('.yaml') or config.endswith('.yml'):
                ctx.obj['config'] = yaml.safe_load(f)
            else:
                ctx.obj['config'] = json.load(f)
    else:
        ctx.obj['config'] = {}

@cli.group()
def system():
    """System management commands"""
    pass

@system.command()
@click.option('--system-id', required=True, help='Unique system identifier')
@click.option('--domain', required=True, help='Business domain (finance, healthcare, etc.)')
@click.option('--use-case', required=True, help='Specific use case description')
@click.option('--architecture', default='hybrid', type=click.Choice(['hierarchical', 'mesh', 'pipeline', 'hybrid', 'swarm']))
@click.option('--latency-target', default=1000, type=int, help='Latency target in milliseconds')
@click.option('--throughput-rps', default=100, type=int, help='Throughput target in requests per second')
@click.option('--accuracy-threshold', default=0.95, type=float, help='Accuracy threshold (0-1)')
@click.pass_context
def create(ctx, system_id, domain, use_case, architecture, latency_target, throughput_rps, accuracy_threshold):
    """Create a new compound AI system"""
    try:
        # Create system requirements
        requirements = SystemRequirements(
            domain=domain,
            use_case=use_case,
            latency_target_ms=latency_target,
            throughput_rps=throughput_rps,
            accuracy_threshold=accuracy_threshold
        )
        
        # Create system
        system_builder = SystemBuilder()
        system = system_builder.create_system(
            system_id=system_id,
            requirements=requirements,
            architecture=SystemArchitecture(architecture)
        )
        
        click.echo(f"Created compound AI system: {system_id}")
        click.echo(f"   Domain: {domain}")
        click.echo(f"   Use Case: {use_case}")
        click.echo(f"   Architecture: {architecture}")
        click.echo(f"   Performance Targets: {latency_target}ms latency, {throughput_rps} RPS")
        
        # Save system configuration
        config_path = Path(f"systems/{system_id}.json")
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump({
                "system_id": system_id,
                "requirements": requirements.__dict__,
                "architecture": architecture,
                "created_at": system.performance_metrics.get("created_at", "unknown")
            }, f, indent=2)
        
        click.echo(f"   Configuration saved to: {config_path}")
        
    except Exception as e:
        click.echo(f"Error creating system: {str(e)}", err=True)
        sys.exit(1)

@system.command()
@click.option('--system-id', required=True, help='System identifier')
@click.option('--model-name', required=True, help='Model name')
@click.option('--provider', required=True, type=click.Choice(['openai', 'anthropic', 'google', 'local_mlx']))
@click.option('--model-id', required=True, help='Provider-specific model ID')
@click.option('--api-key', help='API key for the provider')
@click.option('--max-tokens', default=4096, type=int, help='Maximum tokens')
@click.option('--temperature', default=0.7, type=float, help='Temperature setting')
@click.option('--cost-per-token', default=0.0, type=float, help='Cost per token')
def add_model(system_id, model_name, provider, model_id, api_key, max_tokens, temperature, cost_per_token):
    """Add a model to an existing system"""
    try:
        system_builder = SystemBuilder()
        system = system_builder.get_system(system_id)
        
        if not system:
            click.echo(f"System {system_id} not found", err=True)
            sys.exit(1)
        
        # Create model configuration
        model_config = ModelConfiguration(
            model_name=model_name,
            provider=provider,
            model_id=model_id,
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
            cost_per_token=cost_per_token
        )
        
        # Add model to system
        system.add_model(model_config)
        
        click.echo(f"Added model {model_name} to system {system_id}")
        click.echo(f"   Provider: {provider}")
        click.echo(f"   Model ID: {model_id}")
        click.echo(f"   Max Tokens: {max_tokens}")
        
    except Exception as e:
        click.echo(f"Error adding model: {str(e)}", err=True)
        sys.exit(1)

@system.command()
def list():
    """List all created systems"""
    try:
        system_builder = SystemBuilder()
        systems = system_builder.list_systems()
        
        if not systems:
            click.echo("No systems found")
            return
        
        click.echo("OpenDistillery Systems:")
        click.echo("=" * 50)
        
        for system_id in systems:
            system = system_builder.get_system(system_id)
            status = system.get_system_status()
            
            click.echo(f"{system_id}")
            click.echo(f"   Domain: {status['requirements']['domain']}")
            click.echo(f"   Use Case: {status['requirements']['use_case']}")
            click.echo(f"   Architecture: {status['architecture']}")
            click.echo(f"   Models: {status['models']['count']}")
            click.echo(f"   Health: {status['health']['overall']}")
            click.echo()
        
    except Exception as e:
        click.echo(f"Error listing systems: {str(e)}", err=True)

@system.command()
@click.option('--system-id', required=True, help='System identifier')
def status(system_id):
    """Get detailed status of a system"""
    try:
        system_builder = SystemBuilder()
        system = system_builder.get_system(system_id)
        
        if not system:
            click.echo(f"System {system_id} not found", err=True)
            sys.exit(1)
        
        status = system.get_system_status()
        
        click.echo(f"System Status: {system_id}")
        click.echo("=" * 50)
        click.echo(f"Architecture: {status['architecture']}")
        click.echo(f"Domain: {status['requirements']['domain']}")
        click.echo(f"Use Case: {status['requirements']['use_case']}")
        click.echo()
        
        click.echo("Models:")
        click.echo(f"  Count: {status['models']['count']}")
        click.echo(f"  Providers: {', '.join(status['models']['providers'])}")
        click.echo(f"  Models: {', '.join(status['models']['models'])}")
        click.echo()
        
        click.echo("Performance:")
        perf = status['performance']
        click.echo(f"  Requests Processed: {perf['requests_processed']}")
        click.echo(f"  Average Latency: {perf['average_latency']:.3f}s")
        click.echo(f"  Success Rate: {perf['success_rate']:.1%}")
        click.echo(f"  Total Cost: ${perf['total_cost']:.4f}")
        click.echo()
        
        click.echo("Health:")
        health = status['health']
        click.echo(f"  Overall: {health['overall']}")
        click.echo(f"  Latency SLA Met: {health['latency_sla_met']}")
        click.echo(f"  Success Rate Acceptable: {health['success_rate_acceptable']}")
        click.echo(f"  Models Operational: {health['models_operational']}")
        
    except Exception as e:
        click.echo(f"Error getting system status: {str(e)}", err=True)

@cli.group()
def agent():
    """Agent management commands"""
    pass

@agent.command()
@click.option('--agent-id', required=True, help='Unique agent identifier')
@click.option('--agent-type', required=True, help='Agent type')
@click.option('--specialization', help='Agent specialization')
@click.option('--capabilities', multiple=True, help='Agent capabilities')
def create_agent(agent_id, agent_type, specialization, capabilities):
    """Create a new specialized agent"""
    try:
        # Convert capability strings to enums
        agent_capabilities = []
        for cap in capabilities:
            try:
                agent_capabilities.append(AgentCapability(cap.upper()))
            except ValueError:
                click.echo(f"Unknown capability: {cap}")
        
        if specialization:
            # Create specialized agent
            agent = SpecializedAgent(
                agent_id=agent_id,
                specialization=specialization,
                domain_knowledge={}
            )
        else:
            # Create base agent
            agent = BaseAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=agent_capabilities
            )
        
        click.echo(f"Created agent: {agent_id}")
        click.echo(f"   Type: {agent_type}")
        if specialization:
            click.echo(f"   Specialization: {specialization}")
        click.echo(f"   Capabilities: {', '.join([cap.value for cap in agent_capabilities])}")
        
    except Exception as e:
        click.echo(f"Error creating agent: {str(e)}", err=True)

@cli.group()
def experiment():
    """Research experiment commands"""
    pass

@experiment.command()
@click.option('--experiment-id', required=True, help='Experiment identifier')
@click.option('--name', required=True, help='Experiment name')
@click.option('--description', required=True, help='Experiment description')
@click.option('--duration-hours', default=24, type=int, help='Experiment duration in hours')
def create_experiment(experiment_id, name, description, duration_hours):
    """Create a new research experiment"""
    try:
        runner = ExperimentRunner()
        
        config = ExperimentConfiguration(
            experiment_id=experiment_id,
            name=name,
            description=description,
            duration_hours=duration_hours
        )
        
        experiment = runner.create_experiment(config, [], [])
        
        click.echo(f"Created experiment: {experiment_id}")
        click.echo(f"   Name: {name}")
        click.echo(f"   Description: {description}")
        click.echo(f"   Duration: {duration_hours} hours")
        
    except Exception as e:
        click.echo(f"Error creating experiment: {str(e)}", err=True)

@cli.group()
def server():
    """Server management commands"""
    pass

@server.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--workers', default=1, type=int, help='Number of worker processes')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.pass_context
def start(ctx, host, port, workers, reload):
    """Start the OpenDistillery API server"""
    try:
        import uvicorn
        
        click.echo(f"Starting OpenDistillery API server...")
        click.echo(f"   Host: {host}")
        click.echo(f"   Port: {port}")
        click.echo(f"   Workers: {workers}")
        
        # Start the server
        uvicorn.run(
            "opendistillery.api.enterprise_api:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level="info"
        )
        
    except ImportError:
        click.echo("uvicorn not installed. Install with: pip install uvicorn", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error starting server: {str(e)}", err=True)
        sys.exit(1)

@cli.group()
def integration():
    """Enterprise integration commands"""
    pass

@integration.command()
@click.option('--username', required=True, help='Salesforce username')
@click.option('--password', required=True, help='Salesforce password')
@click.option('--security-token', required=True, help='Salesforce security token')
@click.option('--domain', default='login', help='Salesforce domain (login or test)')
def setup_salesforce(username, password, security_token, domain):
    """Setup Salesforce integration"""
    try:
        config = SalesforceConfig(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain
        )
        
        # Test connection
        orchestrator = AgentOrchestrator()
        integration = SalesforceAIIntegration(config, orchestrator)
        
        async def test_connection():
            success = await integration.initialize()
            return success
        
        success = asyncio.run(test_connection())
        
        if success:
            click.echo("Salesforce integration configured successfully")
            
            # Save configuration (without password)
            config_path = Path("integrations/salesforce.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump({
                    "username": username,
                    "domain": domain,
                    "configured_at": "now"
                }, f, indent=2)
            
            click.echo(f"   Configuration saved to: {config_path}")
        else:
            click.echo("Failed to configure Salesforce integration", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error setting up Salesforce: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--system-id', required=True, help='System to test')
@click.option('--prompt', required=True, help='Test prompt')
@click.option('--strategy', default='adaptive', type=click.Choice(['react', 'chain_of_thought', 'tree_of_thoughts', 'graph_of_thoughts', 'self_consistency', 'ensemble', 'adaptive']))
def test(system_id, prompt, strategy):
    """Test a system with a prompt"""
    try:
        system_builder = SystemBuilder()
        system = system_builder.get_system(system_id)
        
        if not system:
            click.echo(f"System {system_id} not found", err=True)
            sys.exit(1)
        
        async def run_test():
            from .core.compound_system import ReasoningStrategy
            
            request = {
                "prompt": prompt,
                "context": {"test_mode": True}
            }
            
            result = await system.process_request(request, ReasoningStrategy(strategy))
            return result
        
        click.echo(f"Testing system {system_id}...")
        click.echo(f"   Strategy: {strategy}")
        click.echo(f"   Prompt: {prompt}")
        click.echo()
        
        result = asyncio.run(run_test())
        
        if result.get("success", False):
            click.echo("Test completed successfully")
            click.echo(f"   Response: {result.get('response', 'No response')}")
            click.echo(f"   Confidence: {result.get('confidence', 0):.1%}")
            
            metadata = result.get("system_metadata", {})
            if metadata:
                click.echo(f"   Processing Time: {metadata.get('processing_time', 0):.3f}s")
                click.echo(f"   Strategy Used: {metadata.get('strategy_used', 'unknown')}")
        else:
            click.echo("Test failed")
            click.echo(f"   Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error running test: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def version():
    """Show version information"""
    click.echo("OpenDistillery v1.0.0")
    click.echo("Advanced Compound AI Systems for Enterprise Workflow Transformation")
    click.echo()
    click.echo("Components:")
    click.echo("  - Compound AI System")
    click.echo("  - Multi-Agent Orchestration")
    click.echo("  - Advanced Reasoning Techniques")
    click.echo("  - Enterprise Integrations")
    click.echo("  - Research & Experimentation")

def main():
    """Main CLI entry point"""
    cli()

if __name__ == '__main__':
    main() 