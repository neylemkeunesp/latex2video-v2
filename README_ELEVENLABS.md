# Using ElevenLabs TTS with LaTeX2Video

This guide explains how to use ElevenLabs Text-to-Speech (TTS) with the LaTeX2Video project.

## Prerequisites

1. An ElevenLabs account with API access
2. Your ElevenLabs API key
3. A voice ID from your ElevenLabs account

## Configuration

1. Open the `config/config.yaml` file
2. Set the TTS provider to "elevenlabs":
   ```yaml
   tts:
     provider: "elevenlabs"
   ```
3. Configure your ElevenLabs settings:
   ```yaml
   elevenlabs:
     api_key: "your_api_key_here"
     voice_id: "your_voice_id_here"
     model_id: "eleven_multilingual_v2"  # Better for non-English languages
   ```

## Finding Your Voice ID

1. Log in to your ElevenLabs account
2. Go to the "Voice Library" section
3. Click on the voice you want to use
4. The voice ID is in the URL or in the voice details

## Testing ElevenLabs TTS

You can test the ElevenLabs TTS integration using the provided test scripts:

### Basic ElevenLabs Test

```bash
python test_elevenlabs_tts.py
```

This will generate a test audio file in the `output/elevenlabs_test` directory.

### LaTeX Parser with ElevenLabs Test

```bash
python test_latex_parser_with_tts.py
```

This will parse the LaTeX presentation and generate audio for the first 5 slides.

### LaTeX Parser with ElevenLabs and ChatGPT Formatting

```bash
python test_latex_parser_with_elevenlabs.py
```

This will parse the LaTeX presentation, format the slides for ChatGPT, and generate audio for the first 3 slides.

To process a specific slide:

```bash
python test_latex_parser_with_elevenlabs.py --slide 24
```

## Troubleshooting

### API Key Issues

If you see errors related to authentication, verify your API key is correct in the config file.

### Voice ID Issues

If you see errors related to the voice ID, make sure the voice ID exists in your ElevenLabs account.

### Model ID Issues

The default model is `eleven_multilingual_v2`, which works well for multiple languages. For English-only content, you can use `eleven_monolingual_v1` for potentially better results.

## Performance Considerations

ElevenLabs API calls may take longer than local TTS solutions like gTTS. The audio quality is significantly better, but processing time will be longer, especially for large presentations.

## Fallback to gTTS

If ElevenLabs is not available or encounters an error, the system will automatically fall back to gTTS if it's installed.
