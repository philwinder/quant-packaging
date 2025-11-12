"""Docker container builder for strategies."""

import shutil
from pathlib import Path
from typing import Optional


class DockerBuilder:
    """Build Docker containers for deployed strategies.

    This class generates Dockerfiles and related configuration files to
    package strategies into deployable containers with FastAPI servers.

    Example:
        >>> builder = DockerBuilder()
        >>> builder.create_deployment(
        ...     strategy_name="momentum_strategy",
        ...     strategy_dir="./strategies/momentum_strategy"
        ... )
    """

    def __init__(self, output_dir: str = "./deployments"):
        """Initialize the Docker builder.

        Args:
            output_dir: Directory where deployment files will be created
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_deployment(
        self,
        strategy_name: str,
        strategy_dir: str,
        port: int = 8000,
        python_version: str = "3.11",
    ) -> Path:
        """Create a complete Docker deployment for a strategy.

        Args:
            strategy_name: Name of the strategy
            strategy_dir: Path to the strategy directory
            port: Port to expose for the FastAPI server
            python_version: Python version to use in the container

        Returns:
            Path to the created deployment directory
        """
        strategy_path = Path(strategy_dir)
        if not strategy_path.exists():
            raise ValueError(f"Strategy directory not found: {strategy_dir}")

        # Create deployment directory
        deploy_dir = self.output_dir / strategy_name
        deploy_dir.mkdir(parents=True, exist_ok=True)

        # Copy strategy files
        strategy_dest = deploy_dir / "strategy"
        if strategy_dest.exists():
            shutil.rmtree(strategy_dest)
        shutil.copytree(strategy_path, strategy_dest)

        # Create Dockerfile
        self._create_dockerfile(deploy_dir, python_version, port)

        # Create FastAPI server
        self._create_server(deploy_dir, strategy_name)

        # Create requirements.txt for the deployment
        self._create_deployment_requirements(deploy_dir, strategy_path)

        # Create docker-compose.yml
        self._create_docker_compose(deploy_dir, strategy_name, port)

        # Create build and run scripts
        self._create_scripts(deploy_dir, strategy_name)

        # Create README
        self._create_deployment_readme(deploy_dir, strategy_name, port)

        print(f"\n✓ Deployment created for '{strategy_name}' in {deploy_dir}")
        print(f"\nTo build and run:")
        print(f"  cd {deploy_dir}")
        print(f"  docker-compose up --build")
        print(f"\nOr use the scripts:")
        print(f"  cd {deploy_dir}")
        print(f"  ./build.sh")
        print(f"  ./run.sh")

        return deploy_dir

    def _create_dockerfile(self, deploy_dir: Path, python_version: str, port: int) -> None:
        """Create Dockerfile for the deployment."""
        dockerfile_content = f'''FROM python:{python_version}-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy strategy and server
COPY strategy/ ./strategy/
COPY server.py .

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')"

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "{port}"]
'''
        (deploy_dir / "Dockerfile").write_text(dockerfile_content)

    def _create_server(self, deploy_dir: Path, strategy_name: str) -> None:
        """Create FastAPI server for the strategy."""
        server_content = '''"""FastAPI server for quant strategy deployment."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any
import pandas as pd
import dill
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="Quant Strategy API",
    description="REST API for quant trading strategy",
    version="1.0.0"
)

# Load strategy at startup
strategy_func = None
strategy_metadata = {}

def load_strategy():
    """Load the serialized strategy."""
    global strategy_func, strategy_metadata

    strategy_dir = Path("./strategy")

    # Load strategy function
    with open(strategy_dir / "strategy.pkl", "rb") as f:
        strategy_func = dill.load(f)

    # Ensure pandas is available in the function's globals
    if strategy_func and hasattr(strategy_func, '__globals__'):
        strategy_func.__globals__['pd'] = pd

    # Load metadata
    metadata_path = strategy_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            strategy_metadata = json.load(f)

# Load strategy on startup
load_strategy()


