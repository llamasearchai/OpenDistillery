# Grok API Integration Documentation

## Overview

OpenDistillery provides comprehensive integration with xAI's Grok models, offering enterprise-grade features including real-time information access, vision capabilities, function calling, and advanced reasoning. This integration supports all Grok models with production-ready features.

## Features

### 🤖 **Complete Model Support**
- **Grok 3**: Latest flagship model with 1M context window
- **Grok 3 Beta**: Experimental features and improvements
- **Grok 2**: Balanced performance and cost
- **Grok 2 Mini**: Fast and efficient for simple tasks
- **Grok 1.5 Vision**: Specialized for image analysis

### 🌐 **Real-Time Information**
- Access to current web data and real-time information
- Live search and fact-checking capabilities
- Current events and trending topics

### 👁 **Vision & Multimodal**
- Image analysis and description
- Visual question answering
- Document and chart analysis
- Multimodal reasoning

###  **Advanced Features**
- Function calling with automatic execution
- Streaming responses for real-time interaction
- Advanced rate limiting with burst handling
- Usage analytics and monitoring
- Enterprise-grade error handling

## Quick Start

### Installation

```bash
pip install opendistillery[all]
```

### Basic Setup

```python
import os
from opendistillery.integrations import GrokAPIClient, GrokModel

# Set your API key
os.environ["XAI_API_KEY"] = "your-api-key-here"

# Create client
async def main():
    async with GrokAPIClient() as client:
        response = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello, Grok!"}],
            model=GrokModel.GROK_3
        )
        print(response.content)

# Run
import asyncio
asyncio.run(main())
```

### Convenience Functions

```python
from opendistillery.integrations import get_grok_completion

# Quick completion
response = await get_grok_completion(
    "What are the latest developments in AI?",
    model="grok-3",
    real_time_info=True
)
print(response.content)
```

## Model Specifications

### Grok 3
- **Context Window**: 1,000,000 tokens
- **Max Output**: 131,072 tokens
- **Capabilities**: Text, Vision, Function Calling, Real-time Info
- **Use Cases**: Complex reasoning, large document analysis, research

### Grok 3 Beta
- **Context Window**: 1,000,000 tokens
- **Max Output**: 131,072 tokens
- **Capabilities**: Latest experimental features
- **Use Cases**: Cutting-edge applications, testing new features

### Grok 2
- **Context Window**: 128,000 tokens
- **Max Output**: 65,536 tokens
- **Capabilities**: Text, Function Calling, Real-time Info
- **Use Cases**: General purpose, balanced performance

### Grok 1.5 Vision
- **Context Window**: 64,000 tokens
- **Max Output**: 32,768 tokens
- **Capabilities**: Vision, Image Analysis, Multimodal
- **Use Cases**: Image analysis, visual Q&A, document processing

## Usage Examples

### Basic Chat Completion

```python
from opendistillery.integrations import GrokAPIClient, GrokModel

async def basic_chat():
    async with GrokAPIClient() as client:
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Explain quantum computing in simple terms."}
            ],
            model=GrokModel.GROK_3,
            temperature=0.1,
            max_tokens=500
        )
        
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.usage['total_tokens']}")
        print(f"Latency: {response.latency_ms}ms")
        print(f"Confidence: {response.confidence_score}")
```

### Real-Time Information

```python
async def real_time_info():
    async with GrokAPIClient() as client:
        response = await client.chat_completion(
            messages=[{"role": "user", "content": "What's happening in the stock market today?"}],
            model=GrokModel.GROK_3,
            real_time_info=True  # Enable real-time data access
        )
        
        print(f"Current info: {response.content}")
        if response.real_time_info:
            print(f"Sources: {response.real_time_info.get('sources', [])}")
```

### Vision Analysis

