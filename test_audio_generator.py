import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src import audio_generator

@pytest.fixture
def temp_output_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config(temp_output_dir):
    return {
        'output_dir': temp_output_dir,
        'tts': {'provider': 'mock'},
        'elevenlabs': {}
    }

def test_generate_all_audio_success(sample_config):
    narrations = ["Texto 1", "Texto 2", "Texto 3"]
    mock_provider = MagicMock()
    mock_provider.generate_audio.return_value = True

    with patch('src.audio_generator.create_tts_provider', return_value=mock_provider):
        audio_paths = audio_generator.generate_all_audio(narrations, sample_config)

    assert len(audio_paths) == 3
    for i, path in enumerate(audio_paths):
        assert path.endswith(f"audio_{i+1}.mp3")
        assert os.path.dirname(path) == os.path.abspath(os.path.join(sample_config['output_dir'], 'audio'))

def test_generate_all_audio_provider_init_fail(sample_config):
    narrations = ["Texto 1"]
    with patch('src.audio_generator.create_tts_provider', side_effect=Exception("Provider error")):
        audio_paths = audio_generator.generate_all_audio(narrations, sample_config)
    assert audio_paths == []

def test_generate_all_audio_generation_fail(sample_config):
    narrations = ["Texto 1", "Texto 2"]
    mock_provider = MagicMock()
    # First call succeeds, second fails
    mock_provider.generate_audio.side_effect = [True, False]

    with patch('src.audio_generator.create_tts_provider', return_value=mock_provider):
        audio_paths = audio_generator.generate_all_audio(narrations, sample_config)

    # Deve interromper e retornar lista vazia ao falhar
    assert audio_paths == []

def test_generate_all_audio_creates_audio_dir(sample_config):
    narrations = ["Texto único"]
    mock_provider = MagicMock()
    mock_provider.generate_audio.return_value = True

    audio_dir = os.path.join(sample_config['output_dir'], 'audio')
    if os.path.exists(audio_dir):
        shutil.rmtree(audio_dir)

    with patch('src.audio_generator.create_tts_provider', return_value=mock_provider):
        audio_paths = audio_generator.generate_all_audio(narrations, sample_config)

    assert os.path.exists(audio_dir)
    assert len(audio_paths) == 1

def test_generate_all_audio_empty_narrations(sample_config):
    narrations = []
    mock_provider = MagicMock()
    with patch('src.audio_generator.create_tts_provider', return_value=mock_provider):
        audio_paths = audio_generator.generate_all_audio(narrations, sample_config)
    assert audio_paths == []
