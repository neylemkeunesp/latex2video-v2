#!/bin/bash
# Example script demonstrating how to use LaTeX2Video CLI

# Make sure config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "Config file not found. Creating from template..."
    cp config/config.yaml.template config/config.yaml
    echo "Please edit config/config.yaml to add your API keys before continuing."
    exit 1
fi

# Check if presentation.tex exists
if [ ! -f "assets/presentation.tex" ]; then
    echo "Error: assets/presentation.tex not found."
    echo "Please provide a LaTeX presentation file."
    exit 1
fi

# Run the CLI version
echo "Running LaTeX2Video CLI with assets/presentation.tex..."
python run_cli.py assets/presentation.tex --save-scripts

# Check if the video was created
if [ -f "output/final_video.mp4" ]; then
    echo "Success! Video created at output/final_video.mp4"
    
    # Try to play the video if a player is available
    if command -v ffplay &> /dev/null; then
        echo "Playing video with ffplay..."
        ffplay -autoexit output/final_video.mp4
    elif command -v vlc &> /dev/null; then
        echo "Playing video with VLC..."
        vlc --play-and-exit output/final_video.mp4
    else
        echo "Video player not found. Please open output/final_video.mp4 manually."
    fi
else
    echo "Video generation may have failed. Check the logs for errors."
fi
