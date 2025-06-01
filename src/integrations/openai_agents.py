"""
OpenAI Agents SDK Integration
Provides integration with OpenAI's latest agents and tools capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import openai
from openai.types.beta import Assistant, Thread, Run
from openai.types.beta.threads import Message

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Agent role definitions"""
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    SYNTHESIZER = "synthesizer"
    CRITIC = "critic"
    COORDINATOR = "coordinator"

@dataclass
class AgentConfig:
    """Configuration for OpenAI agent"""
    name: str
    role: AgentRole
    instructions: str
    model: str = "gpt-4-1106-preview"
    tools: List[Dict[str, Any]] = None
    file_ids: List[str] = None
    metadata: Dict[str, Any] = None

class OpenAIAgent:
    """Individual OpenAI agent wrapper"""
    
    def __init__(self, config: AgentConfig, client: openai.AsyncOpenAI):
        self.config = config
        self.client = client
        self.assistant: Optional[Assistant] = None
        self.thread: Optional[Thread] = None
        
    async def initialize(self):
        """Initialize the agent with OpenAI"""
        try:
            # Create assistant
            self.assistant = await self.client.beta.assistants.create(
                name=self.config.name,
                instructions=self.config.instructions,
                model=self.config.model,
                tools=self.config.tools or [],
                file_ids=self.config.file_ids or [],
                metadata=self.config.metadata or {}
            )
            
            # Create thread
            self.thread = await self.client.beta.threads.create()
            
            logger.info(f"Initialized agent {self.config.name} with assistant {self.assistant.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.config.name}: {e}")
            raise
    
    async def send_message(self, content: str, role: str = "user") -> str:
        """Send message to agent and get response"""
        if not self.assistant or not self.thread:
            raise ValueError("Agent not initialized")
        
        try:
            # Add message to thread
            await self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )
            
            # Create run
            run = await self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get messages
                messages = await self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                
                # Return latest assistant message
                for message in messages.data:
                    if message.role == "assistant":
                        return message.content[0].text.value
                        
            else:
                logger.error(f"Run failed with status: {run.status}")
                return f"Error: Run failed with status {run.status}"
                
        except Exception as e:
            logger.error(f"Error sending message to agent {self.config.name}: {e}")
            return f"Error: {str(e)}"
    
    async def cleanup(self):
        """Cleanup agent resources"""
        if self.assistant:
            try:
                await self.client.beta.assistants.delete(self.assistant.id)
                logger.info(f"Deleted assistant {self.assistant.id}")
            except Exception as e:
                logger.error(f"Error deleting assistant: {e}")