```python
from pathlib import Path

async def analyze_image():
    async with GrokAPIClient() as client:
        # Analyze local image
        response = await client.vision_completion(
            prompt="Describe this image in detail. What do you see?",
            images=[Path("path/to/your/image.jpg")],
            model=GrokModel.GROK_1_5_VISION
        )
        
        print(f"Image analysis: {response.content}")

# Or analyze image from URL
async def analyze_image_url():
    async with GrokAPIClient() as client:
        response = await client.vision_completion(
            prompt="What's in this image?",
            images=["https://example.com/image.jpg"],
            model=GrokModel.GROK_3  # Grok 3 also supports vision
        )
        
        print(f"Analysis: {response.content}")
```

### Streaming Responses

```python
async def streaming_chat():
    async with GrokAPIClient() as client:
        stream = await client.chat_completion(
            messages=[{"role": "user", "content": "Write a short story about AI."}],
            model=GrokModel.GROK_3,
            stream=True
        )
        
        print("Streaming response:")
        async for chunk in stream:
            print(chunk, end="", flush=True)
        print()  # New line at end
```

### Function Calling

```python
from opendistillery.integrations import GrokFunction, create_search_function

async def search_handler(query: str, num_results: int = 5):
    """Mock search function - replace with real implementation"""
    return f"Search results for '{query}' (top {num_results})"

async def function_calling_example():
    # Create search function
    search_func = create_search_function()
    search_func.handler = search_handler
    
    async with GrokAPIClient() as client:
        # Register function
        client.register_function(search_func)
        
        # Use function calling
        response = await client.function_calling_completion(
            prompt="Search for the latest AI research papers",
            functions=[search_func],
            execute_functions=True  # Automatically execute functions
        )
        
        print(f"Response: {response.content}")
        if response.function_calls:
            print(f"Function called: {response.function_calls[0]['name']}")
        if "function_results" in response.metadata:
            print(f"Results: {response.metadata['function_results']}")
```

### Custom Function Definition

```python
from opendistillery.integrations import GrokFunction

# Define custom function
def create_weather_function():
    return GrokFunction(
        name="get_weather",
        description="Get current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or coordinates"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["location"]
        }
    )

async def weather_handler(location: str, units: str = "celsius"):
    """Mock weather function"""
    return f"Weather in {location}: 22°{units[0].upper()}, sunny"

async def custom_function_example():
    weather_func = create_weather_function()
    weather_func.handler = weather_handler
    
    async with GrokAPIClient() as client:
        client.register_function(weather_func)
        
        response = await client.function_calling_completion(
            prompt="What's the weather like in San Francisco?",
            functions=[weather_func],
            execute_functions=True
        )
        
        print(response.content)
```

## Configuration

### Environment Variables

```bash
# Required
export XAI_API_KEY="your-xai-api-key"

# Optional
export XAI_BASE_URL="https://api.x.ai/v1"  # Custom API endpoint
```

### Client Configuration

```python
# Custom configuration
client = GrokAPIClient(
    api_key="your-key-here",
    base_url="https://custom-endpoint.com/v1"
)

# Advanced rate limiting
from opendistillery.integrations import GrokRateLimiter

custom_limiter = GrokRateLimiter(
    requests_per_minute=1000,  # Higher rate limit
    burst_size=20              # Allow burst requests
)

client.rate_limiter = custom_limiter
```

## Monitoring and Analytics

### Usage Statistics

```python
async def monitor_usage():
    async with GrokAPIClient() as client:
        # Make some requests...
        await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model=GrokModel.GROK_3
        )
        
        # Get usage stats
        stats = client.get_usage_stats()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Average latency: {stats['average_latency']}ms")
        print(f"Error rate: {stats['errors']}")
```

### Health Monitoring

```python
async def health_check():
    async with GrokAPIClient() as client:
        health = await client.health_check()
        
        print(f"Status: {health['status']}")
        print(f"API Key Valid: {health['api_key_valid']}")
        print(f"Model Available: {health['model_available']}")
        print(f"Latency: {health['latency_ms']}ms")
```

### Model Information

```python
async def get_model_info():
    async with GrokAPIClient() as client:
        # Get info for specific model
        info = client.get_model_info(GrokModel.GROK_3)
        
        print(f"Model: {info.name}")
        print(f"Max tokens: {info.max_tokens}")
        print(f"Context window: {info.context_window}")
        print(f"Cost per 1K tokens: ${info.cost_per_1k_tokens}")
        print(f"Rate limit: {info.rate_limit_rpm} RPM")
        print(f"Capabilities: {[cap.value for cap in info.capabilities]}")
```

