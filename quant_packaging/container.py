"""Strategy container for loading and running serialized strategies."""

import dill
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, Optional


class StrategyContainer:
    """Container for loading and running serialized strategies.

    This class is designed to be used in production environments (e.g., Docker containers)
    to load and execute previously serialized strategies.

    Example:
        >>> container = StrategyContainer("./strategies/momentum_strategy")
        >>> signals = container.run(market_data)
    """

    def __init__(self, strategy_path: str):
        """Initialize the container with a strategy.

        Args:
            strategy_path: Path to the strategy directory or .pkl file
        """
        self.strategy_path = Path(strategy_path)
        self.strategy_func = None
        self.metadata = None
        self._load()

    def _load(self) -> None:
        """Load the strategy function and metadata."""
        # Handle both directory and direct .pkl file paths
        if self.strategy_path.is_dir():
            pkl_path = self.strategy_path / "strategy.pkl"
            metadata_path = self.strategy_path / "metadata.json"
        else:
            pkl_path = self.strategy_path
            metadata_path = self.strategy_path.parent / "metadata.json"

        if not pkl_path.exists():
            raise ValueError(f"Strategy file not found: {pkl_path}")

        # Load the strategy function
        with open(pkl_path, "rb") as f:
            self.strategy_func = dill.load(f)

        # Load metadata if available
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def run(self, data: pd.DataFrame) -> pd.Series:
        """Run the strategy on market data.

        Args:
            data: pandas DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            pandas Series with position signals (1.0=long, 0.0=flat, -1.0=short)

        Raises:
            ValueError: If the strategy hasn't been loaded or data is invalid
        """
        if self.strategy_func is None:
            raise ValueError("Strategy not loaded. Cannot run.")

        # Validate input data
        self._validate_data(data)

        # Run the strategy
        try:
            signals = self.strategy_func(data)
            return signals
        except Exception as e:
            raise RuntimeError(f"Error running strategy: {str(e)}") from e

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate that input data has the expected format.

        Args:
            data: DataFrame to validate

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError(f"Expected pandas DataFrame, got {type(data)}")

        if data.empty:
            raise ValueError("Input data is empty")

        # Check for common OHLCV columns (case-insensitive)
        columns_lower = [col.lower() for col in data.columns]
        required = ["close"]  # At minimum, we need close prices

        missing = [col for col in required if col not in columns_lower]
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"Available columns: {list(data.columns)}"
            )

    def get_info(self) -> Dict[str, Any]:
        """Get strategy metadata and information.

        Returns:
            Dictionary with strategy metadata
        """
        return {
            "metadata": self.metadata,
            "function_name": self.strategy_func.__name__ if self.strategy_func else None,
            "loaded": self.strategy_func is not None,
        }

    def __repr__(self) -> str:
        """String representation of the container."""
        name = self.metadata.get("name", "Unknown") if self.metadata else "Unknown"
        version = self.metadata.get("version", "Unknown") if self.metadata else "Unknown"
        return f"StrategyContainer(name='{name}', version='{version}')"
