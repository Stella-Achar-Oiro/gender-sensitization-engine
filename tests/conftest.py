"""Shared pytest fixtures for all tests."""
import sys
import pytest
from pathlib import Path

# Add project root to Python path for test imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from eval.models import Language


@pytest.fixture
def sample_texts():
    """Sample texts for testing across languages."""
    return {
        Language.ENGLISH: "The chairman will lead the meeting.",
        Language.SWAHILI: "Mwalimu alisema yeye ni mwanamume.",
        Language.FRENCH: "Le président dirigera la réunion.",
        Language.KIKUYU: "Mũrutani aramenyithia atĩ nĩ mũrũme."
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_biased_texts():
    """Known biased texts for testing."""
    return [
        "The chairman will lead.",
        "The policeman arrested the suspect.",
        "The nurse said she would help."
    ]


@pytest.fixture
def sample_neutral_texts():
    """Known neutral texts (should not detect bias)."""
    return [
        "The table is wooden.",
        "It is raining today.",
        "Python is a programming language."
    ]
