"""
OpenDistillery Testing Framework
Test suite for the OpenDistillery compound AI system.
"""

__version__ = "1.0.0"
__all__ = [
    "run_all_tests",
    "generate_test_report"
]

def run_all_tests():
    """Run comprehensive test suite"""
    import pytest
    return pytest.main(["-v", "tests/"])

def generate_test_report():
    """Generate comprehensive test coverage and quality report"""
    import pytest
    return pytest.main(["-v", "--cov=src", "--cov-report=html", "tests/"])

# Empty file to make tests a proper package 