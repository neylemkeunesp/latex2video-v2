#!/usr/bin/env python3
"""
Example script demonstrating how to use LaTeX2Video CLI from Python
"""

import os
import sys
import subprocess
import shutil

def main():
    """Run the LaTeX2Video CLI with a sample presentation"""
    
    # Make sure config file exists
    if not os.path.isfile("config/config.yaml"):
        print("Config file not found. Creating from template...")
        shutil.copy("config/config.yaml.template", "config/config.yaml")
        print("Please edit config/config.yaml to add your API keys before continuing.")
        return 1
    
    # Check if presentation.tex exists
    if not os.path.isfile("assets/presentation.tex"):
        print("Error: assets/presentation.tex not found.")
        print("Please provide a LaTeX presentation file.")
        return 1
    
    # Run the CLI version
    print("Running LaTeX2Video CLI with assets/presentation.tex...")
    try:
        subprocess.run(["python", "run_cli.py", "assets/presentation.tex", "--save-scripts"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running LaTeX2Video CLI: {e}")
        return 1
    
    # Check if the video was created
    if os.path.isfile("output/final_video.mp4"):
        print("Success! Video created at output/final_video.mp4")
        
        # Try to play the video if a player is available
        video_players = {
            "ffplay": ["ffplay", "-autoexit", "output/final_video.mp4"],
            "vlc": ["vlc", "--play-and-exit", "output/final_video.mp4"],
            "mpv": ["mpv", "output/final_video.mp4"]
        }
        
        for player, command in video_players.items():
            if shutil.which(player):
                print(f"Playing video with {player}...")
                try:
                    subprocess.run(command)
                    break
                except Exception as e:
                    print(f"Error playing video with {player}: {e}")
        else:
            print("Video player not found. Please open output/final_video.mp4 manually.")
    else:
        print("Video generation may have failed. Check the logs for errors.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
