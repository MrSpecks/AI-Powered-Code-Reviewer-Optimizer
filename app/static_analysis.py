"""
Static analysis runner for Python and JavaScript files.
Supports flake8, radon for Python and eslint for JavaScript.
"""

import subprocess
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

class StaticAnalyzer:
    """Runs static analysis tools and parses their output."""
    
    def __init__(self):
        """Initialize static analyzer."""
        self.tools_available = self._check_tools_availability()
    
    def _check_tools_availability(self) -> Dict[str, bool]:
        """Check which static analysis tools are available."""
        tools = {
            'flake8': False,
            'radon': False,
            'eslint': False,
            'node': False
        }
        
        # Check Python tools
        try:
            subprocess.run(['flake8', '--version'], capture_output=True, check=True)
            tools['flake8'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            subprocess.run(['radon', '--version'], capture_output=True, check=True)
            tools['radon'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check Node.js tools
        try:
            subprocess.run(['node', '--version'], capture_output=True, check=True)
            tools['node'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        if tools['node']:
            try:
                subprocess.run(['eslint', '--version'], capture_output=True, check=True)
                tools['eslint'] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return tools
    
    def analyze(self, content: str, filename: str, language: str, 
                enable_js_linting: bool = False) -> Dict[str, Any]:
        """Run static analysis on the provided content."""
        results = {
            'filename': filename,
            'language': language,
            'tools_used': [],
            'issues': [],
            'metrics': {},
            'warnings': []
        }
        
        if language == 'python':
            results.update(self._analyze_python(content, filename))
        elif language in ['javascript', 'typescript']:
            results.update(self._analyze_javascript(content, filename, enable_js_linting))
        else:
            results['warnings'].append(f"Static analysis not supported for language: {language}")
        
        return results
    
    def _analyze_python(self, content: str, filename: str) -> Dict[str, Any]:
        """Run Python static analysis."""
        results = {
            'tools_used': [],
            'issues': [],
            'metrics': {}
        }
        
        # Run flake8
        if self.tools_available['flake8']:
            flake8_results = self._run_flake8(content, filename)
            results['issues'].extend(flake8_results['issues'])
            results['tools_used'].append('flake8')
        else:
            results['warnings'].append("flake8 not available - install with: pip install flake8")
        
        # Run radon
        if self.tools_available['radon']:
            radon_results = self._run_radon(content, filename)
            results['metrics'].update(radon_results['metrics'])
            results['tools_used'].append('radon')
        else:
            results['warnings'].append("radon not available - install with: pip install radon")
        
        return results
    
    def _analyze_javascript(self, content: str, filename: str, enable_linting: bool) -> Dict[str, Any]:
        """Run JavaScript static analysis."""
        results = {
            'tools_used': [],
            'issues': [],
            'metrics': {}
        }
        
        if enable_linting and self.tools_available['eslint']:
            eslint_results = self._run_eslint(content, filename)
            results['issues'].extend(eslint_results['issues'])
            results['tools_used'].append('eslint')
        elif enable_linting:
            results['warnings'].append("eslint not available - install with: npm install -g eslint")
        else:
            results['warnings'].append("JavaScript linting disabled")
        
        # Basic JavaScript analysis
        js_issues = self._basic_js_analysis(content, filename)
        results['issues'].extend(js_issues)
        results['tools_used'].append('basic_js_analysis')
        
        return results
    
    def _run_flake8(self, content: str, filename: str) -> Dict[str, List[Dict[str, Any]]]:
        """Run flake8 on Python content."""
        issues = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run flake8
            result = subprocess.run(
                ['flake8', '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s', temp_file],
                capture_output=True,
                text=True
            )
            
            # Parse output
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        issues.append({
                            'tool': 'flake8',
                            'line': int(parts[1]),
                            'column': int(parts[2]),
                            'code': parts[3].split()[0],
                            'message': ' '.join(parts[3].split()[1:]),
                            'severity': self._get_flake8_severity(parts[3].split()[0])
                        })
            
            # Cleanup
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"Error running flake8: {e}")
        
        return {'issues': issues}
    
    def _run_radon(self, content: str, filename: str) -> Dict[str, Any]:
        """Run radon on Python content."""
        metrics = {}
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run radon cc (cyclomatic complexity)
            result = subprocess.run(
                ['radon', 'cc', '--json', temp_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                try:
                    radon_data = json.loads(result.stdout)
                    if radon_data:
                        file_data = radon_data[0]
                        metrics['cyclomatic_complexity'] = file_data.get('complexity', 0)
                        metrics['functions'] = []
                        
                        for func in file_data.get('methods', []):
                            metrics['functions'].append({
                                'name': func.get('name', 'unknown'),
                                'complexity': func.get('complexity', 0),
                                'line': func.get('lineno', 0)
                            })
                except json.JSONDecodeError:
                    pass
            
            # Run radon mi (maintainability index)
            result = subprocess.run(
                ['radon', 'mi', '--json', temp_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                try:
                    radon_data = json.loads(result.stdout)
                    if radon_data:
                        file_data = radon_data[0]
                        metrics['maintainability_index'] = file_data.get('mi', 0)
                except json.JSONDecodeError:
                    pass
            
            # Cleanup
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"Error running radon: {e}")
        
        return {'metrics': metrics}
    
    def _run_eslint(self, content: str, filename: str) -> Dict[str, List[Dict[str, Any]]]:
        """Run eslint on JavaScript content."""
        issues = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run eslint
            result = subprocess.run(
                ['eslint', '--format=json', temp_file],
                capture_output=True,
                text=True
            )
            
            # Parse JSON output
            if result.stdout.strip():
                try:
                    eslint_data = json.loads(result.stdout)
                    for file_data in eslint_data:
                        for message in file_data.get('messages', []):
                            issues.append({
                                'tool': 'eslint',
                                'line': message.get('line', 0),
                                'column': message.get('column', 0),
                                'rule': message.get('ruleId', 'unknown'),
                                'message': message.get('message', ''),
                                'severity': 'error' if message.get('severity') == 2 else 'warning'
                            })
                except json.JSONDecodeError:
                    pass
            
            # Cleanup
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"Error running eslint: {e}")
        
        return {'issues': issues}
    
    def _basic_js_analysis(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Basic JavaScript analysis without external tools."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for common issues
            if 'console.log' in stripped:
                issues.append({
                    'tool': 'basic_js_analysis',
                    'line': i,
                    'column': 0,
                    'rule': 'no-console',
                    'message': 'console.log should be removed in production',
                    'severity': 'warning'
                })
            
            if 'var ' in stripped and 'let ' not in stripped and 'const ' not in stripped:
                issues.append({
                    'tool': 'basic_js_analysis',
                    'line': i,
                    'column': 0,
                    'rule': 'prefer-let-const',
                    'message': 'Consider using let or const instead of var',
                    'severity': 'warning'
                })
            
            if '==' in stripped and '===' not in stripped:
                issues.append({
                    'tool': 'basic_js_analysis',
                    'line': i,
                    'column': 0,
                    'rule': 'prefer-strict-equals',
                    'message': 'Consider using === instead of ==',
                    'severity': 'warning'
                })
        
        return issues
    
    def _get_flake8_severity(self, code: str) -> str:
        """Map flake8 error codes to severity levels."""
        if code.startswith('E'):
            return 'error'
        elif code.startswith('W'):
            return 'warning'
        elif code.startswith('F'):
            return 'error'
        else:
            return 'info'
    
    def get_tools_status(self) -> Dict[str, bool]:
        """Get status of available tools."""
        return self.tools_available.copy()
