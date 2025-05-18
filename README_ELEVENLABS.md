# ElevenLabs Integration for LaTeX2Video

This document explains how to use the ElevenLabs Text-to-Speech (TTS) integration in the LaTeX2Video project.

## Requirements

- ElevenLabs API key (sign up at [elevenlabs.io](https://elevenlabs.io))
- elevenlabs Python package (version 1.57.0 or higher)

## Configuration

To use ElevenLabs for audio narration, edit the `config/config.yaml` file:

```yaml
# TTS configuration
tts:
  provider: "elevenlabs"  # Change from "gtts" to "elevenlabs"
  language: "pt"  # Still used for fallback to gTTS if needed
  slow: false

# ElevenLabs configuration
elevenlabs:
  api_key: "your_api_key_here"  # Replace with your actual API key
  voice_id: "4BGVHcW2xjlsh3CQ2d0i"  # Ney's voice ID (or use another voice ID)
  model_id: "eleven_multilingual_v2"  # Better for Portuguese
```

## Finding Voice IDs

To find available voice IDs in your ElevenLabs account, you can run the included test script:

```bash
python test_elevenlabs.py
```

This will list all available voices in your account along with their IDs. Choose the voice ID you prefer and update the `voice_id` field in your config.yaml file.

## Testing ElevenLabs Audio Generation

You can test the ElevenLabs audio generation with the provided test script:

```bash
python test_elevenlabs_audio.py
```

This will generate a test audio file in the `output/audio` directory using the ElevenLabs API.

## Troubleshooting

### API Key Issues

- Make sure your API key is valid and has sufficient credits
- Check that the API key is correctly entered in the config.yaml file

### Voice ID Issues

- If you get a "voice not found" error, run `test_elevenlabs.py` to get a list of valid voice IDs
- Update the `voice_id` in your config.yaml file with a valid ID from your account

### Package Version Issues

The LaTeX2Video project requires elevenlabs version 1.57.0 or higher. If you encounter import errors, make sure you have the correct version installed:

```bash
pip install elevenlabs>=1.57.0
```

### Fallback to gTTS

If ElevenLabs fails for any reason, the system will automatically fall back to using Google Text-to-Speech (gTTS). You'll see a warning message in the logs if this happens.
