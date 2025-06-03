"""
Enterprise Input Validation and Security Scanning
Advanced input validation, sanitization, and security scanning
"""

import re
import html
import urllib.parse
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation security levels"""
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"

class ThreatType(Enum):
    """Security threat types"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    SCRIPT_INJECTION = "script_injection"
    LDAP_INJECTION = "ldap_injection"
    XXE = "xxe"

@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_value: str = ""
    threats_detected: List[ThreatType] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.threats_detected is None:
            self.threats_detected = []
        if self.warnings is None:
            self.warnings = []

class InputValidator:
    """Enterprise input validator"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.validation_level = validation_level
        self.threat_patterns = self._init_threat_patterns()
        self.allowed_patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "username": r'^[a-zA-Z0-9_]{3,32}$',
            "phone": r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$',
            "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            "alphanumeric": r'^[a-zA-Z0-9]+$',
            "url": r'^https?:\/\/[^\s/$.?#].[^\s]*$'
        }
    
    def _init_threat_patterns(self) -> Dict[ThreatType, List[str]]:
        """Initialize threat detection patterns"""
        return {
            ThreatType.SQL_INJECTION: [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(--|\#|\/\*|\*\/)",
                r"(\')(.*?)(\bOR\b|\bAND\b)(.*?)(\').*?(\=)",
            ],
            ThreatType.XSS: [
                r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
                r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>",
                r"javascript\s*:",
                r"on\w+\s*=",
                r"<\s*(img|link|meta)[^>]*>",
            ],
            ThreatType.PATH_TRAVERSAL: [
                r"\.\.\/",
                r"\.\.\\\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c",
                r"\.\.%2f",
                r"\.\.%5c",
            ],
            ThreatType.COMMAND_INJECTION: [
                r"[\;\&\|\`\$\(\)]",
                r"\b(bash|sh|cmd|powershell|python|perl|ruby)\b",
                r"(\||&&|;|\$\(|\`)",
            ],
            ThreatType.SCRIPT_INJECTION: [
                r"<\s*script",
                r"<\s*object",
                r"<\s*embed",
                r"<\s*applet",
                r"eval\s*\(",
                r"setTimeout\s*\(",
                r"setInterval\s*\(",
            ],
            ThreatType.LDAP_INJECTION: [
                r"[\(\)\*\&\|\!]",
                r"\bou\s*=",
                r"\bcn\s*=",
                r"\bdc\s*=",
            ],
            ThreatType.XXE: [
                r"<!ENTITY",
                r"<!DOCTYPE",
                r"SYSTEM\s+[\"']",
                r"PUBLIC\s+[\"']",
            ],
        }
    
    def validate_input(self, value: str, input_type: str = "text", 
                      max_length: int = None, allow_empty: bool = True) -> ValidationResult:
        """Validate input against security threats"""
        if not isinstance(value, str):
            value = str(value)
        
        result = ValidationResult(is_valid=True, sanitized_value=value)
        
        # Check empty values
        if not value.strip():
            if not allow_empty:
                result.is_valid = False
                result.warnings.append("Empty value not allowed")
            return result
        
        # Check length
        if max_length and len(value) > max_length:
            result.is_valid = False
            result.warnings.append(f"Value exceeds maximum length of {max_length}")
            return result
        
        # Check against threat patterns
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    result.threats_detected.append(threat_type)
                    if self.validation_level != ValidationLevel.BASIC:
                        result.is_valid = False
                        result.warnings.append(f"Potential {threat_type.value} detected")
        
        # Validate specific input types
        if input_type in self.allowed_patterns:
            pattern = self.allowed_patterns[input_type]
            if not re.match(pattern, value, re.IGNORECASE):
                result.is_valid = False
                result.warnings.append(f"Invalid {input_type} format")
        
        # Sanitize if valid
        if result.is_valid or self.validation_level == ValidationLevel.BASIC:
            result.sanitized_value = self._sanitize_value(value, input_type)
        
        return result
    
    def _sanitize_value(self, value: str, input_type: str) -> str:
        """Sanitize input value"""
        sanitized = value
        
        # HTML escape
        sanitized = html.escape(sanitized, quote=True)
        
        # URL encode special characters if needed
        if input_type == "url":
            sanitized = urllib.parse.quote(sanitized, safe=':/?#[]@!$&\'()*+,;=')
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def validate_batch(self, inputs: Dict[str, Any], 
                      schema: Dict[str, Dict[str, Any]]) -> Dict[str, ValidationResult]:
        """Validate multiple inputs according to schema"""
        results = {}
        
        for field_name, field_value in inputs.items():
            if field_name in schema:
                field_schema = schema[field_name]
                result = self.validate_input(
                    str(field_value),
                    input_type=field_schema.get("type", "text"),
                    max_length=field_schema.get("max_length"),
                    allow_empty=field_schema.get("allow_empty", True)
                )
                results[field_name] = result
            else:
                # Unknown field
                results[field_name] = ValidationResult(
                    is_valid=False,
                    warnings=["Unknown field in schema"]
                )
        
        return results

class SanitizationEngine:
    """Advanced data sanitization engine"""
    
    def __init__(self):
        self.sanitizers = {
            "html": self._sanitize_html,
            "sql": self._sanitize_sql,
            "javascript": self._sanitize_javascript,
            "xml": self._sanitize_xml,
            "json": self._sanitize_json,
        }
    
    def sanitize(self, value: str, content_type: str = "html") -> str:
        """Sanitize content based on type"""
        if content_type in self.sanitizers:
            return self.sanitizers[content_type](value)
        return self._sanitize_generic(value)
    
    def _sanitize_html(self, value: str) -> str:
        """Sanitize HTML content"""
        # Remove dangerous tags
        dangerous_tags = r'<\s*(script|object|embed|applet|meta|link|style|iframe)[^>]*?>.*?<\s*/\s*\1\s*>'
        value = re.sub(dangerous_tags, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove dangerous attributes
        dangerous_attrs = r'\s*(on\w+|javascript:|data:|vbscript:)[^>]*'
        value = re.sub(dangerous_attrs, '', value, flags=re.IGNORECASE)
        
        return html.escape(value, quote=True)
    
    def _sanitize_sql(self, value: str) -> str:
        """Sanitize SQL input"""
        # Escape single quotes
        value = value.replace("'", "''")
        
        # Remove SQL keywords that shouldn't be in data
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC']
        for keyword in dangerous_keywords:
            value = re.sub(rf'\b{keyword}\b', '', value, flags=re.IGNORECASE)
        
        return value
    
    def _sanitize_javascript(self, value: str) -> str:
        """Sanitize JavaScript content"""
        # Remove dangerous functions
        dangerous_functions = r'\b(eval|setTimeout|setInterval|Function|alert|confirm|prompt)\s*\('
        value = re.sub(dangerous_functions, '', value, flags=re.IGNORECASE)
        
        # Escape special characters
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        value = value.replace("'", "\\'")
        
        return value
    
    def _sanitize_xml(self, value: str) -> str:
        """Sanitize XML content"""
        # Remove DTD and entity declarations
        value = re.sub(r'<!DOCTYPE[^>]*>', '', value, flags=re.IGNORECASE)
        value = re.sub(r'<!ENTITY[^>]*>', '', value, flags=re.IGNORECASE)
        
        # Escape XML special characters
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')
        
        return value
    
    def _sanitize_json(self, value: str) -> str:
        """Sanitize JSON content"""
        # Escape special JSON characters
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        value = value.replace('\t', '\\t')
        
        return value
    
    def _sanitize_generic(self, value: str) -> str:
        """Generic sanitization"""
        # Remove control characters
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Normalize unicode
        value = value.encode('ascii', 'ignore').decode('ascii')
        
        return value.strip()

class SecurityScanner:
    """Security vulnerability scanner"""
    
    def __init__(self):
        self.scan_rules = self._init_scan_rules()
    
    def _init_scan_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize security scan rules"""
        return {
            "sensitive_data": {
                "patterns": [
                    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                    r'\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b',  # IBAN
                ],
                "severity": "high",
                "description": "Potential sensitive data detected"
            },
            "api_keys": {
                "patterns": [
                    r'api[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
                    r'secret[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
                    r'access[_-]?token[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
                ],
                "severity": "critical",
                "description": "Potential API key or secret detected"
            },
            "file_paths": {
                "patterns": [
                    r'[a-zA-Z]:\\[\\a-zA-Z0-9._-]+',  # Windows paths
                    r'/[a-zA-Z0-9._/-]+',  # Unix paths
                ],
                "severity": "medium",
                "description": "File path detected"
            }
        }
    
    def scan_content(self, content: str) -> Dict[str, Any]:
        """Scan content for security issues"""
        findings = []
        
        for rule_name, rule in self.scan_rules.items():
            for pattern in rule["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        "rule": rule_name,
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "match": match.group(),
                        "position": match.span()
                    })
        
        return {
            "scan_completed": True,
            "findings_count": len(findings),
            "findings": findings,
            "risk_level": self._calculate_risk_level(findings)
        }
    
    def _calculate_risk_level(self, findings: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level"""
        if not findings:
            return "low"
        
        severities = [f["severity"] for f in findings]
        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low" 