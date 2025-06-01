# Data Agent for OpenDistillery
# Specialized agent for data processing and analysis tasks

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

logger = logging.getLogger(__name__)

@dataclass
class DataContext:
    data: Union[pd.DataFrame, Dict[str, Any], List[Any], None] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    analysis_history: List[Dict[str, Any]] = field(default_factory=list)

class DataAgent(BaseAgent):
    def __init__(self, agent_id: str, models: Dict[str, ModelConfiguration], router: ModelRouter, system: CompoundAISystem):
        super().__init__(agent_id, models, router, system)
        self.capabilities = ["data_analysis", "data_processing", "data_visualization", "statistical_analysis"]
        self.data_context = DataContext()
        self.context.state["data_status"] = "empty"

    async def _process_task_internal(self, task: Dict[str, Any]) -> AgentResponse:
        """Process data-related tasks"""
        task_type = task.get("type", "data_analysis")
        
        logger.info(f"Data agent {self.agent_id} processing {task_type} task")
        
        try:
            if task_type == "data_load":
                return await self._handle_data_load(task)
            elif task_type == "data_analysis":
                return await self._handle_data_analysis(task)
            elif task_type == "data_processing":
                return await self._handle_data_processing(task)
            elif task_type == "data_visualization":
                return await self._handle_data_visualization(task)
            elif task_type == "statistical_analysis":
                return await self._handle_statistical_analysis(task)
            else:
                return await self._handle_general_data_task(task)
        except Exception as e:
            logger.error(f"Data task failed for agent {self.agent_id}: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Data processing error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"task_type": task_type}
            )

    async def _handle_data_load(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle data loading tasks"""
        data_source = task.get("data_source", task.get("data", None))
        data_format = task.get("format", "json")
        metadata = task.get("metadata", {})
        
        try:
            if isinstance(data_source, (pd.DataFrame, dict, list)):
                # Direct data provided
                data = data_source
            elif isinstance(data_source, str):
                # Assume file path or URL - in real implementation, would load from source
                if data_format == "csv":
                    data = pd.read_csv(data_source)
                elif data_format == "json":
                    data = pd.read_json(data_source)
                elif data_format == "excel":
                    data = pd.read_excel(data_source)
                else:
                    raise ValueError(f"Unsupported data format: {data_format}")
            else:
                raise ValueError("Invalid data source provided")
            
            # Store data in context
            self.data_context.data = data
            self.data_context.metadata = metadata
            self.context.state["data_status"] = "loaded"
            
            # Basic data summary
            summary = self._get_data_summary(data)
            
            logger.info(f"Data loaded for agent {self.agent_id}: {summary['data_type']} with shape {summary.get('shape', 'unknown')}")
            return AgentResponse(
                success=True,
                content=summary,
                confidence=0.9,
                metadata={"data_source": str(data_source)[:100], "format": data_format}
            )
        except Exception as e:
            logger.error(f"Data loading failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Data load error: {str(e)}",
                confidence=0.0,
                error=str(e)
            )

    async def _handle_data_analysis(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle data analysis tasks"""
        analysis_type = task.get("analysis_type", "summary")
        parameters = task.get("parameters", {})
        
        if self.data_context.data is None:
            return AgentResponse(
                success=False,
                content="No data loaded for analysis",
                confidence=0.0,
                error="No data available"
            )
        
        try:
            data = self.data_context.data
            result = {}
            
            if analysis_type == "summary":
                result = self._get_data_summary(data)
            elif analysis_type == "correlation":
                if isinstance(data, pd.DataFrame):
                    result = data.corr().to_dict()
                else:
                    result = {"error": "Correlation analysis requires tabular data"}
            elif analysis_type == "distribution":
                column = parameters.get("column")
                if isinstance(data, pd.DataFrame) and column in data.columns:
                    result = data[column].describe().to_dict()
                else:
                    result = {"error": f"Column {column} not found or invalid data type"}
            elif analysis_type == "missing_values":
                if isinstance(data, pd.DataFrame):
                    result = data.isnull().sum().to_dict()
                else:
                    result = {"error": "Missing value analysis requires tabular data"}
            else:
                result = {"error": f"Unsupported analysis type: {analysis_type}"}
            
            # Store analysis in history
            analysis_record = {
                "type": analysis_type,
                "parameters": parameters,
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            }
            self.data_context.analysis_history.append(analysis_record)
            
            return AgentResponse(
                success="error" not in result,
                content=result,
                confidence=0.85,
                metadata={"analysis_type": analysis_type}
            )
        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Data analysis error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"analysis_type": analysis_type}
            )

    async def _handle_data_processing(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle data processing tasks"""
        processing_type = task.get("processing_type", "clean")
        parameters = task.get("parameters", {})
        
        if self.data_context.data is None:
            return AgentResponse(
                success=False,
                content="No data loaded for processing",
                confidence=0.0,
                error="No data available"
            )
        
        try:
            data = self.data_context.data
            result_data = data
            metadata = {}
            
            if processing_type == "clean":
                if isinstance(data, pd.DataFrame):
                    if parameters.get("drop_na", False):
                        result_data = data.dropna()
                        metadata["rows_dropped"] = len(data) - len(result_data)
                    if parameters.get("fill_na") is not None:
                        result_data = data.fillna(parameters["fill_na"])
                        metadata["filled_values"] = data.isnull().sum().sum()
                    if "drop_columns" in parameters:
                        result_data = data.drop(columns=parameters["drop_columns"], errors="ignore")
                        metadata["columns_dropped"] = parameters["drop_columns"]
                else:
                    return AgentResponse(
                        success=False,
                        content="Cleaning operations require tabular data",
                        confidence=0.0,
                        error="Invalid data type"
                    )
            elif processing_type == "transform":
                if isinstance(data, pd.DataFrame):
                    if "apply_function" in parameters:
                        # In real implementation, would apply custom function
                        metadata["transformation"] = "Custom function applied"
                    if "normalize" in parameters and parameters["normalize"]:
                        numeric_cols = data.select_dtypes(include=[np.number]).columns
                        result_data[numeric_cols] = (data[numeric_cols] - data[numeric_cols].mean()) / data[numeric_cols].std()
                        metadata["normalized_columns"] = list(numeric_cols)
                else:
                    return AgentResponse(
                        success=False,
                        content="Transformation operations require tabular data",
                        confidence=0.0,
                        error="Invalid data type"
                    )
            elif processing_type == "filter":
                if isinstance(data, pd.DataFrame):
                    condition = parameters.get("condition", "")
                    if condition:
                        # In real implementation, would parse condition string
                        result_data = data  # Placeholder
                        metadata["filter_applied"] = condition
                        metadata["rows_filtered"] = 0
                else:
                    return AgentResponse(
                        success=False,
                        content="Filter operations require tabular data",
                        confidence=0.0,
                        error="Invalid data type"
                    )
            else:
                return AgentResponse(
                    success=False,
                    content=f"Unsupported processing type: {processing_type}",
                    confidence=0.0,
                    error="Unsupported operation"
                )
            
            # Update data context
            self.data_context.data = result_data
            self.context.state["data_status"] = "processed"
            
            return AgentResponse(
                success=True,
                content={"metadata": metadata, "data_shape": self._get_data_shape(result_data)},
                confidence=0.9,
                metadata={"processing_type": processing_type}
            )
        except Exception as e:
            logger.error(f"Data processing failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Data processing error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"processing_type": processing_type}
            )

    async def _handle_data_visualization(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle data visualization tasks"""
        viz_type = task.get("viz_type", "histogram")
        parameters = task.get("parameters", {})
        
        if self.data_context.data is None:
            return AgentResponse(
                success=False,
                content="No data loaded for visualization",
                confidence=0.0,
                error="No data available"
            )
        
        try:
            data = self.data_context.data
            if not isinstance(data, pd.DataFrame):
                return AgentResponse(
                    success=False,
                    content="Visualization requires tabular data",
                    confidence=0.0,
                    error="Invalid data type"
                )
            
            # In a real implementation, this would generate actual visualization code or images
            result = {
                "visualization_type": viz_type,
                "parameters": parameters,
                "status": "generated"
            }
            
            if viz_type == "histogram":
                column = parameters.get("column")
                if column and column in data.columns:
                    result["data_summary"] = {
                        "bins": parameters.get("bins", 30),
                        "range": [float(data[column].min()), float(data[column].max())]
                    }
                else:
                    result["error"] = f"Column {column} not found"
            elif viz_type == "scatter":
                x_col = parameters.get("x")
                y_col = parameters.get("y")
                if x_col in data.columns and y_col in data.columns:
                    result["data_summary"] = {
                        "points": len(data),
                        "x_range": [float(data[x_col].min()), float(data[x_col].max())],
                        "y_range": [float(data[y_col].min()), float(data[y_col].max())]
                    }
                else:
                    result["error"] = f"Columns {x_col} or {y_col} not found"
            elif viz_type == "boxplot":
                column = parameters.get("column")
                if column in data.columns:
                    result["data_summary"] = data[column].describe().to_dict()
                else:
                    result["error"] = f"Column {column} not found"
            else:
                result["error"] = f"Unsupported visualization type: {viz_type}"
            
            return AgentResponse(
                success="error" not in result,
                content=result,
                confidence=0.8,
                metadata={"viz_type": viz_type}
            )
        except Exception as e:
            logger.error(f"Data visualization failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Data visualization error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"viz_type": viz_type}
            )

    async def _handle_statistical_analysis(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle statistical analysis tasks"""
        analysis_type = task.get("analysis_type", "descriptive")
        parameters = task.get("parameters", {})
        
        if self.data_context.data is None:
            return AgentResponse(
                success=False,
                content="No data loaded for statistical analysis",
                confidence=0.0,
                error="No data available"
            )
        
        try:
            data = self.data_context.data
            if not isinstance(data, pd.DataFrame):
                return AgentResponse(
                    success=False,
                    content="Statistical analysis requires tabular data",
                    confidence=0.0,
                    error="Invalid data type"
                )
            
            result = {}
            if analysis_type == "descriptive":
                columns = parameters.get("columns", data.select_dtypes(include=[np.number]).columns.tolist())
                result = data[columns].describe().to_dict()
            elif analysis_type == "correlation":
                method = parameters.get("method", "pearson")
                result = data.corr(method=method).to_dict()
            elif analysis_type == "t_test":
                # In real implementation, would perform actual statistical test
                result = {
                    "test": "t-test",
                    "columns": parameters.get("columns", []),
                    "result": "placeholder result - t-statistic and p-value would be calculated here"
                }
            elif analysis_type == "regression":
                # In real implementation, would perform regression analysis
                result = {
                    "dependent_variable": parameters.get("dependent", ""),
                    "independent_variables": parameters.get("independent", []),
                    "result": "placeholder result - regression coefficients would be calculated here"
                }
            else:
                result = {"error": f"Unsupported statistical analysis type: {analysis_type}"}
            
            return AgentResponse(
                success="error" not in result,
                content=result,
                confidence=0.85,
                metadata={"analysis_type": analysis_type}
            )
        except Exception as e:
            logger.error(f"Statistical analysis failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Statistical analysis error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"analysis_type": analysis_type}
            )

    async def _handle_general_data_task(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle general data tasks"""
        action = task.get("action", "status")
        
        if action == "status":
            return AgentResponse(
                success=True,
                content={
                    "data_status": self.context.state.get("data_status", "empty"),
                    "data_summary": self._get_data_summary(self.data_context.data) if self.data_context.data is not None else {},
                    "analysis_history": len(self.data_context.analysis_history)
                },
                confidence=0.9
            )
        else:
            return AgentResponse(
                success=False,
                content=f"Unsupported data action: {action}",
                confidence=0.0,
                error="Unsupported action"
            )

    def _get_data_summary(self, data: Any) -> Dict[str, Any]:
        """Get summary of data"""
        if data is None:
            return {"data_type": "none", "status": "no data"}
        
        if isinstance(data, pd.DataFrame):
            return {
                "data_type": "dataframe",
                "shape": data.shape,
                "columns": list(data.columns),
                "dtypes": data.dtypes.astype(str).to_dict(),
                "memory_usage": data.memory_usage(deep=True).sum()
            }
        elif isinstance(data, dict):
            return {
                "data_type": "dict",
                "keys": list(data.keys()),
                "size": len(data)
            }
        elif isinstance(data, list):
            return {
                "data_type": "list",
                "length": len(data)
            }
        else:
            return {
                "data_type": str(type(data).__name__),
                "status": "unknown"
            }

    def _get_data_shape(self, data: Any) -> Union[tuple, str]:
        """Get shape of data"""
        if isinstance(data, pd.DataFrame):
            return data.shape
        elif isinstance(data, (list, dict)):
            return len(data)
        else:
            return "unknown" 