class MarketData(BaseModel):
    """Market data input model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    data: List[Dict[str, Any]] = Field(
        ...,
        description="List of OHLCV records with columns: timestamp, open, high, low, close, volume"
    )


class SignalResponse(BaseModel):
    """Strategy signal response model."""
    signals: List[float] = Field(..., description="Position signals (1.0=long, 0.0=flat, -1.0=short)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Strategy metadata")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Quant Strategy API",
        "strategy": {
            "name": strategy_metadata.get("name", "Unknown"),
            "version": strategy_metadata.get("version", "Unknown"),
            "description": strategy_metadata.get("description", "")
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "strategy_loaded": strategy_func is not None}


@app.get("/info")
async def info():
    """Get strategy information."""
    return {
        "metadata": strategy_metadata,
        "function_name": strategy_func.__name__ if strategy_func else None,
        "loaded": strategy_func is not None
    }


@app.post("/predict", response_model=SignalResponse)
async def predict(market_data: MarketData):
    """Generate trading signals from market data.

    Args:
        market_data: Historical OHLCV data

    Returns:
        Trading signals and metadata
    """
    if strategy_func is None:
        raise HTTPException(status_code=500, detail="Strategy not loaded")

    try:
        # Convert input to DataFrame
        df = pd.DataFrame(market_data.data)

        # Ensure timestamp is datetime if present
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')

        # Run strategy
        signals = strategy_func(df)

        # Convert signals to list
        signals_list = signals.tolist() if hasattr(signals, 'tolist') else list(signals)

        return SignalResponse(
            signals=signals_list,
            metadata=strategy_metadata
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        (deploy_dir / "server.py").write_text(server_content)

    def _create_deployment_requirements(self, deploy_dir: Path, strategy_path: Path) -> None:
        """Create requirements.txt for the deployment."""
        # Read strategy requirements
        strategy_req_path = strategy_path / "requirements.txt"
        strategy_requirements = []
        if strategy_req_path.exists():
            strategy_requirements = strategy_req_path.read_text().strip().split("\n")

        # Combine with server requirements
        server_requirements = [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6",
        ]

        all_requirements = list(set(strategy_requirements + server_requirements))
        all_requirements.sort()

        (deploy_dir / "requirements.txt").write_text("\n".join(all_requirements))

    def _create_docker_compose(self, deploy_dir: Path, strategy_name: str, port: int) -> None:
        """Create docker-compose.yml for easy deployment."""
        compose_content = f'''version: '3.8'

services:
  {strategy_name.replace("_", "-")}:
    build: .
    container_name: {strategy_name}
    ports:
      - "{port}:{port}"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s
'''
        (deploy_dir / "docker-compose.yml").write_text(compose_content)

    def _create_scripts(self, deploy_dir: Path, strategy_name: str) -> None:
        """Create build and run scripts."""
        # Build script
        build_script = f'''#!/bin/bash
set -e

echo "Building Docker image for {strategy_name}..."
docker build -t {strategy_name}:latest .

echo "Build complete!"
echo "Run with: ./run.sh"
'''
        build_path = deploy_dir / "build.sh"
        build_path.write_text(build_script)
        build_path.chmod(0o755)

        # Run script
        run_script = f'''#!/bin/bash
set -e

echo "Starting {strategy_name} container..."
docker-compose up -d

echo "Container started!"
echo "API available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "View logs with: docker-compose logs -f"
echo "Stop with: docker-compose down"
'''
        run_path = deploy_dir / "run.sh"
        run_path.write_text(run_script)
        run_path.chmod(0o755)

    def _create_deployment_readme(self, deploy_dir: Path, strategy_name: str, port: int) -> None:
        """Create README for the deployment."""
        readme_content = f'''# {strategy_name} Deployment

This directory contains a Docker deployment for the `{strategy_name}` trading strategy.

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

### Using Build Scripts

```bash
./build.sh  # Build the Docker image
./run.sh    # Run the container
```

### Manual Docker Commands

```bash
# Build
docker build -t {strategy_name}:latest .

# Run
docker run -d -p {port}:{port} --name {strategy_name} {strategy_name}:latest
```

## API Usage

Once running, the API will be available at `http://localhost:{port}`

### Endpoints

- `GET /` - Root endpoint with strategy info
- `GET /health` - Health check
- `GET /info` - Strategy metadata
- `POST /predict` - Generate trading signals
- `GET /docs` - Interactive API documentation (Swagger UI)

### Example Request

```bash
curl -X POST "http://localhost:{port}/predict" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "data": [
      {{
        "timestamp": "2024-01-01T00:00:00",
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 103.0,
        "volume": 1000000
      }},
      {{
        "timestamp": "2024-01-02T00:00:00",
        "open": 103.0,
        "high": 107.0,
        "low": 102.0,
        "close": 106.0,
        "volume": 1200000
      }}
    ]
  }}'
```

### Python Client Example

```python
import requests
import pandas as pd

# Prepare data
data = {{
    "data": [
        {{
            "timestamp": "2024-01-01T00:00:00",
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000
        }}
    ]
}}

# Make request
response = requests.post("http://localhost:{port}/predict", json=data)
result = response.json()

print("Signals:", result["signals"])
print("Metadata:", result["metadata"])
```

## Management

```bash
# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart

# Remove container and image
docker-compose down --rmi all
```

## Files

- `Dockerfile` - Container image definition
- `docker-compose.yml` - Docker Compose configuration
- `server.py` - FastAPI server implementation
- `strategy/` - Strategy files (strategy.pkl, metadata.json, requirements.txt)
- `requirements.txt` - Python dependencies
- `build.sh` - Build script
- `run.sh` - Run script

## Customization

To modify the server behavior, edit `server.py`. The strategy itself is loaded from `./strategy/strategy.pkl`.

To update the strategy, replace the contents of the `strategy/` directory and rebuild the container.
'''
        (deploy_dir / "README.md").write_text(readme_content)
