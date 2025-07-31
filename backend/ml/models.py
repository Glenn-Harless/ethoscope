from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd


class BasePredictor(ABC):
    """Simple base class for ML predictors with versioning"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.is_trained = False
        self.version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.model_path = Path(f"models/{model_name}")
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.training_metrics = {}

    @abstractmethod
    def train(self, data: pd.DataFrame) -> dict[str, float]:
        """Train the model"""
        pass

    @abstractmethod
    def predict(self, data: pd.DataFrame) -> Any:
        """Make predictions"""
        pass

    def save(self):
        """Save model to disk with versioning"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")

        # Save model with version
        model_file = self.model_path / f"{self.model_name}_v{self.version}.pkl"
        joblib.dump(self.model, model_file)

        # Save metadata
        metadata = {
            "trained_at": datetime.utcnow().isoformat(),
            "model_name": self.model_name,
            "version": self.version,
            "training_metrics": self.training_metrics,
        }
        joblib.dump(metadata, self.model_path / "metadata.pkl")

        # Create symlink to latest model
        latest_link = self.model_path / f"{self.model_name}_latest.pkl"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(model_file.name)

    def load(self, version: Optional[str] = None):
        """Load model from disk"""
        if version:
            model_file = self.model_path / f"{self.model_name}_v{version}.pkl"
        else:
            model_file = self.model_path / f"{self.model_name}_latest.pkl"

        if not model_file.exists():
            raise FileNotFoundError(f"Model {self.model_name} not found")

        self.model = joblib.load(model_file)
        self.is_trained = True

        # Load metadata
        metadata_file = self.model_path / "metadata.pkl"
        if metadata_file.exists():
            metadata = joblib.load(metadata_file)
            self.version = metadata.get("version", "unknown")
            self.training_metrics = metadata.get("training_metrics", {})
