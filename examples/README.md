# Examples

This directory contains example notebooks demonstrating how to use the quant-packaging library.

## Available Examples

### [strategy_packaging_demo.ipynb](strategy_packaging_demo.ipynb)

A comprehensive end-to-end example showing:

1. Creating sample market data
2. Defining a trading strategy (momentum-based)
3. Packaging the strategy using `StrategyPackager`
4. Testing the packaged strategy locally with `StrategyContainer`
5. Building a Docker deployment with `DockerBuilder`
6. Testing the deployed REST API

## Running the Examples

### Prerequisites

Install the library with dev dependencies:

**Using uv (recommended):**
```bash
uv sync --extra dev
```

**Using pip:**
```bash
pip install -e ".[dev]"
```

### Run the Python Example

```bash
# Using uv
uv run examples/simple_example.py

# Or with activated venv
python examples/simple_example.py
```

### Launch Jupyter

**Using uv:**
```bash
uv run jupyter notebook examples/
```

**Using pip:**
```bash
jupyter notebook examples/
```

Then open `strategy_packaging_demo.ipynb` and run through the cells.

## What You'll Learn

- How to structure a trading strategy for the quant-helper pattern
- How to serialize and package strategies
- How to test packaged strategies before deployment
- How to build production-ready Docker containers
- How to interact with the deployed REST API

## Example Strategy Patterns

The notebook includes examples of:

- **Momentum Strategy**: Using moving average crossovers
- **Signal Generation**: Creating position signals (long/flat/short)
- **Data Validation**: Ensuring proper input format
- **API Integration**: Calling the deployed strategy API

## Generated Artifacts

When you run the example, it will create:

```
examples/
├── strategies/
│   └── momentum_ma20/         # Packaged strategy
└── deployments/
    └── momentum_ma20/         # Docker deployment
```

These directories are gitignored but provide a complete reference implementation.

## Need Help?

See the [main README](../README.md) for more details on the library API and deployment options.
