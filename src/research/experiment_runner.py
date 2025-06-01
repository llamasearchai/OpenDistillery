"""
OpenDistillery Research & Experimentation Framework
Advanced experimentation platform for AI research with enterprise-grade
A/B testing, statistical analysis, and publication-ready insights.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor
import pickle
import hashlib

import structlog

logger = structlog.get_logger(__name__)

class ExperimentType(Enum):
    AB_TEST = "ab_test"
    MULTI_VARIANT = "multi_variant"
    ABLATION_STUDY = "ablation_study"
    PARAMETER_SWEEP = "parameter_sweep"
    TECHNIQUE_COMPARISON = "technique_comparison"
    ARCHITECTURE_EVALUATION = "architecture_evaluation"
    PRODUCTION_SHADOW = "production_shadow"

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExperimentConfiguration:
    """Configuration for an experiment"""
    experiment_id: str
    experiment_type: ExperimentType
    name: str
    description: str
    hypothesis: str
    success_criteria: Dict[str, Any]
    duration_hours: Optional[int] = None
    sample_size: Optional[int] = None
    significance_level: float = 0.05
    power: float = 0.8
    randomization_strategy: str = "balanced"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentVariant:
    """Variant configuration for experiments"""
    variant_id: str
    name: str
    description: str
    configuration: Dict[str, Any]
    traffic_allocation: float = 0.5
    is_control: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentMetric:
    """Metric definition for experiments"""
    metric_name: str
    metric_type: str  # "primary", "secondary", "guardrail"
    description: str
    aggregation_method: str = "mean"
    direction: str = "increase"  # "increase", "decrease", "neutral"
    threshold: Optional[float] = None
    statistical_test: str = "t_test"

@dataclass
class ExperimentResult:
    """Individual experiment result data point"""
    experiment_id: str
    variant_id: str
    metric_name: str
    value: float
    sample_size: int
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class StatisticalAnalyzer:
    """Advanced statistical analysis for experiments"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    def analyze_experiment(self, 
                          experiment_id: str,
                          results: List[ExperimentResult],
                          variants: List[ExperimentVariant],
                          metrics: List[ExperimentMetric]) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis"""
        analysis = {
            "experiment_id": experiment_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "sample_sizes": {},
            "metric_analyses": {}
        }
        
        # Group results by metric and variant
        results_by_metric = self._group_results_by_metric(results)
        
        # Analyze each metric
        for metric in metrics:
            if metric.metric_name in results_by_metric:
                metric_analysis = self._analyze_metric(
                    metric, results_by_metric[metric.metric_name], variants
                )
                analysis["metric_analyses"][metric.metric_name] = metric_analysis
        
        # Overall experiment summary
        analysis["overall_summary"] = self._generate_overall_summary(analysis["metric_analyses"])
        
        return analysis
    
    def _group_results_by_metric(self, results: List[ExperimentResult]) -> Dict[str, Dict[str, List[float]]]:
        """Group results by metric and variant"""
        grouped = {}
        
        for result in results:
            metric_name = result.metric_name
            variant_id = result.variant_id
            
            if metric_name not in grouped:
                grouped[metric_name] = {}
            
            if variant_id not in grouped[metric_name]:
                grouped[metric_name][variant_id] = []
            
            grouped[metric_name][variant_id].append(result.value)
        
        return grouped
    
    def _analyze_metric(self, 
                       metric: ExperimentMetric,
                       metric_results: Dict[str, List[float]],
                       variants: List[ExperimentVariant]) -> Dict[str, Any]:
        """Analyze individual metric"""
        analysis = {
            "metric_name": metric.metric_name,
            "metric_type": metric.metric_type,
            "sample_sizes": {},
            "descriptive_stats": {},
            "statistical_tests": {},
            "effect_sizes": {},
            "confidence_intervals": {}
        }
        
        # Calculate descriptive statistics
        for variant_id, values in metric_results.items():
            if values:
                analysis["sample_sizes"][variant_id] = len(values)
                analysis["descriptive_stats"][variant_id] = {
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "q25": np.percentile(values, 25),
                    "q75": np.percentile(values, 75)
                }
        
        # Perform statistical tests
        if len(metric_results) >= 2:
            analysis["statistical_tests"] = self._perform_statistical_tests(
                metric, metric_results, variants
            )
        
        return analysis
    
    def _perform_statistical_tests(self, 
                                 metric: ExperimentMetric,
                                 metric_results: Dict[str, List[float]],
                                 variants: List[ExperimentVariant]) -> Dict[str, Any]:
        """Perform statistical significance tests"""
        tests = {}
        
        # Find control variant
        control_variant = next((v for v in variants if v.is_control), None)
        if not control_variant:
            return tests
        
        control_data = metric_results.get(control_variant.variant_id, [])
        if not control_data:
            return tests
        
        # Test each treatment against control
        for variant in variants:
            if variant.is_control:
                continue
                
            treatment_data = metric_results.get(variant.variant_id, [])
            if not treatment_data:
                continue
            
            # Perform appropriate statistical test
            if metric.statistical_test == "t_test":
                test_result = self._perform_t_test(control_data, treatment_data)
            elif metric.statistical_test == "mann_whitney":
                test_result = self._perform_mann_whitney(control_data, treatment_data)
            elif metric.statistical_test == "chi_square":
                test_result = self._perform_chi_square(control_data, treatment_data)
            else:
                test_result = self._perform_t_test(control_data, treatment_data)  # Default
            
            test_result["variant_comparison"] = f"{variant.variant_id}_vs_{control_variant.variant_id}"
            test_result["effect_size"] = self._calculate_effect_size(control_data, treatment_data)
            test_result["confidence_interval"] = self._calculate_confidence_interval(
                control_data, treatment_data
            )
            
            tests[variant.variant_id] = test_result
        
        return tests
    
    def _perform_t_test(self, control: List[float], treatment: List[float]) -> Dict[str, Any]:
        """Perform independent t-test"""
        if len(control) < 2 or len(treatment) < 2:
            return {"error": "Insufficient sample size"}
        
        t_stat, p_value = stats.ttest_ind(treatment, control)
        
        return {
            "test_type": "independent_t_test",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "degrees_of_freedom": len(control) + len(treatment) - 2
        }
    
    def _perform_mann_whitney(self, control: List[float], treatment: List[float]) -> Dict[str, Any]:
        """Perform Mann-Whitney U test"""
        if len(control) < 2 or len(treatment) < 2:
            return {"error": "Insufficient sample size"}
        
        u_stat, p_value = stats.mannwhitneyu(treatment, control, alternative='two-sided')
        
        return {
            "test_type": "mann_whitney_u",
            "u_statistic": float(u_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05
        }
    
    def _perform_chi_square(self, control: List[float], treatment: List[float]) -> Dict[str, Any]:
        """Perform chi-square test for categorical data"""
        # Convert to counts (assuming binary outcomes)
        control_success = sum(1 for x in control if x > 0.5)
        control_failure = len(control) - control_success
        treatment_success = sum(1 for x in treatment if x > 0.5)
        treatment_failure = len(treatment) - treatment_success
        
        observed = np.array([[control_success, control_failure],
                           [treatment_success, treatment_failure]])
        
        if observed.sum() == 0:
            return {"error": "No observations"}
        
        chi2, p_value, dof, expected = stats.chi2_contingency(observed)
        
        return {
            "test_type": "chi_square",
            "chi2_statistic": float(chi2),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "degrees_of_freedom": dof
        }
    
    def _calculate_effect_size(self, control: List[float], treatment: List[float]) -> Dict[str, Any]:
        """Calculate effect sizes"""
        if not control or not treatment:
            return {}
        
        control_mean = np.mean(control)
        treatment_mean = np.mean(treatment)
        
        # Cohen's d
        pooled_std = np.sqrt(((len(control) - 1) * np.var(control) + 
                             (len(treatment) - 1) * np.var(treatment)) /
                            (len(control) + len(treatment) - 2))
        
        cohens_d = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        
        # Relative difference
        relative_diff = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0
        
        return {
            "cohens_d": cohens_d,
            "relative_difference": relative_diff,
            "absolute_difference": treatment_mean - control_mean,
            "interpretation": self._interpret_effect_size(abs(cohens_d))
        }
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        if cohens_d < 0.2:
            return "negligible"
        elif cohens_d < 0.5:
            return "small"
        elif cohens_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def _calculate_confidence_interval(self, 
                                     control: List[float], 
                                     treatment: List[float],
                                     confidence: float = 0.95) -> Dict[str, Any]:
        """Calculate confidence interval for difference in means"""
        if not control or not treatment:
            return {}
        
        control_mean = np.mean(control)
        treatment_mean = np.mean(treatment)
        control_se = stats.sem(control)
        treatment_se = stats.sem(treatment)
        
        # Standard error of difference
        se_diff = np.sqrt(control_se**2 + treatment_se**2)
        
        # Degrees of freedom (Welch's)
        df = (control_se**2 + treatment_se**2)**2 / (
            control_se**4 / (len(control) - 1) + treatment_se**4 / (len(treatment) - 1)
        )
        
        # Critical value
        alpha = 1 - confidence
        t_critical = stats.t.ppf(1 - alpha/2, df)
        
        # Difference and margin of error
        diff = treatment_mean - control_mean
        margin_error = t_critical * se_diff
        
        return {
            "difference": diff,
            "lower_bound": diff - margin_error,
            "upper_bound": diff + margin_error,
            "confidence_level": confidence,
            "margin_of_error": margin_error
        }
    
    def _generate_overall_summary(self, metric_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall experiment summary"""
        summary = {
            "total_metrics": len(metric_analyses),
            "significant_metrics": 0,
            "primary_metric_results": {},
            "recommendations": []
        }
        
        for metric_name, analysis in metric_analyses.items():
            if analysis.get("metric_type") == "primary":
                summary["primary_metric_results"][metric_name] = analysis
            
            # Count significant results
            tests = analysis.get("statistical_tests", {})
            for test in tests.values():
                if test.get("significant", False):
                    summary["significant_metrics"] += 1
                    break
        
        # Generate recommendations
        if summary["significant_metrics"] > 0:
            summary["recommendations"].append("Significant results detected - consider deployment")
        else:
            summary["recommendations"].append("No significant results - continue testing or iterate")
        
        return summary

