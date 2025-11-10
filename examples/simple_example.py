"""
Simple example of packaging a quant strategy.

This script demonstrates the basic workflow without Jupyter.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Import the library
import sys
sys.path.insert(0, '..')
from quant_packaging import StrategyPackager, StrategyContainer, DockerBuilder


def create_sample_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2024-06-01', freq='D')
    n = len(dates)

    base_price = 100
    trend = np.linspace(0, 20, n)
    noise = np.random.randn(n) * 2
    close_prices = base_price + trend + noise

    data = pd.DataFrame({
        'open': close_prices + np.random.randn(n) * 0.5,
        'high': close_prices + np.abs(np.random.randn(n)) * 1.5,
        'low': close_prices - np.abs(np.random.randn(n)) * 1.5,
        'close': close_prices,
        'volume': np.random.randint(1000000, 5000000, n)
    }, index=dates)

    return data


def momentum_strategy(data):
    """
    Simple momentum strategy using 20-day moving average.

    Args:
        data: DataFrame with OHLCV columns

    Returns:
        Series with position signals (1.0=long, 0.0=flat, -1.0=short)
    """
    ma_20 = data['close'].rolling(window=20).mean()

    signals = pd.Series(0.0, index=data.index)
    signals[data['close'] > ma_20] = 1.0
    signals[data['close'] <= ma_20] = 0.0

    return signals


def main():
    """Main workflow demonstration."""
    print("=" * 60)
    print("Quant Strategy Packaging Demo")
    print("=" * 60)

    # Step 1: Create sample data
    print("\n[1/5] Creating sample market data...")
    data = create_sample_data()
    print(f"✓ Created {len(data)} days of OHLCV data")

    # Step 2: Test strategy
    print("\n[2/5] Testing strategy...")
    signals = momentum_strategy(data)
    print(f"✓ Generated {len(signals)} signals")
    print(f"  - Long positions: {(signals == 1.0).sum()}")
    print(f"  - Flat positions: {(signals == 0.0).sum()}")

    # Step 3: Package strategy
    print("\n[3/5] Packaging strategy...")
    packager = StrategyPackager(output_dir="./strategies")
    strategy_dir = packager.save_strategy(
        strategy_func=momentum_strategy,
        name="momentum_ma20",
        description="Momentum strategy using 20-day moving average",
        requirements=["pandas>=1.5.0", "numpy>=1.24.0"],
        version="1.0.0",
        metadata={
            "author": "Demo User",
            "strategy_type": "momentum",
            "timeframe": "daily"
        }
    )

    # Step 4: Test packaged strategy
    print("\n[4/5] Testing packaged strategy...")
    container = StrategyContainer(strategy_dir)
    test_signals = container.run(data)

    match = np.allclose(signals, test_signals, equal_nan=True)
    print(f"✓ Loaded and verified strategy: {'PASS' if match else 'FAIL'}")

    # Step 5: Build Docker deployment
    print("\n[5/5] Building Docker deployment...")
    builder = DockerBuilder(output_dir="./deployments")
    deployment_dir = builder.create_deployment(
        strategy_name="momentum_ma20",
        strategy_dir=str(strategy_dir),
        port=8000
    )

    print("\n" + "=" * 60)
    print("All steps completed successfully!")
    print("=" * 60)
    print(f"\nTo deploy:")
    print(f"  cd {deployment_dir}")
    print(f"  docker-compose up --build")
    print(f"\nThen access the API at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