## Error Handling

### Basic Error Handling

```python
from opendistillery.integrations import GrokAPIClient

async def handle_errors():
    try:
        async with GrokAPIClient() as client:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="invalid-model"  # This will raise an error
            )
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"API error: {e}")
```

### Retry Logic

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def resilient_request():
    async with GrokAPIClient() as client:
        return await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model=GrokModel.GROK_3
        )

# Usage
try:
    response = await resilient_request()
    print(response.content)
except Exception as e:
    print(f"All retries failed: {e}")
```

## Performance Optimization

### Concurrent Requests

```python
import asyncio

async def concurrent_requests():
    async with GrokAPIClient() as client:
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = client.chat_completion(
                messages=[{"role": "user", "content": f"Question {i}"}],
                model=GrokModel.GROK_3
            )
            tasks.append(task)
        
        # Execute concurrently
        responses = await asyncio.gather(*tasks)
        
        for i, response in enumerate(responses):
            print(f"Response {i}: {response.content[:50]}...")
```

### Batch Processing

```python
async def batch_process_questions(questions: list):
    async with GrokAPIClient() as client:
        results = []
        
        # Process in batches of 3 to respect rate limits
        batch_size = 3
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            
            # Create tasks for this batch
            tasks = [
                client.chat_completion(
                    messages=[{"role": "user", "content": question}],
                    model=GrokModel.GROK_2  # Use faster model for batches
                )
                for question in batch
            ]
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Optional: add delay between batches
            if i + batch_size < len(questions):
                await asyncio.sleep(1)
        
        return results

# Usage
questions = [
    "What is machine learning?",
    "Explain neural networks",
    "What is deep learning?",
    "How do transformers work?",
    "What is attention mechanism?"
]

results = await batch_process_questions(questions)
for i, result in enumerate(results):
    print(f"Q{i+1}: {result.content[:100]}...")
```

## Integration with OpenDistillery

### Multi-Agent Systems

```python
from opendistillery.agents import MultiAgentOrchestrator
from opendistillery.integrations import GrokAPIClient

async def grok_powered_agents():
    # Create Grok-powered agents
    async with GrokAPIClient() as grok_client:
        
        # Researcher agent using Grok's real-time capabilities
        researcher_config = {
            "name": "researcher",
            "role": "research_specialist",
            "client": grok_client,
            "model": GrokModel.GROK_3,
            "capabilities": ["real_time_info", "web_search"]
        }
        
        # Analyst agent using vision capabilities
        analyst_config = {
            "name": "analyst", 
            "role": "data_analyst",
            "client": grok_client,
            "model": GrokModel.GROK_1_5_VISION,
            "capabilities": ["vision", "chart_analysis"]
        }
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator([researcher_config, analyst_config])
        
        # Execute multi-agent task
        result = await orchestrator.execute_task(
            "Research the latest AI trends and analyze the provided chart",
            context={"chart_image": "path/to/chart.png"}
        )
        
        return result
```

### Compound AI Systems

```python
from opendistillery.core import CompoundAISystem
from opendistillery.integrations import GrokAPIClient, get_grok_completion

async def grok_compound_system():
    # Create compound system with Grok integration
    system = CompoundAISystem()
    
    # Add Grok as a reasoning component
    async def grok_reasoning(prompt: str, context: dict):
        return await get_grok_completion(
            f"Context: {context}\n\nTask: {prompt}",
            model="grok-3",
            real_time_info=True
        )
    
    system.add_component("grok_reasoning", grok_reasoning)
    
    # Add Grok vision for image analysis
    async def grok_vision(prompt: str, images: list):
        async with GrokAPIClient() as client:
            return await client.vision_completion(prompt, images)
    
    system.add_component("grok_vision", grok_vision)
    
    return system
```

## Best Practices

### 1. **API Key Security**
```python
# ✅ Good: Use environment variables
import os
api_key = os.getenv("XAI_API_KEY")

