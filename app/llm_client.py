"""
LLM client for OpenAI and custom providers.
Handles API calls, JSON parsing, and response validation.
"""

import json
import time
from typing import Dict, Any, Optional, List
import openai
from app.prompt_templates import PromptTemplates
from app.schema import REVIEW_SCHEMA, REFACTOR_SCHEMA, TEST_SCHEMA
from app.utils import extract_json_from_response, validate_json_schema

class LLMClient:
    """Client for LLM API calls with JSON response validation."""
    
    def __init__(self, api_key: str, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        """Initialize LLM client."""
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.templates = PromptTemplates()
        
        # Initialize OpenAI client
        if provider == "OpenAI" and api_key:
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return self.client is not None and bool(self.api_key)
    
    def call_review(self, file_content: str, filename: str, language: str,
                   static_output: Dict[str, Any], max_findings: int = 6) -> Dict[str, Any]:
        """Call LLM for code review."""
        if not self.is_configured():
            raise ValueError("LLM client not configured")
        
        # Get prompt
        prompt = self.templates.get_review_prompt(
            language, filename, file_content, static_output, max_findings
        )
        
        # Get system message
        system_message = self.templates.get_system_message()
        
        # Get temperature and max tokens
        temperature = self.templates.get_temperature_for_task('review')
        max_tokens = self.templates.get_max_tokens_for_task('review')
        
        # Make API call
        response = self._make_api_call(
            system_message, prompt, temperature, max_tokens
        )
        
        # Parse and validate response
        parsed_response = self._parse_and_validate_response(
            response, REVIEW_SCHEMA, 'review'
        )
        
        return parsed_response
    
    def call_refactor(self, file_content: str, filename: str, language: str,
                     target_lines: str, mode: str = "readability") -> Dict[str, Any]:
        """Call LLM for code refactoring."""
        if not self.is_configured():
            raise ValueError("LLM client not configured")
        
        # Get prompt
        prompt = self.templates.get_refactor_prompt(
            language, filename, file_content, target_lines, mode
        )
        
        # Get system message
        system_message = self.templates.get_system_message()
        
        # Get temperature and max tokens
        temperature = self.templates.get_temperature_for_task('refactor')
        max_tokens = self.templates.get_max_tokens_for_task('refactor')
        
        # Make API call
        response = self._make_api_call(
            system_message, prompt, temperature, max_tokens
        )
        
        # Parse and validate response
        parsed_response = self._parse_and_validate_response(
            response, REFACTOR_SCHEMA, 'refactor'
        )
        
        return parsed_response
    
    def call_tests(self, file_content: str, filename: str, language: str,
                  target_lines: str, testing_framework: str = "pytest") -> Dict[str, Any]:
        """Call LLM for test generation."""
        if not self.is_configured():
            raise ValueError("LLM client not configured")
        
        # Get prompt
        prompt = self.templates.get_test_generation_prompt(
            language, filename, file_content, target_lines, testing_framework
        )
        
        # Get system message
        system_message = self.templates.get_system_message()
        
        # Get temperature and max tokens
        temperature = self.templates.get_temperature_for_task('test_generation')
        max_tokens = self.templates.get_max_tokens_for_task('test_generation')
        
        # Make API call
        response = self._make_api_call(
            system_message, prompt, temperature, max_tokens
        )
        
        # Parse and validate response
        parsed_response = self._parse_and_validate_response(
            response, TEST_SCHEMA, 'test_generation'
        )
        
        return parsed_response
    
    def call_security_analysis(self, file_content: str, filename: str, language: str,
                              static_security_output: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM for security analysis."""
        if not self.is_configured():
            raise ValueError("LLM client not configured")
        
        # Get prompt
        prompt = self.templates.get_security_analysis_prompt(
            language, filename, file_content, static_security_output
        )
        
        # Get system message
        system_message = self.templates.get_system_message()
        
        # Get temperature and max tokens
        temperature = self.templates.get_temperature_for_task('security')
        max_tokens = self.templates.get_max_tokens_for_task('security')
        
        # Make API call
        response = self._make_api_call(
            system_message, prompt, temperature, max_tokens
        )
        
        # Parse response (no specific schema for security analysis)
        parsed_response = self._parse_response(response)
        
        return parsed_response
    
    def _make_api_call(self, system_message: str, prompt: str, 
                      temperature: float, max_tokens: int) -> str:
        """Make API call to LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
    
    def _parse_and_validate_response(self, response: str, schema: Dict[str, Any], 
                                   task: str) -> Dict[str, Any]:
        """Parse and validate LLM response against schema."""
        # Try to parse response
        parsed = self._parse_response(response)
        
        if parsed is None:
            # Try recovery
            parsed = self._recovery_parse(response, task)
        
        if parsed is None:
            raise ValueError("Failed to parse LLM response as JSON")
        
        # Validate against schema
        if not validate_json_schema(parsed, schema):
            print(f"Warning: Response does not match expected schema for {task}")
        
        return parsed
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response as JSON."""
        # Try direct JSON parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from response
        return extract_json_from_response(response)
    
    def _recovery_parse(self, response: str, task: str) -> Optional[Dict[str, Any]]:
        """Attempt recovery parsing with explicit JSON instruction."""
        try:
            # Create recovery prompt
            recovery_prompt = f"""
ERROR RECOVERY: Your previous response was not pure JSON. You MUST return valid JSON only.

Original task: {task}
Your response: {response}

Please return ONLY the JSON response, no additional text or explanation.
"""
            
            # Make recovery API call
            recovery_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a JSON formatter. Return only valid JSON."},
                    {"role": "user", "content": recovery_prompt}
                ],
                temperature=0.0,
                max_tokens=2000
            )
            
            recovery_text = recovery_response.choices[0].message.content
            
            # Try to parse recovery response
            return self._parse_response(recovery_text)
            
        except Exception as e:
            print(f"Recovery parsing failed: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration."""
        return {
            'provider': self.provider,
            'model': self.model,
            'configured': self.is_configured()
        }
