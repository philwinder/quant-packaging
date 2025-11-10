# Development Guide

This guide covers setting up the development environment for quant-packaging.

## Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- Docker (for testing deployments)

## Setup with uv (Recommended)

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
git clone https://github.com/philwinder/quant-packaging.git
cd quant-packaging

# Install all dependencies (including dev)
uv sync --all-extras
```

### 3. Activate Virtual Environment

```bash
# uv creates a .venv automatically
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 4. Run Examples

```bash
# Run the simple Python example
uv run examples/simple_example.py

# Or activate the venv and run directly
source .venv/bin/activate
python examples/simple_example.py

# Start Jupyter for the notebook example
uv run jupyter notebook examples/
```

## Development Workflow

### Running Tests

```bash
uv run pytest
```

### Code Formatting and Linting

```bash
# Format code with ruff
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add to specific extra
uv add --optional server package-name

# Add dev dependency
uv add --dev package-name
```

### Building the Package

```bash
# Build distribution
uv build

# This creates dist/ with wheel and sdist
```

## Project Structure for Development

```
quant-packaging/
├── quant_packaging/       # Source code
│   ├── __init__.py
│   ├── packager.py
│   ├── container.py
│   └── docker_builder.py
├── examples/              # Examples and demos
├── tests/                # Tests (TODO)
├── pyproject.toml        # Project configuration
├── uv.lock              # Locked dependencies
└── .venv/               # Virtual environment (created by uv)
```

## Testing Strategy Packaging

### Quick Test

```bash
# Install in development mode
uv sync --all-extras

# Run the simple example
uv run examples/simple_example.py
```

This will:
1. Create sample data
2. Define a strategy
3. Package it to `examples/strategies/`
4. Test loading it
5. Build a Docker deployment to `examples/deployments/`

### Test the Docker Deployment

```bash
cd examples/deployments/momentum_ma20
docker-compose up --build
```

Then in another terminal:

```bash
# Test the API
curl http://localhost:8000/health
curl http://localhost:8000/info

# View API docs
open http://localhost:8000/docs
```

## Common Tasks

### Create a New Strategy

```python
from quant_packaging import StrategyPackager

def my_new_strategy(data):
    # Your strategy logic
    return signals

packager = StrategyPackager()
packager.save_strategy(
    my_new_strategy,
    name="my_strategy",
    description="My trading strategy"
)
```

### Build and Test Deployment

```python
from quant_packaging import DockerBuilder

builder = DockerBuilder()
builder.create_deployment(
    strategy_name="my_strategy",
    strategy_dir="./strategies/my_strategy"
)
```

## Troubleshooting

### uv sync fails

```bash
# Remove lock file and retry
rm uv.lock
uv lock
uv sync
```

### Import errors

Make sure you're in the virtual environment:

```bash
source .venv/bin/activate
python -c "import quant_packaging; print(quant_packaging.__version__)"
```

### Docker build fails

Check that all requirements are properly listed in the strategy's requirements.txt:

```bash
cat strategies/my_strategy/requirements.txt
```

## Using Traditional Tools

If you prefer pip/venv:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev,server]"

# Run examples
python examples/simple_example.py
```

## Contributing

When contributing:

1. Use `uv` for dependency management
2. Run `ruff format` before committing
3. Add tests for new features (in `tests/`)
4. Update documentation
5. Ensure examples still work

## Performance Notes

Why uv is recommended:

- **10-100x faster** than pip for package resolution
- **Instant** virtual environment creation
- **Deterministic** installs via lockfile
- **Built-in** formatting and linting tools
- Works great with monorepos and CI/CD

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [Hatchling Build System](https://hatch.pypa.io/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
