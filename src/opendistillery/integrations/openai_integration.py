import openai
from openai import OpenAI
import asyncio
from typing import Dict, List, Any, AsyncGenerator
import json
from dataclasses import dataclass
from rich.console import Console

@dataclass
class ConversationContext:
    """Maintains conversation context and memory"""
    messages: List[Dict[str, str]]
    system_prompt: str
    temperature: float = 0.7
    model: str = "gpt-4-turbo-preview"

class OpenAIInterface:
    """Advanced OpenAI integration with streaming and tool calling"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key)
        self.console = Console()
        self.tools = self._setup_tools()
        
    def _setup_tools(self) -> List[Dict]:
        """Setup function calling tools"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_research_task",
                    "description": "Execute a research task using OpenDistillery",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_type": {"type": "string"},
                            "parameters": {"type": "object"},
                            "technique": {"type": "string"}
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "analyze_code",
                    "description": "Analyze code structure and quality",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "language": {"type": "string"}
                        }
                    }
                }
            }
        ]
    
    async def chat_completion_stream(
        self, 
        context: ConversationContext
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion with real-time display"""
        
        stream = self.client.chat.completions.create(
            model=context.model,
            messages=context.messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=context.temperature,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    async def process_with_tools(self, query: str) -> Dict[str, Any]:
        """Process query with function calling capabilities"""
        
        messages = [
            {"role": "system", "content": "You are an AI research assistant with access to OpenDistillery tools."},
            {"role": "user", "content": query}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            return await self._handle_tool_calls(message.tool_calls)
        else:
            return {"response": message.content, "type": "text"}
    
    async def _handle_tool_calls(self, tool_calls) -> Dict[str, Any]:
        """Handle function calls from AI"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if function_name == "execute_research_task":
                result = await self._execute_research_task(**arguments)
            elif function_name == "analyze_code":
                result = await self._analyze_code(**arguments)
            else:
                result = {"error": f"Unknown function: {function_name}"}
                
            results.append({
                "function": function_name,
                "result": result
            })
            
        return {"tool_results": results, "type": "function_calls"}
    
    async def _execute_research_task(self, task_type: str, parameters: Dict, technique: str):
        """Execute research task using OpenDistillery"""
        # Integration with existing research modules
        from ..research.orchestrator import ResearchOrchestrator
        
        orchestrator = ResearchOrchestrator()
        return await orchestrator.execute_task({
            "type": task_type,
            "parameters": parameters,
            "technique": technique
        })
    
    async def _analyze_code(self, code: str, language: str):
        """Analyze code structure"""
        # Implement code analysis logic
        return {
            "complexity": "medium",
            "suggestions": ["Add type hints", "Improve error handling"],
            "quality_score": 8.5
        }

# Shell-GPT Integration
class ShellGPTIntegration:
    """Integration with shell-gpt for terminal AI assistance"""
    
    def __init__(self):
        self.openai_interface = OpenAIInterface()
        
    async def execute_shell_command(self, natural_language_query: str):
        """Convert natural language to shell commands"""
        
        prompt = f"""
        Convert this natural language request to appropriate shell commands:
        Request: {natural_language_query}
        
        Provide safe, well-commented commands only. No destructive operations.
        """
        
        response = await self.openai_interface.process_with_tools(prompt)
        return response