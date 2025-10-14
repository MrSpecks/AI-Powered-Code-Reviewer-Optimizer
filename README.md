# AI-Powered Code Reviewer & Optimizer

A Streamlit-based MVP that provides automated code review, refactoring suggestions, and test generation using Large Language Models (LLMs). The tool supports Python and JavaScript files with static analysis integration.

## 🚀 Features

- **Automated Code Review**: AI-powered analysis of code quality, readability, and best practices
- **Static Analysis Integration**: Supports flake8, radon for Python and ESLint for JavaScript
- **Refactoring Suggestions**: Multiple refactoring modes (minimal-change, readability-first, performance-first)
- **Test Generation**: Automated unit test generation for Python (pytest) and JavaScript (Jest)
- **Security Analysis**: Security vulnerability detection and mitigation suggestions
- **Interactive UI**: Clean Streamlit interface with real-time analysis results
- **Export Capabilities**: Download analysis reports, patches, and generated tests

## 📋 Requirements

- Python 3.8+
- Node.js (optional, for JavaScript linting)
- OpenAI API key or custom LLM provider

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Powered-Code-Reviewer-Optimizer
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install JavaScript dependencies (optional)**
   ```bash
   npm install -g eslint
   ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t ai-code-reviewer .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 -e OPENAI_API_KEY=your_api_key ai-code-reviewer
   ```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required for LLM functionality)
- `STREAMLIT_SERVER_PORT`: Port for Streamlit server (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: localhost)

### API Key Security

⚠️ **Important Security Notes**:
- API keys are stored in session state only and never persisted to disk
- Code uploaded to the tool will be sent to third-party LLM services
- Do not upload sensitive or proprietary code
- For production use, consider implementing a server-side proxy for API keys

## 📖 Usage

### Basic Workflow

1. **Start the application** using one of the methods above
2. **Configure your API key** in the sidebar
3. **Upload a file** or paste code directly
4. **Configure analysis settings**:
   - Max findings (default: 6)
   - Enable/disable static analysis
   - Enable/disable LLM review
   - Enable/disable test generation
5. **Run analysis** and view results in the tabs:
   - **Summary**: Complexity score, maintainability, quick actions
   - **Findings**: Detailed issues with evidence and suggestions
   - **Refactors**: Alternative implementations with unified diffs
   - **Tests**: Generated unit tests
   - **Raw JSON**: Complete analysis results
   - **Export**: Download reports and artifacts

### Supported File Types

- **Python**: `.py` files
- **JavaScript**: `.js`, `.jsx` files
- **TypeScript**: `.ts`, `.tsx` files

### Analysis Modes

- **Fast**: Quick analysis with basic checks
- **Balanced**: Comprehensive analysis with moderate depth
- **Deep**: Thorough analysis with detailed suggestions

## 🏗️ Architecture

### Core Modules

- **`app/schema.py`**: JSON schema definitions and data classes
- **`app/prompt_templates.py`**: LLM prompt template loader
- **`app/utils.py`**: File processing, chunking, and diff utilities
- **`app/static_analysis.py`**: Static analysis tool integration
- **`app/llm_client.py`**: LLM API client with response validation
- **`app/workers.py`**: Background task execution
- **`streamlit_app.py`**: Main Streamlit application

### Static Analysis Tools

- **Python**: flake8 (linting), radon (complexity metrics)
- **JavaScript**: ESLint (linting), basic pattern analysis
- **Fallback**: Graceful degradation when tools are unavailable

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_utils.py
```

## 📊 Sample Data

The `sample_data/` directory contains example files for testing:
- `math_utils.py`: Python module with various functions
- `example.js`: JavaScript file with common patterns

## 🔒 Security Considerations

- **API Key Protection**: Keys are never logged or persisted
- **Code Privacy**: Uploaded code is sent to LLM providers
- **Temporary Storage**: Analysis artifacts are stored temporarily
- **Input Validation**: All inputs are validated and sanitized

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Set all required environment variables
2. **API Key Management**: Use secure key management systems
3. **Resource Limits**: Configure appropriate memory and CPU limits
4. **Monitoring**: Set up logging and monitoring for the application
5. **Scaling**: Consider horizontal scaling for high-traffic scenarios

### Docker Compose Example

```yaml
version: '3.8'
services:
  ai-code-reviewer:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./artifacts:/app/artifacts
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **API Key Not Working**: Ensure the key is valid and has sufficient credits
2. **Static Analysis Failing**: Install required tools (flake8, radon, eslint)
3. **Memory Issues**: Reduce file size or enable chunking for large files
4. **Slow Performance**: Check API rate limits and network connectivity

### Getting Help

- Check the [Issues](https://github.com/your-repo/issues) page
- Review the logs for error messages
- Ensure all dependencies are properly installed

## 🔮 Future Enhancements

- Support for additional programming languages
- Integration with more static analysis tools
- Custom prompt template editor
- Batch processing capabilities
- Integration with CI/CD pipelines
- On-premises deployment options
- Advanced security scanning
- Code quality metrics dashboard

## 📈 Performance

- **File Size Limits**: Large files are automatically chunked
- **Caching**: Analysis results are cached for repeated requests
- **Background Processing**: Long-running tasks don't block the UI
- **Resource Management**: Automatic cleanup of temporary files

---

**Note**: This is an MVP (Minimum Viable Product) designed for demonstration and testing purposes. For production use, additional security, performance, and reliability measures should be implemented.
