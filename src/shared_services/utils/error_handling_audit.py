"""
Error Handling Consistency Audit and Improvement System
=======================================================

Audits and improves error handling consistency across the codebase.
Implements fail-fast behavior for critical errors and proper error propagation.

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

# Simple logger setup as fallback if shared_services.utils.logger is not available
logger = logging.getLogger(__name__)
try:
    from shared_services.utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def audit_errors(
    module_path: str, 
    output_file: Optional[str] = None,
    severity_threshold: str = "WARNING"
) -> Dict[str, Any]:
    """
    Audit error handling patterns in a specific module or file
    
    Args:
        module_path: Path to the module or file to audit
        output_file: Optional path to save audit results as JSON
        severity_threshold: Minimum severity level to report ("CRITICAL", "ERROR", "WARNING")
        
    Returns:
        Dict containing audit results with issues found
    """
    logger.info(f"Starting error handling audit for {module_path}")
    
    issues = []
    severity_levels = {
        "CRITICAL": 30,
        "ERROR": 20,
        "WARNING": 10
    }
    min_severity = severity_levels.get(severity_threshold, 10)
    
    # Critical patterns that indicate problematic error handling
    critical_patterns = [
        (r"except\s+Exception\s+as\s+\w+:\s*logger\.error.*\n(?!\s*raise)", 
         "CRITICAL", "Exception caught but errors not propagated"),
        (r"except\s+Exception\s+as\s+\w+:\s*pass", 
         "CRITICAL", "Silent exception handling"),
        (r"except:\s*pass", 
         "CRITICAL", "Bare except with silent failure"),
        (r"try:.*except.*return\s+None\s*$", 
         "CRITICAL", "Returning None on exception without logging")
    ]
    
    # Warning patterns
    warning_patterns = [
        (r"logger\.error\(.*\)\s*$(?!\s*raise)", 
         "WARNING", "Error logging without raising"),
        (r"except\s+.*:\s*logger\.warning", 
         "WARNING", "Using warning for potentially critical errors")
    ]
    
    all_patterns = critical_patterns + warning_patterns
    
    try:
        if os.path.isfile(module_path):
            # Audit a single file
            issues.extend(_audit_file(module_path, all_patterns, min_severity))
        elif os.path.isdir(module_path):
            # Recursively audit a directory
            for root, _, files in os.walk(module_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        issues.extend(_audit_file(file_path, all_patterns, min_severity))
        else:
            logger.error(f"Path not found: {module_path}")
            return {"error": f"Path not found: {module_path}", "issues": []}
    
    except Exception as e:
        logger.error(f"Error during audit: {str(e)}")
        return {"error": str(e), "issues": []}
    
    # Create audit report
    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "module_path": module_path,
        "total_issues": len(issues),
        "issues_by_severity": {
            "CRITICAL": len([i for i in issues if i["severity"] == "CRITICAL"]),
            "ERROR": len([i for i in issues if i["severity"] == "ERROR"]),
            "WARNING": len([i for i in issues if i["severity"] == "WARNING"])
        },
        "issues": issues
    }
    
    # Save to file if requested
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(audit_report, f, indent=2)
            logger.info(f"Audit report saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save audit report: {str(e)}")
    
    return audit_report


def _audit_file(file_path: str, patterns: List[tuple[str, str, str]], min_severity: int) -> List[Dict[str, Any]]:
    """Audit a single file for error handling issues"""
    issues = []
    severity_levels = {
        "CRITICAL": 30,
        "ERROR": 20,
        "WARNING": 10
    }
    
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        
        # Check all patterns
        for pattern, severity, description in patterns:
            if severity_levels.get(severity, 0) < min_severity:
                continue
                
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                
                # Get code snippet for context
                start = max(0, line_num - 3 - 1)
                end = min(len(lines), line_num + 3)
                snippet_lines = []
                for i in range(start, end):
                    marker = ">>> " if i == line_num - 1 else "    "
                    snippet_lines.append(f"{marker}{i+1:3d}: {lines[i]}")
                code_snippet = "\n".join(snippet_lines)
                
                issues.append({
                    "file_path": file_path,
                    "line_number": line_num,
                    "severity": severity,
                    "description": description,
                    "code_snippet": code_snippet
                })
    except Exception as e:
        logger.error(f"Failed to audit file {file_path}: {str(e)}")
    
    return issues


def run_error_handling_audit(
    module_path: str, 
    output_file: Optional[str] = None,
    severity_threshold: str = "WARNING"
) -> Dict[str, Any]:
    """
    Audit error handling patterns in a specific module or file
    
    Args:
        module_path: Path to the module or file to audit
        output_file: Optional path to save audit results as JSON
        severity_threshold: Minimum severity level to report ("CRITICAL", "ERROR", "WARNING")
        
    Returns:
        Dict containing audit results with issues found
    """
    logger.info(f"Starting error handling audit for {module_path}")
    
    issues = []
    severity_levels = {
        "CRITICAL": 30,
        "ERROR": 20,
        "WARNING": 10
    }
    min_severity = severity_levels.get(severity_threshold, 10)
    
    # Critical patterns that indicate problematic error handling
    critical_patterns = [
        (r"except\s+Exception\s+as\s+\w+:\s*logger\.error.*\n(?!\s*raise)", 
         "CRITICAL", "Exception caught but errors not propagated"),
        (r"except\s+Exception\s+as\s+\w+:\s*pass", 
         "CRITICAL", "Silent exception handling"),
        (r"except:\s*pass", 
         "CRITICAL", "Bare except with silent failure"),
        (r"try:.*except.*return\s+None\s*$", 
         "CRITICAL", "Returning None on exception without logging")
    ]
    
    # Warning patterns
    warning_patterns = [
        (r"logger\.error\(.*\)\s*$(?!\s*raise)", 
         "WARNING", "Error logging without raising"),
        (r"except\s+.*:\s*logger\.warning", 
         "WARNING", "Using warning for potentially critical errors")
    ]
    
    all_patterns = critical_patterns + warning_patterns
    
    try:
        if os.path.isfile(module_path):
            # Audit a single file
            issues.extend(_audit_file(module_path, all_patterns, min_severity))
        elif os.path.isdir(module_path):
            # Recursively audit a directory
            for root, _, files in os.walk(module_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        issues.extend(_audit_file(file_path, all_patterns, min_severity))
        else:
            logger.error(f"Path not found: {module_path}")
            return {"error": f"Path not found: {module_path}", "issues": []}
    
    except Exception as e:
        logger.error(f"Error during audit: {str(e)}")
        return {"error": str(e), "issues": []}
    
    # Create audit report
    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "module_path": module_path,
        "total_issues": len(issues),
        "issues_by_severity": {
            "CRITICAL": len([i for i in issues if i["severity"] == "CRITICAL"]),
            "ERROR": len([i for i in issues if i["severity"] == "ERROR"]),
            "WARNING": len([i for i in issues if i["severity"] == "WARNING"])
        },
        "issues": issues
    }
    
    # Save to file if requested
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(audit_report, f, indent=2)
            logger.info(f"Audit report saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save audit report: {str(e)}")
    
    return audit_report

def _audit_file(file_path: str, patterns: List[tuple[str, str, str]], min_severity: int) -> List[Dict[str, Any]]:
    """Audit a single file for error handling issues"""
    issues = []
    severity_levels = {
        "CRITICAL": 30,
        "ERROR": 20,
        "WARNING": 10
    }
    
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        
        # Check all patterns
        for pattern, severity, description in patterns:
            if severity_levels.get(severity, 0) < min_severity:
                continue
                
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                
                # Get code snippet for context
                start = max(0, line_num - 3 - 1)
                end = min(len(lines), line_num + 3)
                snippet_lines = []
                for i in range(start, end):
                    marker = ">>> " if i == line_num - 1 else "    "
                    snippet_lines.append(f"{marker}{i+1:3d}: {lines[i]}")
                code_snippet = "\n".join(snippet_lines)
                
                issues.append({
                    "file_path": file_path,
                    "line_number": line_num,
                    "severity": severity,
                    "description": description,
                    "code_snippet": code_snippet
                })
    except Exception as e:
        logger.error(f"Failed to audit file {file_path}: {str(e)}")
    
    return issues

# Alias for backwards compatibility
audit_errors = run_error_handling_audit
