# Text-to-Speech (TTS) Options for LaTeX2Video

This document explains how to use the Text-to-Speech (TTS) functionality in the LaTeX2Video project.

## Available TTS Providers

The project now supports two TTS providers:

1. **gTTS (Google Text-to-Speech)**
   - Free to use
   - High-quality voice
   - Requires internet connection
   - Supports Portuguese (Brazil) natively
   - No API key required

2. **ElevenLabs** (original implementation)
   - Premium service
   - Very high-quality voice
   - Requires API key
   - Requires internet connection

## Configuration

To configure the TTS provider, edit the `config/config.yaml` file:

```yaml
# TTS configuration
tts:
  provider: "gtts"  # Options: "gtts" or "elevenlabs"
  language: "pt"    # Language code for gTTS (Portuguese)
  slow: false       # Whether to use slower speech rate for gTTS

# Keep ElevenLabs config for backward compatibility
elevenlabs:
  api_key: ""
  voice_id: "qt1bLo3nJpkn2qzf2CT2"  # Ney's voice ID from available voices
  model_id: "eleven_multilingual_v2"  # Better for Portuguese
```

### gTTS Configuration Options

- `provider`: Set to `"gtts"` to use Google Text-to-Speech
- `language`: Language code (default: `"pt"` for Portuguese)
- `slow`: Set to `true` for slower speech rate (default: `false`)

### ElevenLabs Configuration Options

- `provider`: Set to `"elevenlabs"` to use ElevenLabs
- `elevenlabs.api_key`: Your ElevenLabs API key
- `elevenlabs.voice_id`: Voice ID to use
- `elevenlabs.model_id`: Model ID to use (default: `"eleven_multilingual_v2"`)

## Installation

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

For ElevenLabs, you need version 1.57.0 or higher. See [README_ELEVENLABS.md](README_ELEVENLABS.md) for more details on the ElevenLabs integration.

## Testing gTTS

You can test the gTTS functionality using the provided test script:

```bash
python test_gtts.py
```

This will generate a sample audio file in the `output/audio` directory.

## Using TTS in the Project

The TTS functionality is integrated into the main workflow. When you run the project, it will automatically use the configured TTS provider to generate audio for the narrations.

```bash
python src/main.py
```

## Troubleshooting

### gTTS Issues

- If you encounter network-related errors, check your internet connection.
- If you get language-related errors, make sure you're using a valid language code.

### ElevenLabs Issues

- Make sure your API key is valid and has sufficient credits.
- Check that the voice ID exists in your ElevenLabs account.

## Language Support

gTTS supports many languages. For Portuguese, use the language code `"pt"`. For other languages, refer to the [gTTS documentation](https://gtts.readthedocs.io/en/latest/module.html#languages-gtts-lang).

Note: The language code `"pt-br"` was previously used but has been deprecated in newer versions of gTTS. The code `"pt"` is now used for Portuguese (including Brazilian Portuguese).
