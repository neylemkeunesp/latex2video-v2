# LaTeX2Video in WSL2 Environment

This document provides information about running LaTeX2Video in a Windows Subsystem for Linux 2 (WSL2) environment, particularly focusing on GUI-related issues and workarounds.

## Issue: GUI Not Working in WSL2

When running the GUI version of LaTeX2Video in a WSL2 environment, you might encounter the following error:

```
[xcb] Unknown sequence number while appending request
[xcb] You called XInitThreads this is not your fault
[xcb] Aborting sorry about that.
python3: ../../src/xcb_io.c:157: append_pending_request: Assertion `!xcb_xlib_unknown_seq_number' failed.
Aborted (core dumped)
```

This is a known issue with Tkinter (Python's standard GUI toolkit) in WSL2 environments. The problem is related to how Tkinter interacts with the X11 server through XCB (X C Binding).

## Solutions

We've provided several alternative solutions to work around this issue:

### 1. Use the CLI Version (Recommended)

The command-line interface (CLI) version of LaTeX2Video works reliably in WSL2 environments. You can use it with the following command:

```bash
python3 run_cli.py assets/presentation.tex --save-scripts
```

For more information, see [README_CLI.md](README_CLI.md).

### 2. Use the Text-based User Interface (TUI)

We've created a text-based user interface that provides a menu-driven experience without requiring X11. To use it:

```bash
bash run_tui.sh
```

This script provides a simple menu-based interface for the CLI version that works in WSL2 environments without requiring X11.

### 3. Modified GUI Versions (Experimental)

We've also created modified versions of the GUI that attempt to work around the XCB issues:

- `run_gui_fixed.py`: A modified version of the GUI that tries to avoid the XCB threading issues.
- `run_gui_cli.py`: A simplified GUI that uses the CLI version under the hood.

However, these experimental versions may still encounter issues in some WSL2 environments.

## Setting Up X11 in WSL2

If you want to try using the GUI version in WSL2, you'll need to set up an X server on Windows:

1. Install an X server for Windows, such as:
   - [VcXsrv](https://sourceforge.net/projects/vcxsrv/)
   - [Xming](https://sourceforge.net/projects/xming/)
   - [X410](https://x410.dev/) (paid)

2. Configure the X server to:
   - Allow public access (disable access control)
   - Enable "Native OpenGL" (if available)
   - Enable "Disable access control" (if available)

3. Set the DISPLAY environment variable in WSL2:
   ```bash
   export DISPLAY=:0
   ```

4. You may also need to set additional environment variables:
   ```bash
   export LIBGL_ALWAYS_INDIRECT=1
   export QT_X11_NO_MITSHM=1
   ```

5. Try running the GUI again:
   ```bash
   python3 run_gui.py
   ```

## Troubleshooting

If you're still having issues with the GUI in WSL2:

1. Check if your X server is running on Windows
2. Verify that the DISPLAY environment variable is set correctly
3. Try running a simple X11 application like `xclock` or `xeyes` to test the X11 connection
4. Consider using the CLI version or the TUI script instead

## Additional Resources

- [WSL2 GUI Apps Documentation](https://docs.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)
- [X410 WSL2 Guide](https://x410.dev/cookbook/wsl/using-x410-with-wsl2/)
- [VcXsrv WSL2 Guide](https://sourceforge.net/p/vcxsrv/wiki/Using%20VcXsrv%20with%20WSL2/)
