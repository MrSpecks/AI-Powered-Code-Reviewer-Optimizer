"""
Utility functions for file processing, chunking, diff generation, and caching.
"""

import hashlib
import difflib
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
import json

class FileProcessor:
    """Handles file processing and language detection."""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript'
    }
    
    def detect_language(self, filename: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(filename).suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(ext, 'python')
    
    def estimate_tokens(self, content: str) -> int:
        """Rough token estimation for content."""
        # Simple estimation: ~1.3 tokens per word
        words = len(content.split())
        return int(words * 1.3)
    
    def is_large_file(self, content: str, threshold: int = 4000) -> bool:
        """Check if file is too large for single analysis."""
        return self.estimate_tokens(content) > threshold

class ChunkingHelper:
    """Handles file chunking for large files."""
    
    def chunk_by_functions(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Split file into function-level chunks."""
        chunks = []
        lines = content.split('\n')
        
        if language == 'python':
            chunks = self._chunk_python_functions(content, lines)
        elif language in ['javascript', 'typescript']:
            chunks = self._chunk_js_functions(content, lines)
        else:
            # Fallback: split by lines
            chunks = self._chunk_by_lines(content, lines)
        
        return chunks
    
    def _chunk_python_functions(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Chunk Python code by functions and classes."""
        chunks = []
        current_chunk = []
        in_function = False
        function_start = 0
        indent_level = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect function or class definition
            if (stripped.startswith('def ') or stripped.startswith('class ') or 
                stripped.startswith('async def ')):
                
                # Save previous chunk if exists
                if current_chunk and in_function:
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append({
                        'start_line': function_start + 1,
                        'end_line': i,
                        'content': chunk_content,
                        'type': 'function'
                    })
                
                # Start new chunk
                current_chunk = [line]
                function_start = i
                in_function = True
                indent_level = len(line) - len(line.lstrip())
            
            elif in_function:
                # Check if we're still in the function
                if stripped and not line.startswith(' ' * (indent_level + 1)) and not line.startswith('\t'):
                    # End of function
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append({
                        'start_line': function_start + 1,
                        'end_line': i,
                        'content': chunk_content,
                        'type': 'function'
                    })
                    current_chunk = []
                    in_function = False
                else:
                    current_chunk.append(line)
            else:
                # Top-level code
                if not current_chunk:
                    current_chunk = []
                current_chunk.append(line)
        
        # Handle last chunk
        if current_chunk and in_function:
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                'start_line': function_start + 1,
                'end_line': len(lines),
                'content': chunk_content,
                'type': 'function'
            })
        
        return chunks
    
    def _chunk_js_functions(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Chunk JavaScript/TypeScript code by functions."""
        chunks = []
        current_chunk = []
        in_function = False
        function_start = 0
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect function definition
            if re.match(r'^\s*(function|const\s+\w+\s*=\s*\(|async\s+function|export\s+function)', stripped):
                # Save previous chunk if exists
                if current_chunk and in_function:
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append({
                        'start_line': function_start + 1,
                        'end_line': i,
                        'content': chunk_content,
                        'type': 'function'
                    })
                
                # Start new chunk
                current_chunk = [line]
                function_start = i
                in_function = True
                brace_count = 0
            
            elif in_function:
                # Count braces to detect function end
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and stripped and not stripped.startswith('//'):
                    # End of function
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append({
                        'start_line': function_start + 1,
                        'end_line': i,
                        'content': chunk_content,
                        'type': 'function'
                    })
                    current_chunk = []
                    in_function = False
                else:
                    current_chunk.append(line)
            else:
                # Top-level code
                if not current_chunk:
                    current_chunk = []
                current_chunk.append(line)
        
        # Handle last chunk
        if current_chunk and in_function:
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                'start_line': function_start + 1,
                'end_line': len(lines),
                'content': chunk_content,
                'type': 'function'
            })
        
        return chunks
    
    def _chunk_by_lines(self, content: str, lines: List[str], chunk_size: int = 50) -> List[Dict[str, Any]]:
        """Fallback: chunk by line count."""
        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunks.append({
                'start_line': i + 1,
                'end_line': min(i + chunk_size, len(lines)),
                'content': '\n'.join(chunk_lines),
                'type': 'lines'
            })
        return chunks

class DiffGenerator:
    """Generates unified diffs and applies patches."""
    
    def generate_unified_diff(self, original: str, modified: str, filename: str) -> str:
        """Generate unified diff between original and modified content."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f'a/{filename}',
            tofile=f'b/{filename}',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def apply_patch(self, content: str, patch: str) -> str:
        """Apply a unified diff patch to content."""
        # This is a simplified implementation
        # In production, you'd want to use a proper patch library
        lines = content.splitlines(keepends=True)
        
        # Parse patch and apply changes
        # This is a basic implementation - for production use a proper patch library
        return content  # Placeholder

class CacheManager:
    """Handles caching of analysis results."""
    
    def __init__(self, cache_dir: str = "./artifacts"):
        """Initialize cache manager."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, content: str, analysis_type: str) -> str:
        """Generate cache key for content and analysis type."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{analysis_type}_{content_hash}"
    
    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        cache_file = self.cache_dir / f"{cache_file}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache analysis result."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
        except IOError:
            pass  # Fail silently for cache errors

class TempFileManager:
    """Manages temporary files for analysis."""
    
    def __init__(self, temp_dir: str = "./artifacts/temp"):
        """Initialize temp file manager."""
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.temp_files = []
    
    def create_temp_file(self, content: str, suffix: str = ".py") -> str:
        """Create temporary file with content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            dir=self.temp_dir,
            delete=False
        )
        temp_file.write(content)
        temp_file.close()
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        self.temp_files.clear()
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup()

def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response, handling cases where it's not pure JSON."""
    # Try to parse as pure JSON first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON block using regex
    json_pattern = r'\{.*\}'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return None

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against JSON schema."""
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return True
    except (jsonschema.ValidationError, ImportError):
        return False
