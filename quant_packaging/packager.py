"""Strategy packaging and serialization."""

import dill
import json
import inspect
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime


class StrategyPackager:
    """Package and serialize quant trading strategies.

    This class handles the serialization of strategy functions and their metadata,
    making it easy to save strategies from Jupyter notebooks and deploy them later.

    Example:
        >>> def my_strategy(data):
        ...     # Calculate signals
        ...     return signals
        >>>
        >>> packager = StrategyPackager()
        >>> packager.save_strategy(
        ...     my_strategy,
        ...     name="momentum_strategy",
        ...     description="Simple momentum strategy",
        ...     requirements=["pandas", "numpy"]
        ... )
    """

    def __init__(self, output_dir: str = "./strategies"):
        """Initialize the packager.

        Args:
            output_dir: Directory where strategies will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_strategy(
        self,
        strategy_func: Callable,
        name: str,
        description: str = "",
        requirements: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
    ) -> Path:
        """Save a strategy function with its metadata.

        Args:
            strategy_func: The strategy function to serialize. Should accept a
                          pandas DataFrame with OHLCV data and return a Series
                          with position signals (1.0=long, 0.0=flat, -1.0=short)
            name: Name for the strategy (used for file naming)
            description: Human-readable description of the strategy
            requirements: List of Python package requirements (e.g., ["pandas>=1.5.0"])
            metadata: Additional metadata to store with the strategy
            version: Version string for the strategy

        Returns:
            Path to the created strategy directory
        """
        strategy_dir = self.output_dir / name
        strategy_dir.mkdir(parents=True, exist_ok=True)

        # Serialize the strategy function
        strategy_path = strategy_dir / "strategy.pkl"
        with open(strategy_path, "wb") as f:
            dill.dump(strategy_func, f)

        # Extract function source code for reference
        try:
            source_code = inspect.getsource(strategy_func)
        except (OSError, TypeError):
            source_code = "# Source code not available (likely defined in notebook)"

        # Create metadata
        strategy_metadata = {
            "name": name,
            "description": description,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "function_name": strategy_func.__name__,
            "source_code": source_code,
            "requirements": requirements or self._extract_requirements(strategy_func),
            "custom_metadata": metadata or {},
        }

        # Save metadata
        metadata_path = strategy_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(strategy_metadata, f, indent=2)

        # Save requirements.txt
        requirements_path = strategy_dir / "requirements.txt"
        with open(requirements_path, "w") as f:
            base_requirements = [
                "pandas>=1.5.0",
                "numpy>=1.24.0",
                "dill>=0.3.7",
            ]
            all_requirements = base_requirements + (requirements or [])
            f.write("\n".join(all_requirements))

        print(f"✓ Strategy '{name}' saved to {strategy_dir}")
        print(f"  - Strategy file: {strategy_path}")
        print(f"  - Metadata: {metadata_path}")
        print(f"  - Requirements: {requirements_path}")

        return strategy_dir

    def _extract_requirements(self, func: Callable) -> List[str]:
        """Attempt to extract requirements from function source code.

        This is a simple heuristic that looks for common import statements.
        """
        requirements = []
        try:
            source = inspect.getsource(func)
            # Look for common imports
            if "pandas" in source or "pd." in source:
                requirements.append("pandas")
            if "numpy" in source or "np." in source:
                requirements.append("numpy")
            if "sklearn" in source:
                requirements.append("scikit-learn")
            if "ta" in source or "talib" in source:
                requirements.append("ta")
        except (OSError, TypeError):
            pass

        return requirements

    def load_strategy(self, name: str) -> tuple[Callable, Dict[str, Any]]:
        """Load a previously saved strategy.

        Args:
            name: Name of the strategy to load

        Returns:
            Tuple of (strategy_function, metadata_dict)
        """
        strategy_dir = self.output_dir / name

        if not strategy_dir.exists():
            raise ValueError(f"Strategy '{name}' not found in {self.output_dir}")

        # Load the strategy function
        strategy_path = strategy_dir / "strategy.pkl"
        with open(strategy_path, "rb") as f:
            strategy_func = dill.load(f)

        # Load metadata
        metadata_path = strategy_dir / "metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        return strategy_func, metadata

    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all saved strategies.

        Returns:
            List of metadata dictionaries for all saved strategies
        """
        strategies = []

        for strategy_dir in self.output_dir.iterdir():
            if strategy_dir.is_dir():
                metadata_path = strategy_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        strategies.append(metadata)

        return strategies
