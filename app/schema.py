"""
JSON Schema definitions for LLM responses.
Based on the canonical schema from the repository.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Category(str, Enum):
    READABILITY = "readability"
    EFFICIENCY = "efficiency"
    SECURITY = "security"
    STYLE = "style"
    CORRECTNESS = "correctness"

class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Maintainability(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Location:
    start_line: int
    end_line: int

@dataclass
class Finding:
    id: str
    category: Category
    severity: Severity
    location: Location
    description: str
    evidence: str
    suggested_fix_summary: str
    confidence: Confidence

@dataclass
class Summary:
    complexityScore: int  # 0-100
    maintainability: Maintainability
    quick_actions: List[str]

@dataclass
class ReviewResponse:
    filename: str
    language: str
    summary: Summary
    findings: List[Finding]
    meta: Dict[str, Any]

@dataclass
class Alternative:
    mode: str
    rationale: str
    unified_diff: str
    risk: Risk
    tests_needed: List[str]

@dataclass
class RefactorResponse:
    filename: str
    language: str
    alternatives: List[Alternative]
    meta: Dict[str, Any]

@dataclass
class TestResponse:
    filename: str
    test_filename: str
    test_content: str
    required_mocks: List[str]
    meta: Dict[str, Any]

@dataclass
class SecurityFinding:
    id: str
    severity: Severity
    cwe: Optional[str]
    location: Location
    exploitability: str
    suggested_mitigation: str
    requires_run: bool = False

@dataclass
class SecurityResponse:
    filename: str
    security_findings: List[SecurityFinding]
    recommendations: List[str]
    meta: Dict[str, Any]

@dataclass
class DiffResponse:
    filename: str
    unified_diff: str

# JSON Schema for validation
REVIEW_SCHEMA = {
    "type": "object",
    "required": ["filename", "language", "summary", "findings", "meta"],
    "properties": {
        "filename": {"type": "string"},
        "language": {"type": "string"},
        "summary": {
            "type": "object",
            "required": ["complexityScore", "maintainability", "quick_actions"],
            "properties": {
                "complexityScore": {"type": "number", "minimum": 0, "maximum": 100},
                "maintainability": {"type": "string", "enum": ["low", "medium", "high"]},
                "quick_actions": {"type": "array", "items": {"type": "string"}}
            }
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "category", "severity", "location", "description", "evidence", "suggested_fix_summary", "confidence"],
                "properties": {
                    "id": {"type": "string"},
                    "category": {"type": "string", "enum": ["readability", "efficiency", "security", "style", "correctness"]},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "location": {
                        "type": "object",
                        "required": ["start_line", "end_line"],
                        "properties": {
                            "start_line": {"type": "integer"},
                            "end_line": {"type": "integer"}
                        }
                    },
                    "description": {"type": "string"},
                    "evidence": {"type": "string"},
                    "suggested_fix_summary": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]}
                }
            }
        },
        "meta": {"type": "object"}
    }
}

REFACTOR_SCHEMA = {
    "type": "object",
    "required": ["filename", "language", "alternatives", "meta"],
    "properties": {
        "filename": {"type": "string"},
        "language": {"type": "string"},
        "alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["mode", "rationale", "unified_diff", "risk", "tests_needed"],
                "properties": {
                    "mode": {"type": "string"},
                    "rationale": {"type": "string"},
                    "unified_diff": {"type": "string"},
                    "risk": {"type": "string", "enum": ["low", "medium", "high"]},
                    "tests_needed": {"type": "array", "items": {"type": "string"}}
            }
        },
        "meta": {"type": "object"}
    }
}

TEST_SCHEMA = {
    "type": "object",
    "required": ["filename", "test_filename", "test_content", "required_mocks", "meta"],
    "properties": {
        "filename": {"type": "string"},
        "test_filename": {"type": "string"},
        "test_content": {"type": "string"},
        "required_mocks": {"type": "array", "items": {"type": "string"}},
        "meta": {"type": "object"}
    }
}
