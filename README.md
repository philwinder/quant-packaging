# Quant Strategy Packaging

A Python library for packaging quantitative trading strategies developed in Jupyter notebooks into deployable Docker containers with REST APIs.

## Overview

**Quant Strategy Packaging** makes it effortless for quantitative analysts to take their trading strategies from Jupyter notebooks to production. With just a few lines of code, you can:

- 📦 **Serialize your strategy functions** using dill (better than pickle for functions)
- 🐳 **Generate Docker deployments** with FastAPI REST APIs
- 🚀 **Deploy anywhere** - local, cloud, or Kubernetes
- 🔄 **Version and track** your strategies with metadata
- 🧪 **Test before deployment** with the StrategyContainer

## Installation

```bash
# Install from source
pip install -e .

# Install with server dependencies (FastAPI, uvicorn)
pip install -e ".[server]"

# Install with dev dependencies (Jupyter, pytest)
pip install -e ".[dev]"
```

## Quick Start

### 1. Define Your Strategy

```python
import pandas as pd

def my_strategy(data):
    """
    Your trading strategy.

    Args:
        data: DataFrame with OHLCV columns (open, high, low, close, volume)

    Returns:
        Series with position signals (1.0=long, 0.0=flat, -1.0=short)
    """
    # Calculate 20-day moving average
    ma_20 = data['close'].rolling(window=20).mean()

    # Generate signals
    signals = pd.Series(0.0, index=data.index)
    signals[data['close'] > ma_20] = 1.0  # Long
    signals[data['close'] <= ma_20] = 0.0  # Flat

    return signals
```

### 2. Package the Strategy

```python
from quant_packaging import StrategyPackager

packager = StrategyPackager(output_dir="./strategies")

packager.save_strategy(
    strategy_func=my_strategy,
    name="momentum_ma20",
    description="Momentum strategy using 20-day MA",
    requirements=["pandas>=1.5.0", "numpy>=1.24.0"],
    version="1.0.0"
)
```

### 3. Create Docker Deployment

```python
from quant_packaging import DockerBuilder

builder = DockerBuilder(output_dir="./deployments")

builder.create_deployment(
    strategy_name="momentum_ma20",
    strategy_dir="./strategies/momentum_ma20",
    port=8000
)
```

### 4. Deploy

```bash
cd deployments/momentum_ma20
docker-compose up --build
```

Your strategy is now running as a REST API at `http://localhost:8000`!

## API Usage

Once deployed, your strategy exposes a REST API:

### Get Strategy Info

```bash
curl http://localhost:8000/info
```

### Generate Signals

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "timestamp": "2024-01-01T00:00:00",
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 103.0,
        "volume": 1000000
      }
    ]
  }'
```

### Python Client Example

```python
import requests
import pandas as pd

# Prepare your market data
data = {
    "data": [
        {
            "timestamp": "2024-01-01T00:00:00",
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000
        }
    ]
}

# Make request
response = requests.post("http://localhost:8000/predict", json=data)
result = response.json()

print("Signals:", result["signals"])
```

## Complete Example

See [examples/strategy_packaging_demo.ipynb](examples/strategy_packaging_demo.ipynb) for a complete end-to-end example including:

- Creating sample market data
- Defining and testing a strategy
- Packaging the strategy
- Testing the packaged strategy locally
- Building a Docker deployment
- Using the deployed API

## Library Components

### StrategyPackager

Handles serialization of strategy functions and metadata.

```python
from quant_packaging import StrategyPackager

packager = StrategyPackager(output_dir="./strategies")

# Save a strategy
packager.save_strategy(
    strategy_func=my_func,
    name="my_strategy",
    description="Strategy description",
    requirements=["pandas", "numpy"],
    version="1.0.0",
    metadata={"author": "Your Name"}
)

# Load a strategy
strategy_func, metadata = packager.load_strategy("my_strategy")

# List all strategies
strategies = packager.list_strategies()
```

### StrategyContainer

Loads and runs serialized strategies (used in production).

```python
from quant_packaging import StrategyContainer

# Load strategy
container = StrategyContainer("./strategies/my_strategy")

# Run on data
signals = container.run(market_data)

# Get info
info = container.get_info()
```

### DockerBuilder

Generates Docker deployments with FastAPI servers.

```python
from quant_packaging import DockerBuilder

builder = DockerBuilder(output_dir="./deployments")

