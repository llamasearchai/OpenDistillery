"""
Advanced ML Pipeline for Continuous Prompt Optimization
Self-improving system using reinforcement learning and neural architecture search
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from transformers import AutoTokenizer, AutoModel
import asyncio
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class TrainingSample:
    """Training sample for ML models"""
    prompt: str
    optimized_prompt: str
    technique_used: str
    model_used: str
    quality_score: float
    improvement: float
    context_features: Dict
    timestamp: datetime

class PromptEmbeddingExtractor:
    """Extract semantic embeddings from prompts"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
    
    def extract_features(self, prompts: List[str]) -> np.ndarray:
        """Extract semantic features from prompts"""
        
        embeddings = []
        
        for prompt in prompts:
            # Tokenize and encode
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                embeddings.append(embedding[0])
        
        return np.array(embeddings)
    
    def extract_linguistic_features(self, prompt: str) -> Dict[str, float]:
        """Extract linguistic and structural features"""
        
        tokens = self.tokenizer.tokenize(prompt)
        
        features = {
            "length": len(prompt),
            "word_count": len(prompt.split()),
            "token_count": len(tokens),
            "avg_word_length": np.mean([len(word) for word in prompt.split()]),
            "sentence_count": prompt.count('.') + prompt.count('!') + prompt.count('?'),
            "question_count": prompt.count('?'),
            "exclamation_count": prompt.count('!'),
            "uppercase_ratio": sum(1 for c in prompt if c.isupper()) / len(prompt),
            "digit_ratio": sum(1 for c in prompt if c.isdigit()) / len(prompt),
            "punctuation_ratio": sum(1 for c in prompt if not c.isalnum() and not c.isspace()) / len(prompt),
        }
        
        return features

class QualityPredictor(nn.Module):
    """Neural network for quality prediction"""
    
    def __init__(self, input_dim: int, hidden_dims: List[int] = [512, 256, 128]):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.BatchNorm1d(hidden_dim)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)

class TechniqueSelector(nn.Module):
    """Neural network for technique selection"""
    
    def __init__(self, input_dim: int, num_techniques: int):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, num_techniques),
            nn.Softmax(dim=1)
        )
    
    def forward(self, x):
        return self.network(x)

