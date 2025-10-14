"""
Unit tests for LLM client functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.llm_client import LLMClient

class TestLLMClient:
    """Test LLMClient class."""
    
    def test_init(self):
        """Test client initialization."""
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        assert client.api_key == "test-key"
        assert client.provider == "OpenAI"
        assert client.model == "gpt-4o-mini"
        assert client.templates is not None
    
    def test_is_configured(self):
        """Test configuration check."""
        # Configured client
        client1 = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        assert client1.is_configured()
        
        # Unconfigured client
        client2 = LLMClient("", "OpenAI", "gpt-4o-mini")
        assert not client2.is_configured()
    
    @patch('app.llm_client.openai.OpenAI')
    def test_call_review_success(self, mock_openai):
        """Test successful review call."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"filename": "test.py", "language": "python", "summary": {"complexityScore": 50, "maintainability": "medium", "quick_actions": []}, "findings": [], "meta": {}}'
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        result = client.call_review("def test(): pass", "test.py", "python", {})
        
        assert result['filename'] == "test.py"
        assert result['language'] == "python"
        assert 'summary' in result
        assert 'findings' in result
    
    def test_call_review_not_configured(self):
        """Test review call when not configured."""
        client = LLMClient("", "OpenAI", "gpt-4o-mini")
        
        with pytest.raises(ValueError, match="LLM client not configured"):
            client.call_review("def test(): pass", "test.py", "python", {})
    
    @patch('app.llm_client.openai.OpenAI')
    def test_call_refactor_success(self, mock_openai):
        """Test successful refactor call."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"filename": "test.py", "language": "python", "alternatives": [], "meta": {}}'
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        result = client.call_refactor("def test(): pass", "test.py", "python", "1-1", "readability")
        
        assert result['filename'] == "test.py"
        assert result['language'] == "python"
        assert 'alternatives' in result
    
    @patch('app.llm_client.openai.OpenAI')
    def test_call_tests_success(self, mock_openai):
        """Test successful test generation call."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"filename": "test.py", "test_filename": "test_test.py", "test_content": "def test_function(): pass", "required_mocks": [], "meta": {}}'
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        result = client.call_tests("def test(): pass", "test.py", "python", "1-1")
        
        assert result['filename'] == "test.py"
        assert result['test_filename'] == "test_test.py"
        assert 'test_content' in result
    
    def test_get_model_info(self):
        """Test getting model information."""
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        info = client.get_model_info()
        
        assert info['provider'] == "OpenAI"
        assert info['model'] == "gpt-4o-mini"
        assert info['configured'] is True
    
    def test_parse_response_pure_json(self):
        """Test parsing pure JSON response."""
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        response = '{"key": "value", "number": 42}'
        result = client._parse_response(response)
        
        assert result == {"key": "value", "number": 42}
    
    def test_parse_response_with_text(self):
        """Test parsing JSON response with surrounding text."""
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        response = 'Here is the result: {"status": "success", "data": [1, 2, 3]}'
        result = client._parse_response(response)
        
        assert result == {"status": "success", "data": [1, 2, 3]}
    
    def test_parse_response_invalid(self):
        """Test parsing invalid JSON response."""
        client = LLMClient("test-key", "OpenAI", "gpt-4o-mini")
        
        response = "This is not JSON at all"
        result = client._parse_response(response)
        
        assert result is None
