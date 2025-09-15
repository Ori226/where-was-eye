# Where Was Eye 👁️

A tool for querying Google Timeline location history data with AI integration. Perfect for building location-aware AI agents and educational examples of agent tool development.

## Features

- **📊 Google Timeline Parser**: Efficiently parse and query Google Takeout location history JSON
- **🤖 AI Agent Integration**: Works with both OpenAI and Ollama providers
- **🌐 HTTP API**: FastAPI-based REST API for programmatic access
- **🔌 MCP Support**: Model Context Protocol compatible endpoints
- **⚡ Performance Optimized**: Caching system for fast timeline data loading
- **📚 Educational**: Clean, well-documented code perfect for learning agent development

## Installation

### From PyPI (Coming Soon)
```bash
pip install where-was-eye
```

### From Source
```bash
git clone https://github.com/Ori226/where-was-eye.git
cd where-was-eye

# Install in development mode (required for examples to work)
pip install -e .

# Or install regularly
pip install .
```

### Optional Dependencies
For AI integration, install the appropriate extras:

```bash
# For OpenAI support
pip install "where-was-eye[openai]"

# For Ollama support
pip install "where-was-eye[ollama]"

# For development
pip install "where-was-eye[dev]"

# Everything
pip install "where-was-eye[all]"
```

## Docker Deployment

Where Was Eye can also be deployed using Docker:

### Quick Start with Docker Compose
```bash
# Prepare your timeline data
mkdir -p data
cp /path/to/your/Location\ History.json data/location-history.json

# Start the service
docker-compose up
```

### Using Docker Directly
```bash
# Build the image
docker build -t where-was-eye .

# Run the container
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  -e LOCATION_HISTORY_PATH=/data/location-history.json \
  where-was-eye
```

See [DOCKER.md](DOCKER.md) for detailed Docker deployment instructions.

## Quick Start

### 1. Get Your Google Timeline Data

1. Visit [Google Takeout](https://takeout.google.com/)
2. Select "Location History" (JSON format)
3. Download and extract the archive
4. Find the `Location History.json` file

### 2. Set Up Environment Variables

```bash
# Required
export LOCATION_HISTORY_PATH="/path/to/your/Location History.json"

# For OpenAI integration (optional)
export OPENAI_API_KEY="your-openai-api-key"

# For Ollama integration (optional)
export OLLAMA_HOST="http://localhost:11434"  # default
```

### 3. Basic Usage

```python
from where_was_eye import MyTimelineDB, WhereWasEyeAgent

# Initialize timeline database
db = MyTimelineDB("/path/to/Location History.json")

# Query a specific time
location = db.get_location_at_time(2024, 8, 20, 15, 30)
print(f"Location: {location}")

# Use with AI agent
agent = WhereWasEyeAgent()
response = agent.run("Where was I on August 20, 2024 at 3:30 PM?")
print(response)
```

### 4. Start the HTTP Server

```bash
# Start the API server
python -m where_was_eye.server

# Or with custom configuration
python -m where_was_eye.server --host 0.0.0.0 --port 8000 --db-path "/path/to/Location History.json"
```

## API Usage

### HTTP API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /get_location_at_time` - Get location at specific time

**Example Request:**
```bash
curl -X POST "http://localhost:8000/get_location_at_time" \
  -H "Content-Type: application/json" \
  -d '{"year": 2024, "month": 8, "day": 20, "hour": 15, "minute": 30}'
```

**Response:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "success": true
}
```

### AI Agent Integration

```python
from where_was_eye import create_agent

# Create agent with OpenAI
agent = create_agent(
    provider="openai",
    model="gpt-4.1",
    timeline_db_path="/path/to/Location History.json"
)

# Create agent with Ollama
agent = create_agent(
    provider="ollama", 
    model="llama3.1",
    timeline_db_path="/path/to/Location History.json"
)

# Ask questions
questions = [
    "Where was I last Tuesday at 2 PM?",
    "What was my location on Christmas day 2023?",
    "Where was I on August 20, 2024 around lunch time?"
]

