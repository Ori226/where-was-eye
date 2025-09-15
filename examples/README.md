# Example Usage Guide

These examples demonstrate how to use Where Was Eye. Before running them, make sure to:

## Prerequisites

1. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Get your Google Timeline data**:
   - Visit [Google Takeout](https://takeout.google.com/)
   - Select "Location History" (JSON format)
   - Download and extract the archive
   - Update `LOCATION_HISTORY_PATH` in your `.env` file

## Running Examples

### Basic Usage
```bash
python examples/basic_usage.py
```

### HTTP API Example
```bash
# First, start the server in one terminal:
python -m where_was_eye.server

# Then in another terminal, run the HTTP example:
python examples/http_api.py
```

### Educational Demo
```bash
python examples/educational_demo.py
```

## Troubleshooting

### If examples fail with import errors:
1. Make sure you installed the package: `pip install -e .`
2. Check that you're in the project root directory
3. Verify your Python path includes the project directory

### If you get "Module not found" errors:
The examples are designed to work after the package is installed. If you want to run them without installation, you can modify them to add the source directory to the Python path:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

### Common Issues:
- **Missing timeline data**: Make sure `LOCATION_HISTORY_PATH` points to a valid JSON file
- **API keys not set**: Set `OPENAI_API_KEY` for OpenAI integration
- **Ollama not running**: Start Ollama with `ollama serve` for local LLM support