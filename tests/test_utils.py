"""
Unit tests for utility functions.
"""

import pytest
from app.utils import FileProcessor, ChunkingHelper, DiffGenerator, extract_json_from_response

class TestFileProcessor:
    """Test FileProcessor class."""
    
    def test_detect_language(self):
        """Test language detection from file extensions."""
        processor = FileProcessor()
        
        assert processor.detect_language("test.py") == "python"
        assert processor.detect_language("script.js") == "javascript"
        assert processor.detect_language("component.jsx") == "javascript"
        assert processor.detect_language("types.ts") == "typescript"
        assert processor.detect_language("unknown.txt") == "python"  # default
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        processor = FileProcessor()
        
        content = "Hello world this is a test"
        tokens = processor.estimate_tokens(content)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_is_large_file(self):
        """Test large file detection."""
        processor = FileProcessor()
        
        small_content = "print('hello')"
        large_content = "print('hello')\n" * 1000
        
        assert not processor.is_large_file(small_content)
        assert processor.is_large_file(large_content)

class TestChunkingHelper:
    """Test ChunkingHelper class."""
    
    def test_chunk_python_functions(self):
        """Test Python function chunking."""
        helper = ChunkingHelper()
        
        content = """
def function1():
    return "hello"

def function2():
    return "world"
"""
        
        chunks = helper.chunk_by_functions(content, "python")
        assert len(chunks) >= 2
        assert all("function" in chunk["type"] for chunk in chunks)
    
    def test_chunk_js_functions(self):
        """Test JavaScript function chunking."""
        helper = ChunkingHelper()
        
        content = """
function test1() {
    return "hello";
}

const test2 = () => {
    return "world";
};
"""
        
        chunks = helper.chunk_by_functions(content, "javascript")
        assert len(chunks) >= 2

class TestDiffGenerator:
    """Test DiffGenerator class."""
    
    def test_generate_unified_diff(self):
        """Test unified diff generation."""
        generator = DiffGenerator()
        
        original = "line1\nline2\nline3"
        modified = "line1\nmodified line2\nline3"
        
        diff = generator.generate_unified_diff(original, modified, "test.py")
        assert "--- a/test.py" in diff
        assert "+++ b/test.py" in diff
        assert "line2" in diff

class TestJsonExtraction:
    """Test JSON extraction from responses."""
    
    def test_extract_pure_json(self):
        """Test extraction of pure JSON."""
        json_str = '{"key": "value", "number": 42}'
        result = extract_json_from_response(json_str)
        assert result == {"key": "value", "number": 42}
    
    def test_extract_json_from_text(self):
        """Test extraction of JSON from mixed text."""
        response = "Here's the result: {\"status\": \"success\", \"data\": [1, 2, 3]}"
        result = extract_json_from_response(response)
        assert result == {"status": "success", "data": [1, 2, 3]}
    
    def test_extract_json_none(self):
        """Test extraction when no JSON is found."""
        response = "This is just plain text with no JSON"
        result = extract_json_from_response(response)
        assert result is None
