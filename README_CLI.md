# LaTeX2Video Command-Line Interface

This document explains how to use LaTeX2Video without a GUI, which is useful for:
- Headless servers
- SSH sessions without X11 forwarding
- Docker containers
- Any environment where you encounter the error: `_tkinter.TclError: couldn't connect to display "0.0"`

## Setup

1. Make sure you have completed the basic setup from the main README:
   - Install required Python packages: `pip install -r requirements.txt`
   - Install FFmpeg
   - Copy `config/config.yaml.template` to `config/config.yaml` and add your API keys

2. Ensure your `config.yaml` file has the necessary API keys:
   - OpenAI API key (required for script generation)
   - ElevenLabs API key (optional, only if using ElevenLabs for TTS)

## Using the Command-Line Interface

### Basic Usage

```bash
./run_cli.py assets/presentation.tex --save-scripts
```

Or using Python directly:

```bash
python run_cli.py assets/presentation.tex --save-scripts
```

### Command-Line Options

- `latex_file`: Path to your LaTeX presentation file (required)
- `-c, --config`: Path to your configuration file (default: `config/config.yaml`)
- `-s, --save-scripts`: Save the generated scripts to files (recommended)

### Examples

Using a custom configuration file:

```bash
./run_cli.py assets/presentation.tex -c my_custom_config.yaml --save-scripts
```

Using the module directly:

```bash
python -m src.automated_video_generation assets/presentation.tex --save-scripts
```

## Troubleshooting

If you encounter issues:

1. Check that your configuration file has valid API keys
2. Ensure FFmpeg is installed and accessible in your PATH
3. Verify that your LaTeX installation is working properly
4. Check the logs for specific error messages

## Notes

- The command-line interface uses the same core functionality as the GUI version
- All output files will be saved to the `output/` directory by default
- The final video will be saved to `output/final_video.mp4` by default