for question in questions:
    response = agent.run(question)
    print(f"Q: {question}")
    print(f"A: {response}\n")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCATION_HISTORY_PATH` | Path to Google Timeline JSON file | Required |
| `OPENAI_API_KEY` | OpenAI API key for GPT integration | Optional |
| `OLLAMA_HOST` | Ollama server host | `http://localhost:11434` |

### Programmatic Configuration

```python
from where_was_eye import AgentConfig, ServerConfig

# Agent configuration
agent_config = AgentConfig(
    provider="openai",
    model="gpt-4.1",
    temperature=0.0,
    timeline_db_path="/path/to/data.json",
    openai_api_key="your-key"
)

# Server configuration  
server_config = ServerConfig(
    timeline_db_path="/path/to/data.json",
    host="0.0.0.0",
    port=8000,
    cors_origins=["*"],
    enable_mcp=True
)
```

## Project Structure

```
where_was_eye/
├── src/
│   └── where_was_eye/
│       ├── __init__.py          # Package exports
│       ├── timeline_db.py       # Google Timeline parser
│       ├── agent.py             # AI agent integration
│       └── server.py            # HTTP API server
├── examples/                    # Usage examples
├── tests/                       # Test suite
├── docs/                        # Documentation
├── pyproject.toml              # Package configuration
└── README.md                   # This file
```

## Educational Value

This project serves as an excellent educational resource for:

### 1. Agent Tool Development
- Learn how to create custom tools for AI agents
- Understand tool function definitions and schemas
- See real-world tool execution patterns

### 2. MCP (Model Context Protocol)
- Example of MCP-compatible server implementation
- Learn how to expose functionality to AI models
- Understand the request/response patterns

### 3. Data Processing
- Efficient parsing of large JSON datasets
- Time-based indexing and query optimization
- Cache mechanisms for performance

### 4. API Design
- Clean REST API design with FastAPI
- Proper error handling and validation
- CORS and security considerations

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/Ori226/where-was-eye.git
cd where-was-eye
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

The project includes a comprehensive test suite covering all major components:

```bash
# Install test dependencies
pip install pytest fastapi httpx

# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_timeline_db.py -v
python -m pytest tests/test_agent.py -v
python -m pytest tests/test_server.py -v

# Run tests with coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Run cache-specific tests
python -m src.where_was_eye.timeline_db --test-cache
```

#### Test Structure

- **`tests/test_timeline_db.py`**: Tests for the Google Timeline database parser, including:
  - Interval extraction and datetime parsing
  - Cache functionality with hash-based validation
  - Location querying at specific times
  - Cache invalidation when source files change

- **`tests/test_agent.py`**: Tests for AI agent functionality (OpenAI and Ollama), including:
  - Agent factory function
  - Mocked API responses
  - Error handling
  - Integration with timeline database

- **`tests/test_server.py`**: Tests for the FastAPI server endpoints, including:
  - Health check endpoint
  - Location query endpoints
  - Agent query endpoints
  - CORS headers
  - Error handling and validation

#### Writing Tests

When adding new features, please include corresponding tests. The test suite uses:
- **pytest** for test framework
- **unittest.mock** for mocking external dependencies
- **TestClient** from FastAPI for testing HTTP endpoints
- **tempfile** for creating isolated test data

Tests should be:
- **Isolated**: Each test should set up its own data and clean up afterwards
- **Deterministic**: Tests should produce the same results every time
- **Comprehensive**: Cover both success and error cases
- **Fast**: Tests should run quickly to encourage frequent testing

### Code Style

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Takeout for providing location history data format
- OpenAI for GPT model integration
- Ollama for local LLM support
- FastAPI team for the excellent web framework

## Support

If you have any questions or need help:

- Open an [issue](https://github.com/Ori226/where-was-eye/issues)
- Check the [documentation](docs/)
- Join our [Discussions](https://github.com/Ori226/where-was-eye/discussions)

## Roadmap

- [ ] Add more timeline data sources (Apple, Samsung, etc.)
- [ ] Enhanced location reverse geocoding
- [ ] Visual timeline interface
- [ ] Batch query operations
- [ ] Advanced caching strategies
- [ ] Fine tune LLMs for better agentic collaboration


---

**Where Was Eye** - Because sometimes you need to know where you've been to understand where you're going. 👁️📍