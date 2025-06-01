"""
Gradient-based Prompt Optimization
Inspired by "Automatic Prompt Optimization with Gradient Descent and Beam Search"
Simulates differentiable prompt optimization for discrete text
"""

import numpy as np
from typing import Dict, List, Any, Tuple
import asyncio
from dataclasses import dataclass
import matplotlib.pyplot as plt

@dataclass
class PromptEmbedding:
    """Represents prompt in differentiable space"""
    tokens: List[str]
    embeddings: np.ndarray
    gradient: np.ndarray
    learning_rate: float = 0.01

class GradientPromptOptimizer:
    """
    Simulated gradient-based prompt optimization
    
    Features:
    - Discrete-to-continuous prompt mapping
    - Gradient estimation via perturbation
    - Beam search integration
    - Performance visualization
    """
    
    def __init__(self, vocab_size: int = 50000, embedding_dim: int = 768):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.token_embeddings = self._initialize_embeddings()
        self.optimization_history = []
        
    def _initialize_embeddings(self) -> np.ndarray:
        """Initialize token embedding matrix (simulated)"""
        return np.random.randn(self.vocab_size, self.embedding_dim) * 0.02
    
    async def optimize_prompt(
        self,
        initial_prompt: str,
        objective_function: callable,
        iterations: int = 20,
        beam_width: int = 3
    ) -> Dict[str, Any]:
        """
        Optimize prompt using simulated gradient descent
        
        Args:
            initial_prompt: Starting prompt
            objective_function: Function that scores prompt quality
            iterations: Number of optimization steps
            beam_width: Number of prompt candidates to maintain
        """
        
        # Convert prompt to embedding space
        current_embedding = self._text_to_embedding(initial_prompt)
        best_score = 0.0
        best_prompt = initial_prompt
        
        # Maintain beam of candidates
        beam = [(current_embedding, initial_prompt, 0.0)]
        
        for iteration in range(iterations):
            new_candidates = []
            
            for embedding, prompt, score in beam:
                # Estimate gradient via finite differences
                gradient = await self._estimate_gradient(
                    embedding, 
                    objective_function
                )
                
                # Update embedding
                new_embedding = PromptEmbedding(
                    tokens=prompt.split(),
                    embeddings=embedding.embeddings - embedding.learning_rate * gradient,
                    gradient=gradient,
                    learning_rate=embedding.learning_rate * 0.99
                )
                
                # Convert back to text
                new_prompt = self._embedding_to_text(new_embedding)
                new_score = await objective_function(new_prompt)
                
                new_candidates.append((new_embedding, new_prompt, new_score))
                
                # Track best performer
                if new_score > best_score:
                    best_score = new_score
                    best_prompt = new_prompt
            
            # Select top candidates for next iteration
            beam = sorted(new_candidates, key=lambda x: x[2], reverse=True)[:beam_width]
            
            # Record progress
            self.optimization_history.append({
                "iteration": iteration,
                "best_score": best_score,
                "beam_scores": [score for _, _, score in beam],
                "gradient_norm": np.linalg.norm(beam[0][0].gradient) if beam else 0.0
            })
        
        return {
            "optimized_prompt": best_prompt,
            "final_score": best_score,
            "optimization_history": self.optimization_history,
            "convergence_plot": self._generate_convergence_plot()
        }
    
    async def _estimate_gradient(
        self, 
        embedding: PromptEmbedding, 
        objective_function: callable,
        epsilon: float = 0.01
    ) -> np.ndarray:
        """Estimate gradient using finite differences"""
        
        gradient = np.zeros_like(embedding.embeddings)
        base_prompt = self._embedding_to_text(embedding)
        base_score = await objective_function(base_prompt)
        
        # Estimate partial derivatives
        for i in range(min(10, embedding.embeddings.shape[0])):  # Sample subset for efficiency
            for j in range(min(10, embedding.embeddings.shape[1])):
                # Positive perturbation
                perturbed_embedding = embedding.embeddings.copy()
                perturbed_embedding[i, j] += epsilon
                
                perturbed_prompt_obj = PromptEmbedding(
                    tokens=embedding.tokens,
                    embeddings=perturbed_embedding,
                    gradient=np.zeros_like(perturbed_embedding)
                )
                
                perturbed_prompt = self._embedding_to_text(perturbed_prompt_obj)
                perturbed_score = await objective_function(perturbed_prompt)
                
                # Calculate partial derivative
                gradient[i, j] = (perturbed_score - base_score) / epsilon
        
        return gradient
    
    def _text_to_embedding(self, text: str) -> PromptEmbedding:
        """Convert text to embedding representation"""
        tokens = text.split()
        
        # Simulate token-to-embedding lookup
        embeddings = np.zeros((len(tokens), self.embedding_dim))
        for i, token in enumerate(tokens):
            token_id = hash(token) % self.vocab_size
            embeddings[i] = self.token_embeddings[token_id]
        
        return PromptEmbedding(
            tokens=tokens,
            embeddings=embeddings,
            gradient=np.zeros_like(embeddings)
        )
    
    def _embedding_to_text(self, embedding: PromptEmbedding) -> str:
        """Convert embedding back to text (simplified)"""
        # In practice, this would use nearest neighbor search in embedding space
        # For simulation, we'll apply small modifications to original tokens
        
        modified_tokens = []
        for i, token in enumerate(embedding.tokens):
            # Simulate token modification based on embedding changes
            if i < len(embedding.embeddings):
                embedding_magnitude = np.linalg.norm(embedding.embeddings[i])
                if embedding_magnitude > 1.2:  # Arbitrary threshold
                    # "Mutate" token slightly
                    modified_tokens.append(f"{token}_opt")
                else:
                    modified_tokens.append(token)
            else:
                modified_tokens.append(token)
        
        return " ".join(modified_tokens)
    
    def _generate_convergence_plot(self) -> str:
        """Generate convergence visualization"""
        if not self.optimization_history:
            return "No optimization history available"
        
        iterations = [h["iteration"] for h in self.optimization_history]
        scores = [h["best_score"] for h in self.optimization_history]
        
        plt.figure(figsize=(10, 6))
        plt.plot(iterations, scores, 'b-', linewidth=2, label='Best Score')
        plt.xlabel('Iteration')
        plt.ylabel('Objective Score')
        plt.title('Gradient-based Prompt Optimization Convergence')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plot_path = "gradient_optimization_convergence.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"Convergence plot saved to {plot_path}"

# Example objective function
async def example_objective_function(prompt: str) -> float:
    """
    Example objective function that scores prompt quality
    In practice, this would use actual LLM evaluation
    """
    
    # Simulate evaluation latency
    await asyncio.sleep(0.1)
    
    # Simple heuristic scoring
    score = 0.0
    
    # Prefer longer, more detailed prompts
    score += min(len(prompt.split()) / 50.0, 0.3)
    
    # Prefer specific keywords
    quality_keywords = ["specific", "detailed", "step-by-step", "example", "clear"]
    score += sum(0.1 for keyword in quality_keywords if keyword in prompt.lower())
    
    # Penalize repetition
    words = prompt.lower().split()
    unique_ratio = len(set(words)) / max(len(words), 1)
    score += unique_ratio * 0.2
    
    return min(score, 1.0)