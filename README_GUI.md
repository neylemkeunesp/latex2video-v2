# Running the LaTeX2Video GUI

This document explains how to run the GUI version of LaTeX2Video in different environments.

## Local Desktop Environment

If you're on a local desktop environment (Windows, macOS, Linux with a desktop), you can run the GUI directly:

```bash
python run.py
```

Or:

```bash
./run.py
```

## SSH with X11 Forwarding

If you're connecting via SSH, you need to enable X11 forwarding:

1. **On the client (your local machine):**
   
   Connect with X11 forwarding enabled:
   
   ```bash
   ssh -X username@server
   ```
   
   Or for more secure forwarding:
   
   ```bash
   ssh -Y username@server
   ```

2. **On the server:**
   
   Make sure you have the X11 packages installed:
   
   ```bash
   # For Debian/Ubuntu
   sudo apt-get install xauth
   
   # For CentOS/RHEL
   sudo yum install xorg-x11-xauth
   ```

3. **Run the GUI:**
   
   ```bash
   python run.py
   ```

## Docker Container

To run the GUI in a Docker container, you need to set up X11 forwarding:

```bash
docker run -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --volume="$HOME/.Xauthority:/root/.Xauthority:rw" \
  your-latex2video-image
```

Then inside the container:

```bash
python run.py
```

## Troubleshooting

If you see the error `_tkinter.TclError: couldn't connect to display "0.0"`, it means:

1. You don't have a display server available, or
2. X11 forwarding is not set up correctly

Solutions:

1. Use the command-line interface instead (see README_CLI.md)
2. Fix X11 forwarding by following the steps above
3. Use a VNC server on the remote machine

## Testing X11 Forwarding

To test if X11 forwarding is working, try running a simple X application:

```bash
xeyes
```

or

```bash
xclock
```

If these display correctly, X11 forwarding is working and you should be able to run the LaTeX2Video GUI.