builder.create_deployment(
    strategy_name="my_strategy",
    strategy_dir="./strategies/my_strategy",
    port=8000,
    python_version="3.11"
)
```

## Strategy Format

Strategies should follow this pattern (compatible with [quant-helper](https://github.com/philwinder/quant-helper)):

**Input**: pandas DataFrame with OHLCV data
- `open`: Opening prices
- `high`: High prices
- `low`: Low prices
- `close`: Closing prices
- `volume`: Trading volume

**Output**: pandas Series with position signals
- `1.0`: Long position
- `0.0`: Flat/no position
- `-1.0`: Short position

## Deployment Options

The generated Docker containers can be deployed to:

- **Local Docker**: `docker-compose up`
- **Docker Hub**: `docker push yourname/strategy:latest`
- **AWS ECS**: Use the Dockerfile with ECS task definitions
- **Google Cloud Run**: Deploy with `gcloud run deploy`
- **Kubernetes**: Use the Dockerfile in your k8s manifests
- **Azure Container Instances**: Deploy with `az container create`

## Project Structure

```
quant-packaging/
├── quant_packaging/          # Main library
│   ├── __init__.py
│   ├── packager.py          # Strategy serialization
│   ├── container.py         # Strategy loading/execution
│   └── docker_builder.py    # Docker deployment generation
├── examples/
│   └── strategy_packaging_demo.ipynb  # Complete example
├── pyproject.toml           # Package configuration
└── README.md
```

## Generated Files

### Strategy Directory Structure

```
strategies/
└── my_strategy/
    ├── strategy.pkl         # Serialized strategy function
    ├── metadata.json        # Strategy metadata
    └── requirements.txt     # Python dependencies
```

### Deployment Directory Structure

```
deployments/
└── my_strategy/
    ├── Dockerfile           # Container definition
    ├── docker-compose.yml   # Docker Compose config
    ├── server.py           # FastAPI server
    ├── requirements.txt    # All dependencies
    ├── strategy/           # Strategy files
    ├── build.sh           # Build script
    ├── run.sh             # Run script
    └── README.md          # Deployment docs
```

## Requirements

- Python 3.9+
- pandas >= 1.5.0
- numpy >= 1.24.0
- dill >= 0.3.7
- pydantic >= 2.0.0
- pyyaml >= 6.0

### Optional Dependencies

**Server** (for local testing):
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- python-multipart >= 0.0.6

**Development**:
- pytest >= 7.4.0
- jupyter >= 1.0.0
- ipython >= 8.0.0

## Use Cases

This library is perfect for:

- 🎯 **Quant researchers** who develop strategies in notebooks and need to deploy them
- 🏦 **Trading firms** that want to standardize strategy deployment
- 🤖 **Automated trading systems** that need to load strategies dynamically
- 📊 **Backtesting platforms** that want to support user-defined strategies
- 🔧 **Third-party coding assistants** that help quants package their work

## Design Principles

- **Easy to use**: Minimal code to go from notebook to deployment
- **Self-contained**: Deployments don't depend on the packaging library
- **Flexible**: Works with any strategy that follows the input/output contract
- **Production-ready**: Generated APIs include health checks, error handling, and docs
- **Versioned**: Track strategy versions and metadata

## Integration with Quant Helper

This library is designed to work seamlessly with [quant-helper](https://github.com/philwinder/quant-helper):

```python
from quant_helper import MarketData, Backtester
from quant_packaging import StrategyPackager

# Develop with quant-helper
market = MarketData()
data = market.fetch_ohlcv("bitcoin", days=365)

def my_strategy(data):
    # Your strategy logic
    return signals

# Test with backtester
backtester = Backtester(data)
results = backtester.run(my_strategy)

# Package for deployment
packager = StrategyPackager()
packager.save_strategy(my_strategy, "my_strategy")
```

## API Documentation

When your container is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

Contributions are welcome! This library is designed to be:
- Easy to extend with new deployment targets
- Compatible with various serialization formats
- Flexible for different API frameworks

## License

MIT License - see LICENSE file for details

## Related Projects

- [quant-helper](https://github.com/philwinder/quant-helper) - Helper library for developing quant trading strategies

## Author

Phil Winder - [phil@winder.ai](mailto:phil@winder.ai)

## Acknowledgments

Built for quantitative analysts who want to focus on strategy development, not deployment infrastructure