class MultiAgentOrchestrator:
    """Orchestrates multiple OpenAI agents for collaborative tasks"""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.agents: Dict[str, OpenAIAgent] = {}
        self.workflows: Dict[str, Callable] = {}
        
    async def add_agent(self, config: AgentConfig) -> OpenAIAgent:
        """Add and initialize a new agent"""
        agent = OpenAIAgent(config, self.client)
        await agent.initialize()
        self.agents[config.name] = agent
        return agent
    
    async def create_financial_analysis_team(self):
        """Create a team of agents for financial analysis"""
        
        # Financial Analyst Agent
        analyst_config = AgentConfig(
            name="financial_analyst",
            role=AgentRole.ANALYST,
            instructions="""You are a senior financial analyst with expertise in:
            - Financial statement analysis
            - Valuation models (DCF, comparable company analysis)
            - Risk assessment and due diligence
            - Market and industry analysis
            
            Provide detailed, data-driven analysis with clear recommendations.
            Always show your calculations and assumptions.""",
            tools=[
                {"type": "code_interpreter"},
                {"type": "retrieval"}
            ]
        )
        
        # Risk Manager Agent
        risk_config = AgentConfig(
            name="risk_manager",
            role=AgentRole.CRITIC,
            instructions="""You are a risk management specialist focused on:
            - Identifying potential risks and red flags
            - Regulatory compliance analysis
            - Credit and operational risk assessment
            - Stress testing and scenario analysis
            
            Critically evaluate all financial decisions and highlight potential issues.""",
            tools=[
                {"type": "code_interpreter"}
            ]
        )
        
        # Research Analyst Agent
        research_config = AgentConfig(
            name="research_analyst",
            role=AgentRole.RESEARCHER,
            instructions="""You are a research analyst specializing in:
            - Market research and competitive analysis
            - Industry trends and dynamics
            - Economic and regulatory environment analysis
            - Due diligence research
            
            Provide comprehensive research reports with actionable insights.""",
            tools=[
                {"type": "retrieval"}
            ]
        )
        
        # Investment Coordinator Agent
        coordinator_config = AgentConfig(
            name="investment_coordinator",
            role=AgentRole.COORDINATOR,
            instructions="""You are the investment committee coordinator responsible for:
            - Synthesizing analysis from multiple team members
            - Facilitating decision-making processes
            - Creating executive summaries and recommendations
            - Ensuring all perspectives are considered
            
            Coordinate the team's work to produce final investment recommendations."""
        )
        
        # Initialize all agents
        await asyncio.gather(
            self.add_agent(analyst_config),
            self.add_agent(risk_config),
            self.add_agent(research_config),
            self.add_agent(coordinator_config)
        )
    
    async def financial_analysis_workflow(self, investment_opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collaborative financial analysis workflow"""
        
        # Phase 1: Individual Analysis
        logger.info("Starting Phase 1: Individual Analysis")
        
        # Prepare analysis prompt
        prompt = f"""
        Please analyze the following investment opportunity:
        
        Company: {investment_opportunity.get('company_name', 'Unknown')}
        Industry: {investment_opportunity.get('industry', 'Unknown')}
        Stage: {investment_opportunity.get('stage', 'Unknown')}
        Funding Amount: ${investment_opportunity.get('funding_amount', 0):,}
        
        Key Metrics:
        - Revenue: ${investment_opportunity.get('revenue', 0):,}
        - Growth Rate: {investment_opportunity.get('growth_rate', 0):.1%}
        - Gross Margin: {investment_opportunity.get('gross_margin', 0):.1%}
        - EBITDA: ${investment_opportunity.get('ebitda', 0):,}
        
        Additional Context:
        {investment_opportunity.get('additional_context', 'No additional context provided')}
        """
        
        # Get individual analyses
        individual_analyses = await asyncio.gather(
            self.agents["financial_analyst"].send_message(
                f"{prompt}\n\nPlease provide a detailed financial analysis including valuation, key metrics analysis, and investment attractiveness."
            ),
            self.agents["risk_manager"].send_message(
                f"{prompt}\n\nPlease conduct a comprehensive risk assessment identifying potential red flags, risks, and mitigation strategies."
            ),
            self.agents["research_analyst"].send_message(
                f"{prompt}\n\nPlease provide market and competitive analysis, industry outlook, and due diligence insights."
            )
        )
        
        # Phase 2: Collaborative Synthesis
        logger.info("Starting Phase 2: Collaborative Synthesis")
        
        synthesis_prompt = f"""
        Based on the following analyses from our team, please provide a comprehensive investment recommendation:
        
        FINANCIAL ANALYSIS:
        {individual_analyses[0]}
        
        RISK ASSESSMENT:
        {individual_analyses[1]}
        
        MARKET RESEARCH:
        {individual_analyses[2]}
        
        Please synthesize these perspectives into:
        1. Executive Summary
        2. Key Strengths and Opportunities
        3. Major Risks and Concerns
        4. Final Investment Recommendation (Invest/Pass/Conditional)
        5. Recommended Terms (if applicable)
        6. Key Conditions or Next Steps
        """
        
        final_recommendation = await self.agents["investment_coordinator"].send_message(synthesis_prompt)
        
        return {
            "investment_opportunity": investment_opportunity,
            "individual_analyses": {
                "financial_analysis": individual_analyses[0],
                "risk_assessment": individual_analyses[1],
                "market_research": individual_analyses[2]
            },
            "final_recommendation": final_recommendation,
            "workflow_status": "completed"
        }
    
    async def execute_workflow(self, workflow_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a named workflow"""
        if workflow_name == "financial_analysis":
            return await self.financial_analysis_workflow(kwargs.get("investment_opportunity", {}))
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")
    
    async def cleanup(self):
        """Cleanup all agents"""
        cleanup_tasks = [agent.cleanup() for agent in self.agents.values()]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        self.agents.clear()

class OpenAIAgentsManager:
    """High-level manager for OpenAI agents integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.orchestrators: Dict[str, MultiAgentOrchestrator] = {}
    
    async def create_orchestrator(self, name: str) -> MultiAgentOrchestrator:
        """Create a new multi-agent orchestrator"""
        orchestrator = MultiAgentOrchestrator(self.api_key)
        self.orchestrators[name] = orchestrator
        return orchestrator
    
    async def get_or_create_financial_team(self) -> MultiAgentOrchestrator:
        """Get or create financial analysis team"""
        if "financial_team" not in self.orchestrators:
            orchestrator = await self.create_orchestrator("financial_team")
            await orchestrator.create_financial_analysis_team()
        return self.orchestrators["financial_team"]
    
    async def analyze_investment(self, investment_data: Dict[str, Any]) -> Dict[str, Any]:
        """High-level investment analysis using agent team"""
        try:
            financial_team = await self.get_or_create_financial_team()
            result = await financial_team.execute_workflow(
                "financial_analysis", 
                investment_opportunity=investment_data
            )
            return result
        except Exception as e:
            logger.error(f"Investment analysis failed: {e}")
            return {
                "error": str(e),
                "workflow_status": "failed"
            }
    
    async def cleanup_all(self):
        """Cleanup all orchestrators"""
        cleanup_tasks = [orch.cleanup() for orch in self.orchestrators.values()]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        self.orchestrators.clear()

# Example usage
async def example_usage():
    """Example of using OpenAI agents for investment analysis"""
    
    # Initialize manager
    manager = OpenAIAgentsManager(api_key="your-openai-api-key")
    
    # Sample investment opportunity
    investment = {
        "company_name": "TechCorp AI",
        "industry": "Artificial Intelligence",
        "stage": "Series B",
        "funding_amount": 25000000,
        "revenue": 8000000,
        "growth_rate": 0.85,
        "gross_margin": 0.75,
        "ebitda": 2000000,
        "additional_context": """
        Leading AI company in enterprise automation.
        Strong customer base including Fortune 500 companies.
        Proprietary technology with significant IP portfolio.
        Experienced management team with previous exits.
        """
    }
    
    try:
        # Analyze investment
        result = await manager.analyze_investment(investment)
        
        print("Investment Analysis Complete!")
        print(f"Status: {result['workflow_status']}")
        print(f"Final Recommendation:\n{result['final_recommendation']}")
        
    finally:
        # Cleanup
        await manager.cleanup_all()

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage()) 