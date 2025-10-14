"""
Unit tests for static analysis functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.static_analysis import StaticAnalyzer

class TestStaticAnalyzer:
    """Test StaticAnalyzer class."""
    
    def test_init(self):
        """Test analyzer initialization."""
        analyzer = StaticAnalyzer()
        assert isinstance(analyzer.tools_available, dict)
        assert 'flake8' in analyzer.tools_available
        assert 'radon' in analyzer.tools_available
        assert 'eslint' in analyzer.tools_available
    
    def test_analyze_python(self):
        """Test Python file analysis."""
        analyzer = StaticAnalyzer()
        
        content = """
def test_function():
    print("hello")
    return 42
"""
        
        result = analyzer.analyze(content, "test.py", "python")
        
        assert result['filename'] == "test.py"
        assert result['language'] == "python"
        assert 'tools_used' in result
        assert 'issues' in result
        assert 'metrics' in result
    
    def test_analyze_javascript(self):
        """Test JavaScript file analysis."""
        analyzer = StaticAnalyzer()
        
        content = """
function testFunction() {
    console.log("hello");
    return 42;
}
"""
        
        result = analyzer.analyze(content, "test.js", "javascript", enable_js_linting=False)
        
        assert result['filename'] == "test.js"
        assert result['language'] == "javascript"
        assert 'tools_used' in result
        assert 'issues' in result
    
    def test_basic_js_analysis(self):
        """Test basic JavaScript analysis without external tools."""
        analyzer = StaticAnalyzer()
        
        content = """
console.log("test");
var x = 1;
if (x == 1) {
    console.log("equal");
}
"""
        
        issues = analyzer._basic_js_analysis(content, "test.js")
        
        # Should find console.log and var usage
        assert len(issues) >= 2
        assert any(issue['rule'] == 'no-console' for issue in issues)
        assert any(issue['rule'] == 'prefer-let-const' for issue in issues)
    
    def test_get_flake8_severity(self):
        """Test flake8 error code to severity mapping."""
        analyzer = StaticAnalyzer()
        
        assert analyzer._get_flake8_severity("E101") == "error"
        assert analyzer._get_flake8_severity("W101") == "warning"
        assert analyzer._get_flake8_severity("F101") == "error"
        assert analyzer._get_flake8_severity("C101") == "info"
    
    @patch('subprocess.run')
    def test_run_flake8_success(self, mock_run):
        """Test successful flake8 execution."""
        analyzer = StaticAnalyzer()
        analyzer.tools_available['flake8'] = True
        
        # Mock successful flake8 output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test.py:1:1: E101 indentation contains mixed spaces and tabs"
        
        result = analyzer._run_flake8("def test():\n    pass", "test.py")
        
        assert len(result['issues']) == 1
        assert result['issues'][0]['tool'] == 'flake8'
        assert result['issues'][0]['code'] == 'E101'
    
    @patch('subprocess.run')
    def test_run_radon_success(self, mock_run):
        """Test successful radon execution."""
        analyzer = StaticAnalyzer()
        analyzer.tools_available['radon'] = True
        
        # Mock successful radon output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '[{"complexity": 1, "methods": []}]'
        
        result = analyzer._run_radon("def test():\n    pass", "test.py")
        
        assert 'metrics' in result
        assert 'cyclomatic_complexity' in result['metrics']
    
    def test_get_tools_status(self):
        """Test getting tools availability status."""
        analyzer = StaticAnalyzer()
        status = analyzer.get_tools_status()
        
        assert isinstance(status, dict)
        assert 'flake8' in status
        assert 'radon' in status
        assert 'eslint' in status
        assert 'node' in status