class ReinforcementLearningOptimizer:
    """RL-based prompt optimization"""
    
    def __init__(self, state_dim: int, action_dim: int):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Q-Network
        self.q_network = nn.Sequential(
            nn.Linear(state_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )
        
        # Target network for stable training
        self.target_network = nn.Sequential(
            nn.Linear(state_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        self.memory = []
        self.epsilon = 0.1
        self.gamma = 0.99
        
    def select_action(self, state: np.ndarray) -> int:
        """Select action using epsilon-greedy policy"""
        
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_network(state_tensor)
            return q_values.argmax().item()
    
    def train_step(self, batch_size: int = 32):
        """Perform one training step"""
        
        if len(self.memory) < batch_size:
            return
        
        batch = np.random.choice(self.memory, batch_size, replace=False)
        
        states = torch.FloatTensor([transition[0] for transition in batch])
        actions = torch.LongTensor([transition[1] for transition in batch])
        rewards = torch.FloatTensor([transition[2] for transition in batch])
        next_states = torch.FloatTensor([transition[3] for transition in batch])
        dones = torch.BoolTensor([transition[4] for transition in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()

class ContinuousImprovementPipeline:
    """Main pipeline for continuous improvement"""
    
    def __init__(self):
        self.embedding_extractor = PromptEmbeddingExtractor()
        self.quality_predictor = None
        self.technique_selector = None
        self.rl_optimizer = None
        self.scaler = StandardScaler()
        
        # Technique mappings
        self.techniques = [
            "quantum_superposition",
            "neural_architecture_search", 
            "hyperparameter_optimization",
            "metacognitive",
            "neuro_symbolic",
            "multimodal_cot",
            "tree_of_thoughts"
        ]
        
        self.technique_to_idx = {tech: idx for idx, tech in enumerate(self.techniques)}
        self.training_data = []
        
    async def collect_training_data(self, samples: List[TrainingSample]):
        """Collect and preprocess training data"""
        
        logger.info(f"Collecting {len(samples)} training samples")
        
        for sample in samples:
            try:
                # Extract features
                embedding = self.embedding_extractor.extract_features([sample.prompt])[0]
                linguistic_features = self.embedding_extractor.extract_linguistic_features(sample.prompt)
                
                # Create feature vector
                feature_vector = np.concatenate([
                    embedding,
                    list(linguistic_features.values()),
                    [self.technique_to_idx.get(sample.technique_used, 0)],
                    [len(sample.context_features)]
                ])
                
                training_point = {
                    "features": feature_vector,
                    "quality_score": sample.quality_score,
                    "improvement": sample.improvement,
                    "technique": sample.technique_used,
                    "timestamp": sample.timestamp
                }
                
                self.training_data.append(training_point)
                
            except Exception as e:
                logger.error(f"Error processing sample: {e}")
                continue
        
        logger.info(f"Successfully processed {len(self.training_data)} samples")
    
    async def train_quality_predictor(self):
        """Train the quality prediction model"""
        
        if len(self.training_data) < 100:
            logger.warning("Insufficient training data for quality predictor")
            return
        
        logger.info("Training quality prediction model")
        
        # Prepare data
        X = np.array([point["features"] for point in self.training_data])
        y = np.array([point["quality_score"] for point in self.training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Initialize model
        input_dim = X_train_scaled.shape[1]
        self.quality_predictor = QualityPredictor(input_dim)
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.quality_predictor.parameters(), lr=0.001)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train_scaled)
        y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1)
        X_test_tensor = torch.FloatTensor(X_test_scaled)
        y_test_tensor = torch.FloatTensor(y_test).unsqueeze(1)
        
        # Training loop
        best_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(1000):
            self.quality_predictor.train()
            
            # Forward pass
            predictions = self.quality_predictor(X_train_tensor)
            loss = criterion(predictions, y_train_tensor)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Validation
            if epoch % 50 == 0:
                self.quality_predictor.eval()
                with torch.no_grad():
                    val_predictions = self.quality_predictor(X_test_tensor)
                    val_loss = criterion(val_predictions, y_test_tensor)
                
                logger.info(f"Epoch {epoch}: Train Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}")
                
                # Early stopping
                if val_loss < best_loss:
                    best_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= 10:
                        logger.info("Early stopping triggered")
                        break
        
        logger.info("Quality predictor training completed")
    
    async def train_technique_selector(self):
        """Train the technique selection model"""
        
        if len(self.training_data) < 100:
            logger.warning("Insufficient training data for technique selector")
            return
        
        logger.info("Training technique selection model")
        
        # Prepare data
        X = np.array([point["features"] for point in self.training_data])
        y = np.array([self.technique_to_idx.get(point["technique"], 0) for point in self.training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.transform(X_train)  # Use existing scaler
        X_test_scaled = self.scaler.transform(X_test)
        
        # Initialize model
        input_dim = X_train_scaled.shape[1]
        num_techniques = len(self.techniques)
        self.technique_selector = TechniqueSelector(input_dim, num_techniques)
        
        # Training setup
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.technique_selector.parameters(), lr=0.001)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train_scaled)
        y_train_tensor = torch.LongTensor(y_train)
        X_test_tensor = torch.FloatTensor(X_test_scaled)
        y_test_tensor = torch.LongTensor(y_test)
        
        # Training loop
        best_accuracy = 0
        patience_counter = 0
        
        for epoch in range(500):
            self.technique_selector.train()
            
            # Forward pass
            predictions = self.technique_selector(X_train_tensor)
            loss = criterion(predictions, y_train_tensor)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Validation
            if epoch % 25 == 0:
                self.technique_selector.eval()
                with torch.no_grad():
                    val_predictions = self.technique_selector(X_test_tensor)
                    _, predicted = torch.max(val_predictions, 1)
                    accuracy = (predicted == y_test_tensor).float().mean().item()
                
                logger.info(f"Epoch {epoch}: Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}")
                
                # Early stopping
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= 10:
                        logger.info("Early stopping triggered")
                        break
        
        logger.info(f"Technique selector training completed. Best accuracy: {best_accuracy:.4f}")
    
    async def train_rl_optimizer(self):
        """Train reinforcement learning optimizer"""
        
        logger.info("Training RL optimizer")
        
        if len(self.training_data) < 500:
            logger.warning("Insufficient data for RL training")
            return
        
        # Prepare RL environment
        state_dim = len(self.training_data[0]["features"])
        action_dim = len(self.techniques)
        
        self.rl_optimizer = ReinforcementLearningOptimizer(state_dim, action_dim)
        
        # Create episodes from training data
        episodes = []
        for i in range(len(self.training_data) - 1):
            current = self.training_data[i]
            next_sample = self.training_data[i + 1]
            
            state = current["features"]
            action = self.technique_to_idx.get(current["technique"], 0)
            reward = current["improvement"]  # Use improvement as reward
            next_state = next_sample["features"]
            done = False
            
            episodes.append((state, action, reward, next_state, done))
        
        # Training loop
        for episode in range(1000):
            # Sample batch
            batch_size = min(32, len(episodes))
            batch_indices = np.random.choice(len(episodes), batch_size, replace=False)
            batch = [episodes[i] for i in batch_indices]
            
            # Add to memory
            self.rl_optimizer.memory.extend(batch)
            
            # Keep memory size manageable
            if len(self.rl_optimizer.memory) > 10000:
                self.rl_optimizer.memory = self.rl_optimizer.memory[-10000:]
            
            # Train
            loss = self.rl_optimizer.train_step(batch_size)
            
            if episode % 100 == 0 and loss is not None:
                logger.info(f"RL Episode {episode}: Loss: {loss:.4f}")
            
            # Update target network
            if episode % 50 == 0:
                self.rl_optimizer.target_network.load_state_dict(
                    self.rl_optimizer.q_network.state_dict()
                )
        
        logger.info("RL optimizer training completed")
    
    async def predict_quality(self, prompt: str, context: Dict = None) -> float:
        """Predict quality score for a prompt"""
        
        if self.quality_predictor is None:
            return 0.5  # Default prediction
        
        try:
            # Extract features
            embedding = self.embedding_extractor.extract_features([prompt])[0]
            linguistic_features = self.embedding_extractor.extract_linguistic_features(prompt)
            
            # Create feature vector
            feature_vector = np.concatenate([
                embedding,
                list(linguistic_features.values()),
                [0],  # Default technique
                [len(context) if context else 0]
            ])
            
            # Scale and predict
            feature_scaled = self.scaler.transform([feature_vector])
            feature_tensor = torch.FloatTensor(feature_scaled)
            
            self.quality_predictor.eval()
            with torch.no_grad():
                prediction = self.quality_predictor(feature_tensor)
                return prediction.item()
        
        except Exception as e:
            logger.error(f"Error predicting quality: {e}")
            return 0.5
    
    async def recommend_technique(self, prompt: str, context: Dict = None) -> str:
        """Recommend best technique for a prompt"""
        
        if self.technique_selector is None:
            return "metacognitive"  # Default recommendation
        
        try:
            # Extract features
            embedding = self.embedding_extractor.extract_features([prompt])[0]
            linguistic_features = self.embedding_extractor.extract_linguistic_features(prompt)
            
            # Create feature vector
            feature_vector = np.concatenate([
                embedding,
                list(linguistic_features.values()),
                [0],  # Default technique
                [len(context) if context else 0]
            ])
            
            # Scale and predict
            feature_scaled = self.scaler.transform([feature_vector])
            feature_tensor = torch.FloatTensor(feature_scaled)
            
            self.technique_selector.eval()
            with torch.no_grad():
                probabilities = self.technique_selector(feature_tensor)
                technique_idx = probabilities.argmax().item()
                return self.techniques[technique_idx]
        
        except Exception as e:
            logger.error(f"Error recommending technique: {e}")
            return "metacognitive"
    
    async def optimize_with_rl(self, prompt: str, context: Dict = None) -> Dict:
        """Use RL to optimize prompt strategy"""
        
        if self.rl_optimizer is None:
            return {"technique": "metacognitive", "confidence": 0.5}
        
        try:
            # Extract features for state
            embedding = self.embedding_extractor.extract_features([prompt])[0]
            linguistic_features = self.embedding_extractor.extract_linguistic_features(prompt)
            
            state = np.concatenate([
                embedding,
                list(linguistic_features.values()),
                [0],
                [len(context) if context else 0]
            ])
            
            # Select action
            action_idx = self.rl_optimizer.select_action(state)
            technique = self.techniques[action_idx]
            
            # Get confidence from Q-values
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                q_values = self.rl_optimizer.q_network(state_tensor)
                confidence = torch.softmax(q_values, dim=1).max().item()
            
            return {
                "technique": technique,
                "confidence": confidence,
                "q_values": q_values.numpy().tolist()
            }
        
        except Exception as e:
            logger.error(f"Error in RL optimization: {e}")
            return {"technique": "metacognitive", "confidence": 0.5}
    
    async def retrain_models(self, new_samples: List[TrainingSample]):
        """Retrain models with new data"""
        
        logger.info(f"Retraining models with {len(new_samples)} new samples")
        
        # Add new samples
        await self.collect_training_data(new_samples)
        
        # Retrain models
        await self.train_quality_predictor()
        await self.train_technique_selector()
        await self.train_rl_optimizer()
        
        logger.info("Model retraining completed")
    
    def get_model_performance_metrics(self) -> Dict:
        """Get performance metrics for all models"""
        
        metrics = {
            "training_samples": len(self.training_data),
            "models_trained": {
                "quality_predictor": self.quality_predictor is not None,
                "technique_selector": self.technique_selector is not None,
                "rl_optimizer": self.rl_optimizer is not None
            },
            "last_training": datetime.now().isoformat()
        }
        
        return metrics

class AutoMLHyperparameterOptimizer:
    """AutoML system for hyperparameter optimization"""
    
    def __init__(self):
        self.optimization_history = []
        self.best_params = {}
        
    async def optimize_technique_parameters(self, technique: str, search_space: Dict) -> Dict:
        """Optimize hyperparameters for a specific technique"""
        
        logger.info(f"Optimizing hyperparameters for {technique}")
        
        best_score = float('-inf')
        best_params = {}
        
        # Bayesian optimization approach
        for iteration in range(50):
            # Sample parameters
            params = self._sample_parameters(search_space)
            
            # Evaluate parameters
            score = await self._evaluate_parameters(technique, params)
            
            # Update best
            if score > best_score:
                best_score = score
                best_params = params
            
            self.optimization_history.append({
                "technique": technique,
                "params": params,
                "score": score,
                "iteration": iteration
            })
            
            logger.info(f"Iteration {iteration}: Score {score:.4f}")
        
        self.best_params[technique] = best_params
        return best_params
    
    def _sample_parameters(self, search_space: Dict) -> Dict:
        """Sample parameters from search space"""
        
        params = {}
        for param_name, param_config in search_space.items():
            if param_config["type"] == "float":
                params[param_name] = np.random.uniform(
                    param_config["min"], param_config["max"]
                )
            elif param_config["type"] == "int":
                params[param_name] = np.random.randint(
                    param_config["min"], param_config["max"] + 1
                )
            elif param_config["type"] == "choice":
                params[param_name] = np.random.choice(param_config["choices"])
        
        return params
    
    async def _evaluate_parameters(self, technique: str, params: Dict) -> float:
        """Evaluate parameter configuration"""
        
        # Simulate evaluation (in practice, this would run actual optimization)
        base_score = 0.7
        
        # Add parameter-based adjustments
        score_adjustment = 0
        for param_name, param_value in params.items():
            # Simulate parameter impact
            if isinstance(param_value, (int, float)):
                score_adjustment += np.random.normal(0, 0.05)
        
        final_score = base_score + score_adjustment + np.random.normal(0, 0.02)
        return np.clip(final_score, 0, 1)

class ModelEnsemble:
    """Ensemble of optimization models for improved performance"""
    
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.performance_history = {}
    
    def add_model(self, name: str, model, weight: float = 1.0):
        """Add model to ensemble"""
        self.models[name] = model
        self.weights[name] = weight
        self.performance_history[name] = []
    
    async def predict_ensemble(self, prompt: str, context: Dict = None) -> Dict:
        """Make ensemble prediction"""
        
        predictions = {}
        total_weight = 0
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict_quality'):
                    pred = await model.predict_quality(prompt, context)
                    predictions[name] = pred
                    total_weight += self.weights[name]
            except Exception as e:
                logger.error(f"Error with model {name}: {e}")
        
        if not predictions:
            return {"quality": 0.5, "confidence": 0.0}
        
        # Weighted average
        weighted_sum = sum(pred * self.weights[name] for name, pred in predictions.items())
        ensemble_prediction = weighted_sum / total_weight
        
        # Calculate confidence based on agreement
        variance = np.var(list(predictions.values()))
        confidence = 1.0 / (1.0 + variance)
        
        return {
            "quality": ensemble_prediction,
            "confidence": confidence,
            "individual_predictions": predictions
        }
    
    def update_weights(self, performance_scores: Dict[str, float]):
        """Update model weights based on performance"""
        
        for name, score in performance_scores.items():
            if name in self.models:
                self.performance_history[name].append(score)
                
                # Calculate recent performance
                recent_scores = self.performance_history[name][-10:]
                avg_performance = np.mean(recent_scores)
                
                # Update weight based on performance
                self.weights[name] = max(0.1, avg_performance)
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        for name in self.weights:
            self.weights[name] /= total_weight

# MLOps Pipeline Integration
class MLOpsPipeline:
    """MLOps pipeline for model lifecycle management"""
    
    def __init__(self):
        self.model_registry = {}
        self.experiment_tracker = {}
        self.deployment_configs = {}
    
    async def register_model(self, name: str, model, version: str, metadata: Dict):
        """Register model in model registry"""
        
        model_info = {
            "model": model,
            "version": version,
            "metadata": metadata,
            "registered_at": datetime.now(),
            "status": "registered"
        }
        
        if name not in self.model_registry:
            self.model_registry[name] = {}
        
        self.model_registry[name][version] = model_info
        logger.info(f"Registered model {name} version {version}")
    
    async def deploy_model(self, name: str, version: str, environment: str):
        """Deploy model to specified environment"""
        
        if name not in self.model_registry or version not in self.model_registry[name]:
            raise ValueError(f"Model {name} version {version} not found in registry")
        
        model_info = self.model_registry[name][version]
        
        deployment_config = {
            "model_name": name,
            "model_version": version,
            "environment": environment,
            "deployed_at": datetime.now(),
            "status": "active"
        }
        
        deployment_key = f"{name}_{version}_{environment}"
        self.deployment_configs[deployment_key] = deployment_config
        
        logger.info(f"Deployed model {name} version {version} to {environment}")
    
    async def monitor_model_drift(self, model_name: str, current_data: np.ndarray, 
                                reference_data: np.ndarray) -> Dict:
        """Monitor for model drift"""
        
        # Statistical tests for drift detection
        from scipy import stats
        
        drift_results = {}
        
        for feature_idx in range(current_data.shape[1]):
            current_feature = current_data[:, feature_idx]
            reference_feature = reference_data[:, feature_idx]
            
            # Kolmogorov-Smirnov test
            ks_statistic, ks_p_value = stats.ks_2samp(reference_feature, current_feature)
            
            # Population Stability Index
            psi = self._calculate_psi(reference_feature, current_feature)
            
            drift_results[f"feature_{feature_idx}"] = {
                "ks_statistic": ks_statistic,
                "ks_p_value": ks_p_value,
                "psi": psi,
                "drift_detected": ks_p_value < 0.05 or psi > 0.1
            }
        
        overall_drift = any(result["drift_detected"] for result in drift_results.values())
        
        return {
            "model_name": model_name,
            "overall_drift_detected": overall_drift,
            "feature_drift": drift_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_psi(self, reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Calculate Population Stability Index"""
        
        # Create bins based on reference data
        bin_edges = np.histogram_bin_edges(reference, bins=bins)
        
        # Calculate distributions
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        cur_counts, _ = np.histogram(current, bins=bin_edges)
        
        # Normalize to probabilities
        ref_probs = ref_counts / len(reference)
        cur_probs = cur_counts / len(current)
        
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        ref_probs = np.maximum(ref_probs, epsilon)
        cur_probs = np.maximum(cur_probs, epsilon)
        
        # Calculate PSI
        psi = np.sum((cur_probs - ref_probs) * np.log(cur_probs / ref_probs))
        
        return psi
    
    async def trigger_retraining(self, model_name: str, trigger_reason: str):
        """Trigger model retraining"""
        
        logger.info(f"Triggering retraining for {model_name}. Reason: {trigger_reason}")
        
        retraining_job = {
            "model_name": model_name,
            "trigger_reason": trigger_reason,
            "triggered_at": datetime.now(),
            "status": "queued"
        }
        
        # In practice, this would trigger a training pipeline
        # For now, we'll simulate the process
        await asyncio.sleep(1)  # Simulate job scheduling
        
        logger.info(f"Retraining job queued for {model_name}")
        return retraining_job