# ❌ Bad: Hardcode API keys
api_key = "xai-123456789"  # Never do this!
```

### 2. **Rate Limiting**
```python
# ✅ Good: Respect rate limits
async with GrokAPIClient() as client:
    # Built-in rate limiting
    response = await client.chat_completion(...)

# ✅ Good: Custom rate limiting for high-volume
from opendistillery.integrations import GrokRateLimiter

limiter = GrokRateLimiter(requests_per_minute=500)  # Conservative limit
client.rate_limiter = limiter
```

### 3. **Error Handling**
```python
# ✅ Good: Comprehensive error handling
try:
    response = await client.chat_completion(...)
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    # Handle configuration issues
except httpx.HTTPStatusError as e:
    logger.error(f"API error {e.response.status_code}: {e}")
    # Handle API errors
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle unexpected errors
```

### 4. **Resource Management**
```python
# ✅ Good: Use context managers
async with GrokAPIClient() as client:
    response = await client.chat_completion(...)
    # Client is automatically closed

# ✅ Good: Manual cleanup
client = GrokAPIClient()
try:
    response = await client.chat_completion(...)
finally:
    await client.close()
```

### 5. **Model Selection**
```python
# ✅ Good: Choose appropriate model for task
def select_model(task_type: str, complexity: str):
    if task_type == "vision":
        return GrokModel.GROK_1_5_VISION
    elif complexity == "high":
        return GrokModel.GROK_3
    elif complexity == "low":
        return GrokModel.GROK_2_MINI
    else:
        return GrokModel.GROK_2
```

### 6. **Monitoring**
```python
# ✅ Good: Monitor usage and performance
async def monitored_completion(client, messages):
    start_time = time.time()
    
    try:
        response = await client.chat_completion(messages=messages)
        
        # Log successful completion
        duration = time.time() - start_time
        logger.info(f"Completion successful: {duration:.2f}s, {response.usage['total_tokens']} tokens")
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Completion failed after {duration:.2f}s: {e}")
        raise
```

## Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   ValueError: XAI_API_KEY environment variable or api_key parameter required
   ```
   **Solution**: Set the `XAI_API_KEY` environment variable or pass it directly to the client.

2. **Rate Limit Exceeded**
   ```
   HTTP 429: Too Many Requests
   ```
   **Solution**: Implement retry logic with exponential backoff or reduce request frequency.

3. **Model Not Found**
   ```
   ValueError: Unsupported Grok model: invalid-model
   ```
   **Solution**: Use a valid model name from `GrokModel` enum.

4. **Vision Not Supported**
   ```
   ValueError: Model grok-2 does not support vision
   ```
   **Solution**: Use `GrokModel.GROK_1_5_VISION` or `GrokModel.GROK_3` for vision tasks.

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("opendistillery.integrations.grok_integration")

# Now you'll see detailed logs
async with GrokAPIClient() as client:
    response = await client.chat_completion(...)
```

### Performance Debugging

```python
async def debug_performance():
    async with GrokAPIClient() as client:
        # Get detailed timing
        import time
        start = time.time()
        
        response = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model=GrokModel.GROK_3
        )
        
        total_time = time.time() - start
        
        print(f"Total time: {total_time:.2f}s")
        print(f"API latency: {response.latency_ms}ms")
        print(f"Tokens/second: {response.usage['total_tokens'] / total_time:.1f}")
```

## API Reference

For complete API reference, see the inline documentation in the source code:

- `GrokAPIClient`: Main client class
- `GrokModel`: Model enumeration
- `GrokResponse`: Response data structure
- `GrokFunction`: Function calling definition
- `GrokModelSpec`: Model specifications

## Support

For issues, questions, or feature requests:

- **GitHub Issues**: [opendistillery/issues](https://github.com/nikjois/opendistillery/issues)
- **Email**: nikjois@llamasearch.ai
- **Documentation**: [docs.opendistillery.ai](https://docs.opendistillery.ai)

## License

OpenDistillery Grok integration is licensed under the MIT License. See [LICENSE](../LICENSE) for details. 