"""
OpenContext Benchmarking Framework
Comprehensive performance and capability benchmarks for compound AI systems.
"""

from .compound_ai_benchmarks import CompoundAIBenchmarkSuite
from .enterprise_performance import EnterprisePerformanceBenchmarks
from .research_validation import ResearchValidationBenchmarks
from .reasoning_benchmarks import ReasoningTechniqueBenchmarks

__version__ = "1.0.0"
__all__ = [
    "CompoundAIBenchmarkSuite",
    "EnterprisePerformanceBenchmarks", 
    "ResearchValidationBenchmarks",
    "ReasoningTechniqueBenchmarks",
    "run_all_benchmarks",
    "generate_benchmark_report"
]

def run_all_benchmarks():
    """Run comprehensive benchmark suite"""
    pass

def generate_benchmark_report():
    """Generate comprehensive benchmark performance report"""
    pass 