class ExperimentRunner:
    """
    Advanced experiment runner for AI research and enterprise A/B testing
    """
    
    def __init__(self, storage_backend: str = "local"):
        self.experiments: Dict[str, 'Experiment'] = {}
        self.running_experiments: Set[str] = set()
        self.results_store: Dict[str, List[ExperimentResult]] = {}
        
        # Analysis components
        self.statistical_analyzer = StatisticalAnalyzer()
        self.visualization_engine = VisualizationEngine()
        
        # Research tracking
        self.research_insights: List[Dict[str, Any]] = []
        self.publication_queue: List[Dict[str, Any]] = []
        
        # Performance monitoring
        self.experiment_metrics = {
            "total_experiments": 0,
            "successful_experiments": 0,
            "average_duration_hours": 0.0,
            "insights_generated": 0
        }
        
        logger.info("Experiment runner initialized")
    
    def create_experiment(self, 
                         config: ExperimentConfiguration,
                         variants: List[ExperimentVariant],
                         metrics: List[ExperimentMetric]) -> 'Experiment':
        """Create a new experiment"""
        experiment = Experiment(
            config=config,
            variants=variants,
            metrics=metrics,
            runner=self
        )
        
        self.experiments[config.experiment_id] = experiment
        self.results_store[config.experiment_id] = []
        
        logger.info(f"Created experiment: {config.experiment_id}")
        return experiment
    
    def create_technique_comparison(self,
                                  experiment_name: str,
                                  techniques: List[str],
                                  test_dataset: List[Dict[str, Any]],
                                  evaluation_metrics: List[str]) -> 'Experiment':
        """Create experiment to compare AI techniques"""
        experiment_id = f"technique_comp_{uuid.uuid4().hex[:8]}"
        
        config = ExperimentConfiguration(
            experiment_id=experiment_id,
            experiment_type=ExperimentType.TECHNIQUE_COMPARISON,
            name=experiment_name,
            description=f"Comparing techniques: {', '.join(techniques)}",
            hypothesis=f"Different AI techniques will show varying performance on {experiment_name}",
            success_criteria={metric: {"direction": "increase"} for metric in evaluation_metrics}
        )
        
        # Create variants for each technique
        variants = []
        traffic_per_variant = 1.0 / len(techniques)
        
        for i, technique in enumerate(techniques):
            variants.append(ExperimentVariant(
                variant_id=f"technique_{i}",
                name=technique,
                description=f"Using {technique} reasoning technique",
                configuration={
                    "technique": technique,
                    "test_data": test_dataset
                },
                traffic_allocation=traffic_per_variant,
                is_control=(i == 0)
            ))
        
        # Create metrics
        metrics = []
        for j, metric_name in enumerate(evaluation_metrics):
            metrics.append(ExperimentMetric(
                metric_name=metric_name,
                metric_type="primary" if j == 0 else "secondary",
                description=f"Evaluation metric: {metric_name}",
                direction="increase"
            ))
        
        return self.create_experiment(config, variants, metrics)
    
    def create_architecture_evaluation(self,
                                     experiment_name: str,
                                     architectures: List[Dict[str, Any]],
                                     evaluation_criteria: List[str]) -> 'Experiment':
        """Create experiment to evaluate different system architectures"""
        experiment_id = f"arch_eval_{uuid.uuid4().hex[:8]}"
        
        config = ExperimentConfiguration(
            experiment_id=experiment_id,
            experiment_type=ExperimentType.ARCHITECTURE_EVALUATION,
            name=experiment_name,
            description=f"Evaluating {len(architectures)} system architectures",
            hypothesis="Different architectures will show distinct performance characteristics",
            success_criteria={criterion: {"direction": "increase"} for criterion in evaluation_criteria}
        )
        
        # Create variants for each architecture
        variants = []
        for i, arch_config in enumerate(architectures):
            variants.append(ExperimentVariant(
                variant_id=f"architecture_{i}",
                name=arch_config.get("name", f"Architecture {i}"),
                description=arch_config.get("description", ""),
                configuration=arch_config,
                traffic_allocation=1.0 / len(architectures),
                is_control=(i == 0)
            ))
        
        # Create metrics
        metrics = []
        for j, criterion in enumerate(evaluation_criteria):
            metrics.append(ExperimentMetric(
                metric_name=criterion,
                metric_type="primary" if j == 0 else "secondary",
                description=f"Architecture criterion: {criterion}",
                direction="increase"
            ))
        
        return self.create_experiment(config, variants, metrics)
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.DRAFT:
            logger.error(f"Experiment {experiment_id} is not in draft status")
            return False
        
        # Validate experiment
        if not experiment.validate():
            logger.error(f"Experiment {experiment_id} validation failed")
            return False
        
        # Start experiment
        experiment.start()
        self.running_experiments.add(experiment_id)
        
        # Start monitoring
        monitoring_task = asyncio.create_task(self._monitor_experiment(experiment_id))
        
        self.experiment_metrics["total_experiments"] += 1
        
        logger.info(f"Started experiment: {experiment_id}")
        return True
    
    async def stop_experiment(self, experiment_id: str, reason: str = "manual_stop") -> bool:
        """Stop a running experiment"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.stop(reason)
        
        if experiment_id in self.running_experiments:
            self.running_experiments.remove(experiment_id)
        
        # Generate final analysis
        analysis = await self._generate_final_analysis(experiment_id)
        
        # Check for research insights
        insights = self._extract_research_insights(analysis)
        if insights:
            self.research_insights.extend(insights)
            self.experiment_metrics["insights_generated"] += len(insights)
        
        logger.info(f"Stopped experiment: {experiment_id}")
        return True
    
    async def _monitor_experiment(self, experiment_id: str) -> None:
        """Monitor running experiment"""
        experiment = self.experiments[experiment_id]
        
        while experiment.status == ExperimentStatus.RUNNING:
            try:
                # Check stopping conditions
                if experiment.should_stop():
                    await self.stop_experiment(experiment_id, "auto_stop")
                    break
                
                # Collect interim results
                await self._collect_interim_results(experiment_id)
                
                # Check for early stopping
                if await self._check_early_stopping(experiment_id):
                    await self.stop_experiment(experiment_id, "early_stopping")
                    break
                
                # Wait before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error monitoring experiment {experiment_id}: {str(e)}")
                await self.stop_experiment(experiment_id, f"monitoring_error: {str(e)}")
                break
    
    async def _collect_interim_results(self, experiment_id: str) -> None:
        """Collect interim results for experiment"""
        experiment = self.experiments[experiment_id]
        
        # Simulate result collection (in real implementation, would connect to actual systems)
        for variant in experiment.variants:
            for metric in experiment.metrics:
                # Generate realistic simulated data
                if variant.is_control:
                    base_value = 0.75  # Control baseline
                else:
                    base_value = 0.78  # Treatment improvement
                
                value = np.random.normal(base_value, 0.1)
                value = max(0, min(1, value))  # Clamp to [0, 1]
                
                result = ExperimentResult(
                    experiment_id=experiment_id,
                    variant_id=variant.variant_id,
                    metric_name=metric.metric_name,
                    value=value,
                    sample_size=np.random.randint(10, 50),
                    timestamp=datetime.now()
                )
                
                self.results_store[experiment_id].append(result)
    
    async def _check_early_stopping(self, experiment_id: str) -> bool:
        """Check if experiment should stop early due to statistical significance"""
        experiment = self.experiments[experiment_id]
        results = self.results_store[experiment_id]
        
        if len(results) < 100:  # Need minimum data
            return False
        
        # Perform interim analysis
        analysis = self.statistical_analyzer.analyze_experiment(
            experiment_id, results, experiment.variants, experiment.metrics
        )
        
        # Check for strong significance on primary metrics
        for metric in experiment.metrics:
            if metric.metric_type == "primary":
                metric_analysis = analysis["metric_analyses"].get(metric.metric_name, {})
                tests = metric_analysis.get("statistical_tests", {})
                
                for test in tests.values():
                    if test.get("significant", False) and test.get("p_value", 1.0) < 0.01:
                        # Strong significance - consider early stopping
                        effect_size = test.get("effect_size", {}).get("cohens_d", 0)
                        if abs(effect_size) > 0.3:  # Meaningful effect
                            logger.info(f"Early stopping conditions met for {experiment_id}")
                            return True
        
        return False
    
    async def _generate_final_analysis(self, experiment_id: str) -> Dict[str, Any]:
        """Generate comprehensive final analysis"""
        experiment = self.experiments[experiment_id]
        results = self.results_store[experiment_id]
        
        # Statistical analysis
        statistical_analysis = self.statistical_analyzer.analyze_experiment(
            experiment_id, results, experiment.variants, experiment.metrics
        )
        
        # Business insights
        business_insights = self._generate_business_insights(experiment, statistical_analysis)
        
        # Recommendations
        recommendations = self._generate_recommendations(experiment, statistical_analysis)
        
        # Research potential
        research_potential = self._assess_research_potential(experiment, statistical_analysis)
        
        final_analysis = {
            "experiment_id": experiment_id,
            "statistical_analysis": statistical_analysis,
            "business_insights": business_insights,
            "recommendations": recommendations,
            "research_potential": research_potential,
            "generated_at": datetime.now().isoformat()
        }
        
        # Store analysis
        experiment.final_analysis = final_analysis
        
        return final_analysis
    
    def _generate_business_insights(self, experiment: 'Experiment', analysis: Dict[str, Any]) -> List[str]:
        """Generate business insights from experiment results"""
        insights = []
        
        metric_analyses = analysis.get("metric_analyses", {})
        
        for metric_name, metric_analysis in metric_analyses.items():
            tests = metric_analysis.get("statistical_tests", {})
            
            for variant_id, test in tests.items():
                if test.get("significant", False):
                    effect = test.get("effect_size", {})
                    relative_diff = effect.get("relative_difference", 0)
                    
                    if relative_diff > 0.05:  # 5% improvement
                        insights.append(
                            f"{variant_id} shows {relative_diff:.1%} improvement in {metric_name}"
                        )
                    elif relative_diff < -0.05:  # 5% degradation
                        insights.append(
                            f"{variant_id} shows {abs(relative_diff):.1%} degradation in {metric_name}"
                        )
        
        # Add experiment-specific insights
        if experiment.config.experiment_type == ExperimentType.TECHNIQUE_COMPARISON:
            insights.append("Technique comparison reveals performance differences across methods")
        elif experiment.config.experiment_type == ExperimentType.ARCHITECTURE_EVALUATION:
            insights.append("Architecture evaluation shows distinct performance characteristics")
        
        return insights
    
    def _generate_recommendations(self, experiment: 'Experiment', analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Statistical significance recommendations
        overall_summary = analysis.get("overall_summary", {})
        significant_metrics = overall_summary.get("significant_metrics", 0)
        
        if significant_metrics > 0:
            recommendations.append("Deploy winning variant based on significant results")
        else:
            recommendations.append("Continue testing or iterate on variants")
        
        # Sample size recommendations
        metric_analyses = analysis.get("metric_analyses", {})
        for metric_name, metric_analysis in metric_analyses.items():
            sample_sizes = metric_analysis.get("sample_sizes", {})
            min_sample_size = min(sample_sizes.values()) if sample_sizes else 0
            
            if min_sample_size < 100:
                recommendations.append(f"Increase sample size for {metric_name} (current min: {min_sample_size})")
        
        # Business impact recommendations
        for metric_name, metric_analysis in metric_analyses.items():
            if metric_analysis.get("metric_type") == "primary":
                tests = metric_analysis.get("statistical_tests", {})
                for test in tests.values():
                    effect = test.get("effect_size", {})
                    if effect.get("interpretation") == "large":
                        recommendations.append(f"Large effect detected in {metric_name} - prioritize implementation")
        
        return recommendations
    
    def _assess_research_potential(self, experiment: 'Experiment', analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential for research publication"""
        score = 0.0
        factors = []
        
        # Novelty factor
        if experiment.config.experiment_type in [ExperimentType.TECHNIQUE_COMPARISON, ExperimentType.ARCHITECTURE_EVALUATION]:
            score += 0.3
            factors.append("Novel technique/architecture comparison")
        
        # Statistical rigor
        metric_analyses = analysis.get("metric_analyses", {})
        significant_results = 0
        large_effects = 0
        
        for metric_analysis in metric_analyses.values():
            tests = metric_analysis.get("statistical_tests", {})
            for test in tests.values():
                if test.get("significant", False):
                    significant_results += 1
                
                effect = test.get("effect_size", {})
                if effect.get("interpretation") == "large":
                    large_effects += 1
        
        if significant_results > 0:
            score += 0.25
            factors.append(f"{significant_results} significant results")
        
        if large_effects > 0:
            score += 0.25
            factors.append(f"{large_effects} large effect sizes")
        
        # Enterprise relevance
        if "enterprise" in experiment.config.description.lower():
            score += 0.2
            factors.append("Enterprise relevance")
        
        return {
            "publication_score": min(score, 1.0),
            "contributing_factors": factors,
            "recommendation": "Strong publication potential" if score > 0.7 else "Additional evidence needed"
        }
    
    def _extract_research_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract research insights from analysis"""
        insights = []
        
        research_potential = analysis.get("research_potential", {})
        if research_potential.get("publication_score", 0) > 0.6:
            insight = {
                "type": "research_finding",
                "experiment_id": analysis["experiment_id"],
                "insight": "Significant experimental results with publication potential",
                "evidence": research_potential.get("contributing_factors", []),
                "timestamp": datetime.now().isoformat()
            }
            insights.append(insight)
        
        return insights
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment status and interim results"""
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}
        
        experiment = self.experiments[experiment_id]
        results = self.results_store.get(experiment_id, [])
        
        # Basic statistics
        total_results = len(results)
        metrics_summary = {}
        
        for metric in experiment.metrics:
            metric_results = [r for r in results if r.metric_name == metric.metric_name]
            if metric_results:
                values = [r.value for r in metric_results]
                metrics_summary[metric.metric_name] = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "std": np.std(values)
                }
        
        # Interim analysis if enough data
        interim_analysis = {}
        if total_results >= 50:
            interim_analysis = self.statistical_analyzer.analyze_experiment(
                experiment_id, results, experiment.variants, experiment.metrics
            )
        
        return {
            "experiment_id": experiment_id,
            "status": experiment.status.value,
            "start_time": experiment.start_time.isoformat() if experiment.start_time else None,
            "duration_minutes": experiment.get_duration_minutes(),
            "total_results": total_results,
            "metrics_summary": metrics_summary,
            "interim_analysis": interim_analysis
        }
    
    def get_research_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive research dashboard"""
        return {
            "experiment_metrics": self.experiment_metrics,
            "active_experiments": len(self.running_experiments),
            "total_experiments": len(self.experiments),
            "research_insights": len(self.research_insights),
            "publication_queue": len(self.publication_queue),
            "recent_insights": self.research_insights[-5:] if self.research_insights else [],
            "experiment_types": self._get_experiment_type_distribution()
        }
    
    def _get_experiment_type_distribution(self) -> Dict[str, int]:
        """Get distribution of experiment types"""
        distribution = {}
        for experiment in self.experiments.values():
            exp_type = experiment.config.experiment_type.value
            distribution[exp_type] = distribution.get(exp_type, 0) + 1
        return distribution

class VisualizationEngine:
    """Generate visualizations for experiment results"""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        
    def create_experiment_dashboard(self, experiment_id: str, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Create comprehensive experiment dashboard"""
        visualizations = {}
        
        # Results distribution plot
        visualizations["results_distribution"] = self._create_results_distribution_plot(analysis)
        
        # Statistical significance plot
        visualizations["significance_plot"] = self._create_significance_plot(analysis)
        
        # Effect size visualization
        visualizations["effect_sizes"] = self._create_effect_size_plot(analysis)
        
        return visualizations
    
    def _create_results_distribution_plot(self, analysis: Dict[str, Any]) -> str:
        """Create results distribution visualization"""
        # This would create actual matplotlib plots
        # For now, return placeholder
        return "results_distribution_plot.png"
    
    def _create_significance_plot(self, analysis: Dict[str, Any]) -> str:
        """Create statistical significance visualization"""
        return "significance_plot.png"
    
    def _create_effect_size_plot(self, analysis: Dict[str, Any]) -> str:
        """Create effect size visualization"""
        return "effect_size_plot.png"

