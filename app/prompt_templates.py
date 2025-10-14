"""
Prompt template loader and assembler.
Loads templates from repository .txt files and assembles prompts with placeholders.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

class PromptTemplates:
    """Loads and manages prompt templates from repository files."""
    
    def __init__(self, repo_root: Optional[str] = None):
        """Initialize with repository root path."""
        if repo_root is None:
            repo_root = Path(__file__).parent.parent
        self.repo_root = Path(repo_root)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates from repository files."""
        template_files = {
            'system_message': 'System Message.txt',
            'review': 'REVIEW prompt (summarize + findings + prioritized issues).txt',
            'refactor': 'REFACTOR prompt (3 modes minimal-change readability-first performance-first).txt',
            'test_generation': 'TEST GENERATION prompt (pytest for Python, jest for JS).txt',
            'security_analysis': 'SECURITY ANALYSIS prompt.txt',
            'unified_diff': 'UNIFIED DIFF GENERATION (explicit).txt',
            'few_shot_examples': 'Few-shot examples.txt'
        }
        
        for key, filename in template_files.items():
            file_path = self.repo_root / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.templates[key] = f.read()
            else:
                print(f"Warning: Template file not found: {file_path}")
                self.templates[key] = ""
    
    def get_system_message(self) -> str:
        """Get the system message for LLM."""
        return self.templates.get('system_message', '')
    
    def get_review_prompt(self, language: str, filename: str, file_content: str, 
                         static_output: Dict[str, Any], max_findings: int = 6) -> str:
        """Assemble review prompt with placeholders."""
        template = self.templates.get('review', '')
        
        # Format static output as JSON string
        static_output_str = json.dumps(static_output, indent=2) if static_output else "{}"
        
        # Replace placeholders
        prompt = template.format(
            language=language,
            filename=filename,
            file_content=file_content,
            static_output=static_output_str,
            N=max_findings
        )
        
        return prompt
    
    def get_refactor_prompt(self, language: str, filename: str, file_content: str,
                           target_lines: str, mode: str, max_alternatives: int = 2) -> str:
        """Assemble refactor prompt with placeholders."""
        template = self.templates.get('refactor', '')
        
        # Replace <MODE> placeholder
        template = template.replace('<MODE>', mode)
        
        prompt = template.format(
            language=language,
            filename=filename,
            file_content=file_content,
            start_line=target_lines.split('-')[0] if '-' in target_lines else '1',
            end_line=target_lines.split('-')[1] if '-' in target_lines else '100'
        )
        
        return prompt
    
    def get_test_generation_prompt(self, language: str, filename: str, file_content: str,
                                  target_lines: str, testing_framework: str = "pytest",
                                  examples: Optional[List[Dict[str, Any]]] = None) -> str:
        """Assemble test generation prompt with placeholders."""
        template = self.templates.get('test_generation', '')
        
        # Format examples
        examples_str = json.dumps(examples or [], indent=2)
        
        prompt = template.format(
            language=language,
            filename=filename,
            file_content=file_content,
            start_line=target_lines.split('-')[0] if '-' in target_lines else '1',
            end_line=target_lines.split('-')[1] if '-' in target_lines else '100',
            pytest=testing_framework,
            examples=examples_str
        )
        
        return prompt
    
    def get_security_analysis_prompt(self, language: str, filename: str, file_content: str,
                                    static_security_output: Dict[str, Any], 
                                    allowed_risk_level: str = "medium") -> str:
        """Assemble security analysis prompt with placeholders."""
        template = self.templates.get('security_analysis', '')
        
        # Format static security output
        static_security_str = json.dumps(static_security_output, indent=2) if static_security_output else "{}"
        
        prompt = template.format(
            language=language,
            filename=filename,
            file_content=file_content,
            static_security_output=static_security_str,
            allowed_risk_level=allowed_risk_level
        )
        
        return prompt
    
    def get_unified_diff_prompt(self, filename: str, original: str, modified: str) -> str:
        """Assemble unified diff generation prompt."""
        template = self.templates.get('unified_diff', '')
        
        prompt = template.format(
            filename=filename,
            file_content=original,
            modified_file_content=modified
        )
        
        return prompt
    
    def get_few_shot_examples(self) -> str:
        """Get few-shot examples for context."""
        return self.templates.get('few_shot_examples', '')
    
    def get_temperature_for_task(self, task: str) -> float:
        """Get recommended temperature for specific task."""
        # Based on prompt engineering tips
        temperature_map = {
            'review': 0.0,
            'security': 0.0,
            'unified_diff': 0.0,
            'refactor': 0.2,
            'test_generation': 0.0
        }
        return temperature_map.get(task, 0.1)
    
    def get_max_tokens_for_task(self, task: str) -> int:
        """Get recommended max tokens for specific task."""
        # Based on prompt engineering tips
        token_map = {
            'review': 2000,
            'refactor': 3000,
            'test_generation': 3000,
            'security': 2000,
            'unified_diff': 1500
        }
        return token_map.get(task, 2000)
