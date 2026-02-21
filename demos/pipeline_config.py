"""Configuration for pipeline demo."""
from dataclasses import dataclass
from pathlib import Path
from eval.models import Language


@dataclass
class PipelineConfig:
    """Configuration for full pipeline demo."""
    language: Language
    sample_size: int = 100
    data_source: str = "ground_truth"  # ground_truth, wikipedia, news
    enable_ml: bool = True
    output_dir: Path = Path("demos/output")
    verbose: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.sample_size < 10:
            raise ValueError("sample_size must be >= 10 for meaningful demo")

        valid_sources = ["ground_truth", "wikipedia", "news"]
        if self.data_source not in valid_sources:
            raise ValueError(
                f"data_source must be one of {valid_sources}, got: {self.data_source}"
            )

    def summary(self) -> str:
        """Return human-readable summary of configuration."""
        return (
            f"Pipeline Config:\n"
            f"  Language: {self.language.value}\n"
            f"  Samples: {self.sample_size}\n"
            f"  Source: {self.data_source}\n"
            f"  ML Enabled: {self.enable_ml}\n"
            f"  Output: {self.output_dir}"
        )
