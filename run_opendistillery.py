#!/usr/bin/env python3
"""
OpenDistillery Startup Script
Comprehensive demonstration of OpenDistillery's compound AI system capabilities
"""

import asyncio
import time
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print OpenDistillery banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                        OpenDistillery                        ║
    ║        Advanced Compound AI Systems for Enterprise           ║
    ║              Workflow Transformation                         ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Main demonstration of OpenDistillery capabilities"""
    print_banner()
    
    try:
        # Import OpenDistillery components
        from src.core.compound_system import SystemBuilder, SystemRequirements, SystemArchitecture, ModelConfiguration
        from src.agents.base_agent import BaseAgent, AgentCapability, SpecializedAgent
        from src.agents.orchestrator import AgentOrchestrator, Task, TaskPriority
        from src.research.experiment_runner import ExperimentRunner
        
        print("OpenDistillery System Initialization")
        print("=" * 50)
        
        # 1. Create Compound AI System
        print("\n1. Creating Compound AI System...")
        system_builder = SystemBuilder()
        
        # Create a financial services system
        requirements = SystemRequirements(
            domain="finance",
            use_case="investment_analysis",
            latency_target_ms=500,
            throughput_rps=200,
            accuracy_threshold=0.95
        )
        
        system = system_builder.create_system(
            system_id="demo_financial_system",
            requirements=requirements,
            architecture=SystemArchitecture.HYBRID
        )
        
        # Add models to the system
        models = [
            ModelConfiguration(
                model_name="gpt4_financial",
                provider="openai",
                model_id="gpt-4",
                max_tokens=4096,
                temperature=0.1,
                specializations=["financial_analysis", "risk_assessment"]
            ),
            ModelConfiguration(
                model_name="claude_compliance",
                provider="anthropic", 
                model_id="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0.0,
                specializations=["compliance", "regulatory_analysis"]
            )
        ]
        
        for model in models:
            system.add_model(model)
        
        print(f"   Created system: {system.system_id}")
        print(f"   Architecture: {system.architecture.value}")
        print(f"   Models configured: {len(system.models)}")
        
        # 2. Create Multi-Agent System
        print("\n2. Setting up Multi-Agent Orchestration...")
        orchestrator = AgentOrchestrator()
        
        # Create specialized agents
        agents = [
            SpecializedAgent(
                agent_id="financial_analyst",
                specialization="financial_analyst",
                domain_knowledge={
                    "expertise": ["financial_modeling", "valuation", "risk_analysis"],
                    "experience_years": 10,
                    "certifications": ["CFA", "FRM"]
                }
            ),
            SpecializedAgent(
                agent_id="risk_manager", 
                specialization="risk_manager",
                domain_knowledge={
                    "expertise": ["risk_assessment", "compliance", "regulatory"],
                    "experience_years": 8,
                    "certifications": ["PRM", "CRM"]
                }
            ),
            BaseAgent(
                agent_id="research_analyst",
                agent_type="research",
                capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS, AgentCapability.SYNTHESIS]
            )
        ]
        
        # Register agents with orchestrator
        for agent in agents:
            orchestrator.register_agent(agent)
        
        print(f"   Registered {len(agents)} specialized agents")
        
        # 3. Demonstrate Reasoning Techniques
        print("\n3. Testing Advanced Reasoning Techniques...")
        
        # Test problem for reasoning
        test_problem = {
            "type": "investment_analysis",
            "prompt": "Analyze the investment potential of a fintech startup with $5M ARR, 40% growth rate, and seeking $20M Series B funding",
            "context": {
                "company": "FinTech Innovations Inc.",
                "metrics": {
                    "arr": 5000000,
                    "growth_rate": 0.40,
                    "funding_round": "Series B",
                    "amount_seeking": 20000000
                }
            }
        }
        
        # Test different reasoning strategies
        from src.core.compound_system import ReasoningStrategy
        
        strategies = [
            ReasoningStrategy.CHAIN_OF_THOUGHT,
            ReasoningStrategy.TREE_OF_THOUGHTS,
            ReasoningStrategy.ADAPTIVE
        ]
        
        results = {}
        for strategy in strategies:
            print(f"   Testing {strategy.value}...")
            start_time = time.time()
            
            try:
                result = await system.process_request(test_problem, strategy)
                execution_time = time.time() - start_time
                
                results[strategy.value] = {
                    "success": result.get("success", False),
                    "execution_time": execution_time,
                    "confidence": result.get("confidence", 0.0)
                }
                
                print(f"     Success: {result.get('success', False)}")
                print(f"     Time: {execution_time:.3f}s")
                print(f"     Confidence: {result.get('confidence', 0.0):.1%}")
                
            except Exception as e:
                print(f"     Error: {str(e)}")
                results[strategy.value] = {"success": False, "error": str(e)}
        
        # 4. Multi-Agent Task Execution
        print("\n4. Demonstrating Multi-Agent Collaboration...")
        
        # Create collaborative tasks
        tasks = [
            Task(
                task_id="financial_analysis_001",
                task_type="financial_analysis",
                description="Perform comprehensive financial analysis of the fintech startup",
                input_data=test_problem["context"],
                priority=TaskPriority.HIGH,
                required_capabilities=[AgentCapability.ANALYSIS, AgentCapability.REASONING]
            ),
            Task(
                task_id="risk_assessment_001", 
                task_type="risk_assessment",
                description="Assess investment risks and regulatory compliance",
                input_data=test_problem["context"],
                priority=TaskPriority.HIGH,
                required_capabilities=[AgentCapability.ANALYSIS, AgentCapability.ADVISORY]
            )
        ]
        
        # Submit tasks to orchestrator
        task_results = []
        for task in tasks:
            task_id = await orchestrator.submit_task(task)
            print(f"   Submitted task: {task.task_type} (ID: {task_id[:8]}...)")
        
        # Wait a moment for task processing
        await asyncio.sleep(2)
        
        # 5. System Status and Performance
        print("\n5. System Status and Performance...")
        
        # Get system status
        system_status = system.get_system_status()
        orchestrator_status = orchestrator.get_orchestration_status()
        
        print("   Compound AI System:")
        print(f"     Models: {system_status['models']['count']}")
        print(f"     Health: {system_status['health']['overall']}")
        print(f"     Requests Processed: {system_status['performance']['requests_processed']}")
        print(f"     Average Latency: {system_status['performance']['average_latency']:.3f}s")
        print(f"     Success Rate: {system_status['performance']['success_rate']:.1%}")
        
        print("   Multi-Agent Orchestrator:")
        print(f"     Active Agents: {orchestrator_status['agents']['active']}")
        print(f"     Tasks Queued: {orchestrator_status['tasks']['queued']}")
        print(f"     Tasks Active: {orchestrator_status['tasks']['active']}")
        print(f"     Tasks Completed: {orchestrator_status['tasks']['completed']}")
        
        # 6. Research and Experimentation
        print("\n6. Research and Experimentation Framework...")
        
        try:
            experiment_runner = ExperimentRunner()
            
            print("   Experiment framework initialized")
            print("   Ready for A/B testing and performance optimization")
            
        except Exception as e:
            print(f"   Experiment framework: {str(e)}")
        
        # 7. Summary and Next Steps
        print("\n7. OpenDistillery Demonstration Summary")
        print("=" * 50)
        
        successful_strategies = sum(1 for r in results.values() if r.get("success", False))
        total_strategies = len(results)
        
        print(f"   Reasoning Strategies Tested: {total_strategies}")
        print(f"   Successful Executions: {successful_strategies}")
        print(f"   Success Rate: {successful_strategies/total_strategies:.1%}")
        
        print(f"   Agents Deployed: {len(agents)}")
        print(f"   Tasks Submitted: {len(tasks)}")
        print(f"   System Health: {system_status['health']['overall']}")
        
        print("\nOpenDistillery Features Demonstrated:")
        print("  - Compound AI System with multi-model orchestration")
        print("  - Advanced reasoning techniques (CoT, ToT, Adaptive)")
        print("  - Multi-agent collaboration and task distribution")
        print("  - Enterprise-grade performance monitoring")
        print("  - Research and experimentation framework")
        print("  - Production-ready architecture and deployment")
        
        print("\nNext Steps:")
        print("  1. Configure API keys for model providers")
        print("  2. Set up enterprise integrations (Salesforce, etc.)")
        print("  3. Deploy using Docker or Kubernetes")
        print("  4. Configure monitoring and alerting")
        print("  5. Run production workloads")
        
        print("\nOpenDistillery is ready for enterprise deployment!")
        
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Please ensure OpenDistillery is properly installed:")
        print("  pip install -e .")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {str(e)}")
        print(f"Error: {str(e)}")
        print("Please check the logs for more details.")

if __name__ == "__main__":
    print("Starting OpenDistillery Demonstration...")
    asyncio.run(main()) 