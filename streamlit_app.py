"""
AI-Powered Code Reviewer & Optimizer - Streamlit MVP
Main application entry point for the code review tool.
"""

import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
import time

# Import our modules
from app.llm_client import LLMClient
from app.static_analysis import StaticAnalyzer
from app.prompt_templates import PromptTemplates
from app.utils import FileProcessor, DiffGenerator
from app.workers import TaskManager
from app.schema import ReviewResponse, RefactorResponse, TestResponse

# Page configuration
st.set_page_config(
    page_title="AI Code Reviewer & Optimizer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main Streamlit application."""
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'provider' not in st.session_state:
        st.session_state.provider = "OpenAI"
    if 'model' not in st.session_state:
        st.session_state.model = "gpt-4o-mini"
    if 'budget_mode' not in st.session_state:
        st.session_state.budget_mode = "balanced"
    
    # Header
    st.title("🔍 AI-Powered Code Reviewer & Optimizer")
    st.markdown("Upload Python/JavaScript files for automated code review, refactoring suggestions, and test generation.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key & Provider
        st.subheader("API Configuration")
        api_key = st.text_input(
            "API Key", 
            value=st.session_state.api_key,
            type="password",
            help="Your OpenAI API key (stored in session only)"
        )
        st.session_state.api_key = api_key
        
        provider = st.selectbox(
            "Provider",
            ["OpenAI", "Custom"],
            index=0 if st.session_state.provider == "OpenAI" else 1
        )
        st.session_state.provider = provider
        
        if provider == "OpenAI":
            model = st.selectbox(
                "Model",
                ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                index=0 if st.session_state.model == "gpt-4o-mini" else 1
            )
        else:
            model = st.text_input("Custom Model Name", value="custom-model")
        st.session_state.model = model
        
        # Budget mode
        budget_mode = st.selectbox(
            "Analysis Mode",
            ["fast", "balanced", "deep"],
            index=1 if st.session_state.budget_mode == "balanced" else 0
        )
        st.session_state.budget_mode = budget_mode
        
        # Analysis settings
        st.subheader("Analysis Settings")
        max_findings = st.slider("Max Findings", 1, 20, 6)
        run_static_analysis = st.checkbox("Run Static Analysis", True)
        run_llm_review = st.checkbox("Run LLM Review", True)
        generate_tests = st.checkbox("Generate Tests", False)
        js_linting = st.checkbox("Enable JS Linting", False)
        
        # Security warning
        st.warning("⚠️ **Privacy Notice**: Your code will be sent to third-party LLM services. Do not upload sensitive or proprietary code.")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 File Upload")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a Python or JavaScript file",
            type=['py', 'js', 'jsx', 'ts', 'tsx'],
            help="Upload .py, .js, .jsx, .ts, or .tsx files"
        )
        
        # Text input as alternative
        st.subheader("Or paste code directly:")
        code_text = st.text_area(
            "Code Input",
            height=200,
            placeholder="Paste your code here...",
            help="For small code snippets"
        )
        
        # File processing
        file_processor = FileProcessor()
        file_content = None
        filename = None
        language = None
        
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode('utf-8')
            filename = uploaded_file.name
            language = file_processor.detect_language(filename)
        elif code_text.strip():
            file_content = code_text
            filename = "input.py"  # Default
            language = "python"
        
        if file_content:
            # Display file info
            st.success(f"✅ Loaded: {filename} ({language})")
            
            # Token estimate
            token_estimate = len(file_content.split()) * 1.3  # Rough estimate
            st.info(f"📊 Estimated tokens: ~{int(token_estimate)}")
            
            # Show file content
            with st.expander("📄 File Content", expanded=False):
                st.code(file_content, language=language)
    
    with col2:
        st.header("🚀 Run Analysis")
        
        if not api_key and st.session_state.provider == "OpenAI":
            st.error("Please enter your API key in the sidebar.")
        elif not file_content:
            st.info("Please upload a file or paste code to analyze.")
        else:
            if st.button("🔍 Analyze Code", type="primary", use_container_width=True):
                with st.spinner("Running analysis..."):
                    try:
                        # Initialize components
                        llm_client = LLMClient(api_key, st.session_state.provider, st.session_state.model)
                        static_analyzer = StaticAnalyzer()
                        task_manager = TaskManager()
                        
                        # Run analysis
                        results = run_analysis(
                            file_content, filename, language,
                            llm_client, static_analyzer, task_manager,
                            max_findings, run_static_analysis, run_llm_review, generate_tests, js_linting
                        )
                        
                        st.session_state.analysis_results = results
                        st.success("✅ Analysis complete!")
                        
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        st.exception(e)
    
    # Display results
    if st.session_state.analysis_results:
        display_results(st.session_state.analysis_results)

def run_analysis(file_content: str, filename: str, language: str, 
                llm_client: LLMClient, static_analyzer: StaticAnalyzer, 
                task_manager: TaskManager, max_findings: int, 
                run_static_analysis: bool, run_llm_review: bool, 
                generate_tests: bool, js_linting: bool) -> Dict[str, Any]:
    """Run the complete analysis pipeline."""
    
    results = {
        'filename': filename,
        'language': language,
        'timestamp': time.time(),
        'static_analysis': None,
        'review': None,
        'refactors': [],
        'tests': None
    }
    
    # Static analysis
    if run_static_analysis:
        try:
            static_results = static_analyzer.analyze(file_content, filename, language, js_linting)
            results['static_analysis'] = static_results
        except Exception as e:
            st.warning(f"Static analysis failed: {e}")
    
    # LLM Review
    if run_llm_review and llm_client.is_configured():
        try:
            static_output = results['static_analysis'] or {}
            review_response = llm_client.call_review(
                file_content, filename, language, static_output, max_findings
            )
            results['review'] = review_response
        except Exception as e:
            st.error(f"LLM review failed: {e}")
    
    # Generate tests
    if generate_tests and llm_client.is_configured():
        try:
            test_response = llm_client.call_tests(
                file_content, filename, language, "1-100"  # Full file
            )
            results['tests'] = test_response
        except Exception as e:
            st.warning(f"Test generation failed: {e}")
    
    return results

def display_results(results: Dict[str, Any]):
    """Display analysis results in tabs."""
    
    st.header("📊 Analysis Results")
    
    # Create tabs
    tabs = st.tabs(["📋 Summary", "🔍 Findings", "🔄 Refactors", "🧪 Tests", "📄 Raw JSON", "💾 Export"])
    
    with tabs[0]:  # Summary
        display_summary(results)
    
    with tabs[1]:  # Findings
        display_findings(results)
    
    with tabs[2]:  # Refactors
        display_refactors(results)
    
    with tabs[3]:  # Tests
        display_tests(results)
    
    with tabs[4]:  # Raw JSON
        display_raw_json(results)
    
    with tabs[5]:  # Export
        display_export(results)

def display_summary(results: Dict[str, Any]):
    """Display summary information."""
    if not results.get('review'):
        st.info("No review results available. Run LLM review to see summary.")
        return
    
    review = results['review']
    summary = review.get('summary', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Complexity Score", summary.get('complexityScore', 'N/A'))
    
    with col2:
        maintainability = summary.get('maintainability', 'N/A')
        st.metric("Maintainability", maintainability.title())
    
    with col3:
        findings_count = len(review.get('findings', []))
        st.metric("Findings", findings_count)
    
    # Quick actions
    quick_actions = summary.get('quick_actions', [])
    if quick_actions:
        st.subheader("🎯 Quick Actions")
        for action in quick_actions:
            st.write(f"• {action}")

def display_findings(results: Dict[str, Any]):
    """Display findings in a table."""
    if not results.get('review'):
        st.info("No review results available.")
        return
    
    findings = results['review'].get('findings', [])
    if not findings:
        st.success("No issues found!")
        return
    
    st.subheader(f"🔍 Found {len(findings)} Issues")
    
    for i, finding in enumerate(findings):
        with st.expander(f"#{i+1} {finding.get('id', 'unknown')} - {finding.get('severity', 'unknown').title()}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Category:** {finding.get('category', 'unknown')}")
                st.write(f"**Description:** {finding.get('description', 'No description')}")
                st.write(f"**Evidence:** {finding.get('evidence', 'No evidence')}")
                st.write(f"**Suggested Fix:** {finding.get('suggested_fix_summary', 'No suggestion')}")
            
            with col2:
                location = finding.get('location', {})
                st.write(f"**Lines:** {location.get('start_line', '?')}-{location.get('end_line', '?')}")
                st.write(f"**Confidence:** {finding.get('confidence', 'unknown')}")
                
                if st.button(f"Show Diff", key=f"diff_{i}"):
                    # TODO: Implement diff generation
                    st.info("Diff generation not yet implemented")

def display_refactors(results: Dict[str, Any]):
    """Display refactoring suggestions."""
    st.info("Refactoring suggestions will be generated on demand. Select specific findings to refactor.")

def display_tests(results: Dict[str, Any]):
    """Display generated tests."""
    if not results.get('tests'):
        st.info("No tests generated. Enable test generation in settings.")
        return
    
    tests = results['tests']
    st.subheader("🧪 Generated Tests")
    
    st.code(tests.get('test_content', ''), language='python')
    
    if st.button("📥 Download Test File"):
        # TODO: Implement file download
        st.info("Download functionality not yet implemented")

def display_raw_json(results: Dict[str, Any]):
    """Display raw JSON results."""
    st.subheader("📄 Raw JSON Output")
    
    json_str = json.dumps(results, indent=2, default=str)
    st.code(json_str, language='json')
    
    if st.button("📋 Copy JSON"):
        st.code(json_str)
        st.success("JSON copied to clipboard!")

def display_export(results: Dict[str, Any]):
    """Display export options."""
    st.subheader("💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download JSON Report"):
            st.info("JSON download not yet implemented")
    
    with col2:
        if st.button("📦 Download ZIP"):
            st.info("ZIP download not yet implemented")
    
    with col3:
        if st.button("📝 Generate Report"):
            st.info("Report generation not yet implemented")

if __name__ == "__main__":
    main()
