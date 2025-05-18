# Running LaTeX2Video

This document explains how to run LaTeX2Video in different environments.

## Quick Start

LaTeX2Video can be run in two ways:

1. **GUI Mode** - For desktop environments with a display server
2. **CLI Mode** - For headless servers or environments without a display server

## GUI Mode

To run LaTeX2Video with the graphical user interface:

```bash
./run_gui.py
```

This will launch the GUI application if a display server is available. If not, it will provide helpful error messages and suggest using the CLI mode instead.

**Requirements for GUI Mode:**
- A display server (local desktop or X11 forwarding)
- Tkinter support in Python

For detailed instructions on setting up X11 forwarding or troubleshooting display issues, see [README_GUI.md](README_GUI.md).

## CLI Mode

To run LaTeX2Video from the command line without a GUI:

```bash
./run_cli.py assets/presentation.tex --save-scripts
```

This will process the LaTeX presentation and generate a video without requiring a display server.

**Options:**
- `latex_file`: Path to your LaTeX presentation file (required)
- `-c, --config`: Path to your configuration file (default: `config/config.yaml`)
- `-s, --save-scripts`: Save the generated scripts to files (recommended)

For detailed instructions on using the CLI mode, see [README_CLI.md](README_CLI.md).

## Example Scripts

We've provided example scripts to help you get started:

- `example_cli_usage.sh` - Bash script demonstrating CLI usage
- `example_cli_usage.py` - Python script demonstrating CLI usage

## Troubleshooting

If you encounter the error `_tkinter.TclError: couldn't connect to display "0.0"`:

1. This means you don't have a display server available or X11 forwarding is not set up correctly
2. Use the CLI mode instead: `./run_cli.py assets/presentation.tex --save-scripts`
3. Or set up X11 forwarding as described in [README_GUI.md](README_GUI.md)

## Configuration

Regardless of which mode you use, make sure to:

1. Copy `config/config.yaml.template` to `config/config.yaml`
2. Add your API keys to the config file
3. Install all dependencies: `pip install -r requirements.txt`
4. Install FFmpeg for video assembly
