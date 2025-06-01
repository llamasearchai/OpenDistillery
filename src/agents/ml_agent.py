# Machine Learning Agent for OpenDistillery
# Specialized agent for ML model training and inference

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
import json
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

# Import base agent and core components
try:
    from ..base_agent import BaseAgent, AgentResponse
    from ...core.compound_system import ModelConfiguration, ModelRouter, CompoundAISystem
except ImportError:
    from src.agents.base_agent import BaseAgent, AgentResponse
    from src.core.compound_system import ModelConfiguration, ModelRouter, CompoundAISystem

# Import ML libraries
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    train_test_split = None
    StandardScaler = None
    LogisticRegression = None
    LinearRegression = None
    RandomForestClassifier = None
    RandomForestRegressor = None
    accuracy_score = None
    mean_squared_error = None
    classification_report = None
    joblib = None

logger = logging.getLogger(__name__)

@dataclass
class MLModelContext:
    model: Any = None
    model_type: str = ""
    model_metadata: Dict[str, Any] = field(default_factory=dict)
    training_data: Union[pd.DataFrame, None] = None
    training_metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

class MLAgent(BaseAgent):
    def __init__(self, agent_id: str, models: Dict[str, ModelConfiguration], router: ModelRouter, system: CompoundAISystem):
        super().__init__(agent_id, models, router, system)
        self.capabilities = ["machine_learning", "model_training", "model_inference", "model_evaluation"]
        self.ml_context = MLModelContext()
        self.context.state["model_status"] = "untrained"
        if not ML_AVAILABLE:
            logger.warning(f"Machine learning libraries not available for agent {agent_id}")

    async def _process_task_internal(self, task: Dict[str, Any]) -> AgentResponse:
        """Process machine learning tasks"""
        task_type = task.get("type", "model_training")
        
        logger.info(f"ML agent {self.agent_id} processing {task_type} task")
        
        if not ML_AVAILABLE:
            return AgentResponse(
                success=False,
                content="Machine learning libraries not available",
                confidence=0.0,
                error="ML dependencies missing"
            )
        
        try:
            if task_type == "model_training":
                return await self._handle_model_training(task)
            elif task_type == "model_inference":
                return await self._handle_model_inference(task)
            elif task_type == "model_evaluation":
                return await self._handle_model_evaluation(task)
            elif task_type == "model_save":
                return await self._handle_model_save(task)
            elif task_type == "model_load":
                return await self._handle_model_load(task)
            else:
                return await self._handle_general_ml_task(task)
        except Exception as e:
            logger.error(f"ML task failed for agent {self.agent_id}: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"ML processing error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"task_type": task_type}
            )

    async def _handle_model_training(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle model training tasks"""
        data = task.get("data")
        model_type = task.get("model_type", "classification")
        parameters = task.get("parameters", {})
        target_column = parameters.get("target_column")
        test_size = parameters.get("test_size", 0.2)
        random_state = parameters.get("random_state", 42)
        
        if data is None or not isinstance(data, pd.DataFrame):
            return AgentResponse(
                success=False,
                content="Valid DataFrame required for training",
                confidence=0.0,
                error="Invalid data"
            )
        
        if not target_column or target_column not in data.columns:
            return AgentResponse(
                success=False,
                content=f"Target column {target_column} not found in data",
                confidence=0.0,
                error="Invalid target column"
            )
        
        try:
            # Prepare data
            X = data.drop(columns=[target_column])
            y = data[target_column]
            
            # Handle categorical variables
            X = pd.get_dummies(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Select and train model
            if model_type == "classification":
                if len(np.unique(y)) > 2:
                    model = RandomForestClassifier(**parameters.get("model_params", {}))
                else:
                    model = LogisticRegression(**parameters.get("model_params", {}))
            elif model_type == "regression":
                model = RandomForestRegressor(**parameters.get("model_params", {}))
            else:
                return AgentResponse(
                    success=False,
                    content=f"Unsupported model type: {model_type}",
                    confidence=0.0,
                    error="Unsupported model type"
                )
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Store model and data in context
            self.ml_context.model = model
            self.ml_context.model_type = model_type
            self.ml_context.model_metadata = {
                "features": list(X.columns),
                "target": target_column,
                "training_date": str(pd.Timestamp.now()),
                "parameters": parameters
            }
            self.ml_context.training_data = data
            self.ml_context.training_metadata = {
                "shape": data.shape,
                "train_size": len(X_train),
                "test_size": len(X_test)
            }
            self.context.state["model_status"] = "trained"
            
            # Evaluate model
            train_pred = model.predict(X_train_scaled)
            test_pred = model.predict(X_test_scaled)
            
            if model_type == "classification":
                train_metric = accuracy_score(y_train, train_pred)
                test_metric = accuracy_score(y_test, test_pred)
                detailed_metrics = classification_report(y_test, test_pred, output_dict=True)
            else:
                train_metric = mean_squared_error(y_train, train_pred, squared=False)
                test_metric = mean_squared_error(y_test, test_pred, squared=False)
                detailed_metrics = {"rmse_train": train_metric, "rmse_test": test_metric}
            
            self.ml_context.performance_metrics = {
                "train_metric": train_metric,
                "test_metric": test_metric,
                "detailed_metrics": detailed_metrics
            }
            
            logger.info(f"Model trained for agent {self.agent_id}: {model_type} with test metric {test_metric}")
            return AgentResponse(
                success=True,
                content={
                    "model_type": model_type,
                    "performance": {
                        "train": train_metric,
                        "test": test_metric
                    },
                    "data_shape": data.shape
                },
                confidence=0.9,
                metadata={"model_type": model_type}
            )
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Model training error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"model_type": model_type}
            )

    async def _handle_model_inference(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle model inference tasks"""
        data = task.get("data")
        parameters = task.get("parameters", {})
        
        if self.ml_context.model is None or self.context.state.get("model_status") != "trained":
            return AgentResponse(
                success=False,
                content="No trained model available for inference",
                confidence=0.0,
                error="Model not trained"
            )
        
        if data is None or not isinstance(data, (pd.DataFrame, np.ndarray, list)):
            return AgentResponse(
                success=False,
                content="Valid data required for inference",
                confidence=0.0,
                error="Invalid data"
            )
        
        try:
            # Prepare data
            if isinstance(data, (list, np.ndarray)):
                data = pd.DataFrame(data, columns=self.ml_context.model_metadata.get("features", []))
            
            # Handle categorical variables
            data = pd.get_dummies(data)
            
            # Ensure all expected features are present
            for feature in self.ml_context.model_metadata.get("features", []):
                if feature not in data.columns:
                    data[feature] = 0
            
            # Order columns as expected by model
            data = data[self.ml_context.model_metadata.get("features", data.columns)]
            
            # Scale features if needed (would store scaler in real implementation)
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Make predictions
            predictions = self.ml_context.model.predict(data_scaled)
            
            # Format predictions
            if parameters.get("return_probabilities", False) and hasattr(self.ml_context.model, "predict_proba"):
                probabilities = self.ml_context.model.predict_proba(data_scaled)
                result = {
                    "predictions": predictions.tolist(),
                    "probabilities": probabilities.tolist()
                }
            else:
                result = {"predictions": predictions.tolist()}
            
            logger.info(f"Inference completed for agent {self.agent_id}: {len(predictions)} predictions made")
            return AgentResponse(
                success=True,
                content=result,
                confidence=0.85,
                metadata={"model_type": self.ml_context.model_type, "data_size": len(predictions)}
            )
        except Exception as e:
            logger.error(f"Model inference failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Model inference error: {str(e)}",
                confidence=0.0,
                error=str(e)
            )

    async def _handle_model_evaluation(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle model evaluation tasks"""
        data = task.get("data", self.ml_context.training_data)
        parameters = task.get("parameters", {})
        
        if self.ml_context.model is None or self.context.state.get("model_status") != "trained":
            return AgentResponse(
                success=False,
                content="No trained model available for evaluation",
                confidence=0.0,
                error="Model not trained"
            )
        
        if data is None or not isinstance(data, pd.DataFrame):
            return AgentResponse(
                success=False,
                content="Valid DataFrame required for evaluation",
                confidence=0.0,
                error="Invalid data"
            )
        
        try:
            # Prepare data
            target_column = self.ml_context.model_metadata.get("target")
            if target_column not in data.columns:
                return AgentResponse(
                    success=False,
                    content=f"Target column {target_column} not found in evaluation data",
                    confidence=0.0,
                    error="Missing target column"
                )
            
            X = data.drop(columns=[target_column])
            y = data[target_column]
            
            # Handle categorical variables
            X = pd.get_dummies(X)
            
            # Ensure all expected features are present
            for feature in self.ml_context.model_metadata.get("features", []):
                if feature not in X.columns:
                    X[feature] = 0
            
            # Order columns as expected by model
            X = X[self.ml_context.model_metadata.get("features", X.columns)]
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Make predictions
            predictions = self.ml_context.model.predict(X_scaled)
            
            # Calculate metrics
            model_type = self.ml_context.model_type
            if model_type == "classification":
                accuracy = accuracy_score(y, predictions)
                report = classification_report(y, predictions, output_dict=True)
                metrics = {
                    "accuracy": accuracy,
                    "classification_report": report
                }
            else:  # regression
                rmse = mean_squared_error(y, predictions, squared=False)
                r2 = self.ml_context.model.score(X_scaled, y)
                metrics = {
                    "rmse": rmse,
                    "r2_score": r2
                }
            
            # Update performance metrics
            self.ml_context.performance_metrics.update({
                "evaluation_metrics": metrics,
                "evaluation_date": str(pd.Timestamp.now())
            })
            
            logger.info(f"Model evaluation completed for agent {self.agent_id}: {model_type} model")
            return AgentResponse(
                success=True,
                content=metrics,
                confidence=0.9,
                metadata={"model_type": model_type, "data_size": len(data)}
            )
        except Exception as e:
            logger.error(f"Model evaluation failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Model evaluation error: {str(e)}",
                confidence=0.0,
                error=str(e)
            )

    async def _handle_model_save(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle model saving tasks"""
        filepath = task.get("filepath")
        
        if self.ml_context.model is None or self.context.state.get("model_status") != "trained":
            return AgentResponse(
                success=False,
                content="No trained model available to save",
                confidence=0.0,
                error="Model not trained"
            )
        
        if not filepath:
            return AgentResponse(
                success=False,
                content="Filepath required to save model",
                confidence=0.0,
                error="Missing filepath"
            )
        
        try:
            # Save model
            joblib.dump(self.ml_context.model, filepath)
            
            # Save metadata
            metadata_path = filepath + ".metadata.json"
            with open(metadata_path, "w") as f:
                json.dump({
                    "model_type": self.ml_context.model_type,
                    "metadata": self.ml_context.model_metadata,
                    "performance": self.ml_context.performance_metrics
                }, f, indent=2)
            
            logger.info(f"Model saved for agent {self.agent_id} to {filepath}")
            return AgentResponse(
                success=True,
                content={"filepath": filepath, "model_type": self.ml_context.model_type},
                confidence=0.95,
                metadata={"save_path": filepath}
            )
        except Exception as e:
            logger.error(f"Model saving failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Model save error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"filepath": filepath}
            )

    async def _handle_model_load(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle model loading tasks"""
        filepath = task.get("filepath")
        
        if not filepath:
            return AgentResponse(
                success=False,
                content="Filepath required to load model",
                confidence=0.0,
                error="Missing filepath"
            )
        
        try:
            # Load model
            model = joblib.load(filepath)
            
            # Load metadata if available
            metadata_path = filepath + ".metadata.json"
            metadata = {}
            model_type = "unknown"
            performance_metrics = {}
            
            try:
                with open(metadata_path, "r") as f:
                    metadata_json = json.load(f)
                    model_type = metadata_json.get("model_type", "unknown")
                    metadata = metadata_json.get("metadata", {})
                    performance_metrics = metadata_json.get("performance", {})
            except FileNotFoundError:
                logger.warning(f"Metadata file not found at {metadata_path}")
            
            # Update context
            self.ml_context.model = model
            self.ml_context.model_type = model_type
            self.ml_context.model_metadata = metadata
            self.ml_context.performance_metrics = performance_metrics
            self.context.state["model_status"] = "trained"
            
            logger.info(f"Model loaded for agent {self.agent_id} from {filepath}")
            return AgentResponse(
                success=True,
                content={"filepath": filepath, "model_type": model_type},
                confidence=0.9,
                metadata={"load_path": filepath}
            )
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Model load error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"filepath": filepath}
            )

    async def _handle_general_ml_task(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle general ML tasks"""
        action = task.get("action", "status")
        
        if action == "status":
            return AgentResponse(
                success=True,
                content={
                    "model_status": self.context.state.get("model_status", "untrained"),
                    "model_type": self.ml_context.model_type,
                    "performance_metrics": self.ml_context.performance_metrics
                },
                confidence=0.9
            )
        else:
            return AgentResponse(
                success=False,
                content=f"Unsupported ML action: {action}",
                confidence=0.0,
                error="Unsupported action"
            ) 