class Experiment:
    """Individual experiment instance"""
    
    def __init__(self, 
                 config: ExperimentConfiguration,
                 variants: List[ExperimentVariant],
                 metrics: List[ExperimentMetric],
                 runner: ExperimentRunner):
        self.config = config
        self.variants = variants
        self.metrics = metrics
        self.runner = runner
        
        self.status = ExperimentStatus.DRAFT
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.stop_reason: Optional[str] = None
        self.final_analysis: Optional[Dict[str, Any]] = None
    
    def validate(self) -> bool:
        """Validate experiment configuration"""
        # Check traffic allocation
        total_allocation = sum(v.traffic_allocation for v in self.variants)
        if abs(total_allocation - 1.0) > 0.01:
            logger.error(f"Traffic allocation sums to {total_allocation}, not 1.0")
            return False
        
        # Check for control variant
        control_variants = [v for v in self.variants if v.is_control]
        if len(control_variants) != 1:
            logger.error(f"Expected 1 control variant, found {len(control_variants)}")
            return False
        
        # Check primary metrics
        primary_metrics = [m for m in self.metrics if m.metric_type == "primary"]
        if not primary_metrics:
            logger.error("No primary metrics defined")
            return False
        
        return True
    
    def start(self) -> None:
        """Start the experiment"""
        self.status = ExperimentStatus.RUNNING
        self.start_time = datetime.now()
        logger.info(f"Experiment {self.config.experiment_id} started")
    
    def stop(self, reason: str) -> None:
        """Stop the experiment"""
        self.status = ExperimentStatus.COMPLETED
        self.end_time = datetime.now()
        self.stop_reason = reason
        logger.info(f"Experiment {self.config.experiment_id} stopped: {reason}")
    
    def should_stop(self) -> bool:
        """Check if experiment should stop based on duration"""
        if self.config.duration_hours:
            if self.get_duration_minutes() >= self.config.duration_hours * 60:
                return True
        return False
    
    def get_duration_minutes(self) -> float:
        """Get experiment duration in minutes"""
        if not self.start_time:
            return 0.0
        
        end_time = self.end_time or datetime.now()
        duration = end_time - self.start_time
        return duration.total_seconds() / 60