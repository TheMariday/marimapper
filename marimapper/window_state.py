import json
import cv2
import platform
import subprocess
import atexit
from pathlib import Path
from multiprocessing import get_logger

logger = get_logger()
_exit_handlers_registered = set()  # Track which windows have exit handlers


def get_config_dir():
    """Get the marimapper config directory."""
    config_dir = Path.home() / ".config" / "marimapper"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_state_file(window_name="MariMapper - Detector"):
    """Get the path to the window state file for a specific window (separate file per window)."""
    config_dir = get_config_dir()
    # Use window name to create unique filename, sanitize for filesystem
    safe_name = window_name.replace(" ", "_").replace("-", "_")
    return config_dir / f"window_state.{safe_name}.json"


def load_window_state(window_name="MariMapper - Detector"):
    """Load saved window state for a given window name."""
    try:
        state_file = get_state_file(window_name)
        if not state_file.exists():
            return {}

        with open(state_file, "r") as f:
            content = f.read()
            if not content.strip():  # Handle empty file
                return {}
            state = json.loads(content)
            return state
    except json.JSONDecodeError as e:
        logger.debug(f"Corrupted window state file {state_file}, starting fresh: {e}")
        return {}
    except Exception as e:
        logger.debug(f"Failed to load window state: {e}")
    return {}


def save_window_state(window_name="MariMapper - Detector", x=None, y=None, width=None, height=None):
    """Save window state to per-window file."""
    try:
        window_state = {}
        if x is not None:
            window_state["x"] = x
        if y is not None:
            window_state["y"] = y
        if width is not None:
            # Sanity check: don't save unreasonably small widths (min 400px)
            if width >= 400:
                window_state["width"] = width
            else:
                logger.debug(f"Rejecting width {width} (too small, min 400px)")
        if height is not None:
            # Sanity check: don't save unreasonably small heights (min 300px)
            if height >= 300:
                window_state["height"] = height
            else:
                logger.debug(f"Rejecting height {height} (too small, min 300px)")

        if window_state:  # Only update if we have something to save
            state_file = get_state_file(window_name)
            with open(state_file, "w") as f:
                json.dump(window_state, f, indent=2)
            logger.debug(f"Saved window state for {window_name}: {window_state}")
    except Exception as e:
        logger.debug(f"Failed to save window state: {e}")


def apply_window_state(window_name="MariMapper - Detector"):
    """Apply saved window state (position and size with sanity checks)."""
    state = load_window_state(window_name)

    if not state:
        logger.debug(f"No saved state found for {window_name}")
        return False

    try:
        logger.debug(f"Applying window state: {state}")
        # Apply size first (only for resizable windows created with cv2.WINDOW_NORMAL)
        if "width" in state and "height" in state:
            w, h = state["width"], state["height"]
            if w >= 400 and h >= 300:  # Sanity check
                logger.debug(f"Resizing window to {w}x{h}")
                cv2.resizeWindow(window_name, w, h)
        # Then apply position
        if "x" in state and "y" in state:
            logger.debug(f"Moving window to x={state['x']}, y={state['y']}")
            cv2.moveWindow(window_name, state["x"], state["y"])
        logger.debug(f"Successfully applied window state for {window_name}")
        return True
    except Exception as e:
        logger.debug(f"Failed to apply window state: {e}")
    return False


def get_window_size_macos_pyobjc(window_name="MariMapper - Detector"):
    """Get window size on macOS using PyObjC (fast, native method)."""
    try:
        import Quartz
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID

        # Get all on-screen windows
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

        for window in windows:
            # Check if window name contains "MariMapper"
            window_name_value = window.get("kCGWindowName", "")
            if "MariMapper" in window_name_value:
                bounds = window.get("kCGWindowBounds", {})
                logger.debug(f"Found MariMapper window, bounds object type: {type(bounds)}, value: {bounds}")
                if bounds:
                    # Objective-C NSDictionary uses subscript notation
                    try:
                        x = int(bounds["X"])
                        y = int(bounds["Y"])
                        w = int(bounds["Width"])
                        h = int(bounds["Height"])
                    except (KeyError, TypeError, ValueError) as e:
                        logger.debug(f"Failed to extract bounds: {e}")
                        continue

                    if w > 0 and h > 0:
                        logger.debug(f"Captured window size: x={x}, y={y}, w={w}, h={h}")
                        return x, y, w, h
    except ImportError:
        pass  # PyObjC not available
    except Exception as e:
        logger.debug(f"Failed with PyObjC method: {e}")

    return None


def get_window_size_macos(window_name="MariMapper - Detector"):
    """Get window size on macOS using fastest available method."""
    # Try PyObjC first (fastest, native)
    result = get_window_size_macos_pyobjc(window_name)
    if result:
        return result

    # Fall back to osascript (slower but always available)
    try:
        script = '''
tell application "System Events"
    try
        repeat with proc in (processes)
            set procName to name of proc
            if procName contains "python" then
                try
                    set windowList to every window of proc whose name contains "MariMapper"
                    if (count of windowList) > 0 then
                        set firstWindow to item 1 of windowList
                        set windowPos to position of firstWindow
                        set windowSize to size of firstWindow
                        return (item 1 of windowPos) & "," & (item 2 of windowPos) & "," & (item 1 of windowSize) & "," & (item 2 of windowSize)
                    end if
                end try
            end if
        end repeat
    end try
end tell
'''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 4:
                    return int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            except (ValueError, IndexError):
                pass
    except subprocess.TimeoutExpired:
        logger.debug("macOS window size query timed out, will use fallback")
    except Exception as e:
        logger.debug(f"Failed osascript method: {e}")

    return None


def get_window_size_linux(window_name="MariMapper - Detector"):
    """Get window size on Linux using xdotool."""
    try:
        # Search for window by name
        search_result = subprocess.run(
            ["xdotool", "search", "--name", window_name],
            capture_output=True,
            text=True,
            timeout=1
        )
        if search_result.returncode == 0 and search_result.stdout.strip():
            window_id = search_result.stdout.strip().split()[0]
            # Get window geometry
            geom_result = subprocess.run(
                ["xdotool", "getwindowgeometry", window_id],
                capture_output=True,
                text=True,
                timeout=1
            )
            if geom_result.returncode == 0:
                # Parse output like: Position: 0,0 (screen: 0)
                # Geometry: 1280x720
                lines = geom_result.stdout.strip().split("\n")
                x, y = 0, 0
                w, h = 0, 0
                for line in lines:
                    if "Position:" in line:
                        coords = line.split("Position:")[1].split("(")[0].strip().split(",")
                        x, y = int(coords[0]), int(coords[1])
                    elif "Geometry:" in line:
                        size = line.split("Geometry:")[1].strip().split("x")
                        w, h = int(size[0]), int(size[1])
                if w > 0 and h > 0:
                    return x, y, w, h
    except Exception as e:
        logger.debug(f"Failed to get Linux window size: {e}")
    return None


def get_window_size_platform_specific(window_name="MariMapper - Detector"):
    """Try to get actual window size using platform-specific methods."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return get_window_size_macos(window_name)
    elif system == "Linux":
        return get_window_size_linux(window_name)
    # Windows support could be added here with ctypes if needed

    return None


def capture_window_state(window_name="MariMapper - Detector"):
    """Attempt to capture and save window state (position and size with sanity checks)."""
    try:
        # Try platform-specific method to get full window bounds
        size_info = get_window_size_platform_specific(window_name)
        if size_info:
            x, y, w, h = size_info[0], size_info[1], size_info[2], size_info[3]
            logger.debug(f"Captured window bounds: x={x}, y={y}, w={w}, h={h}")
            # save_window_state will apply sanity checks
            save_window_state(window_name, x=x, y=y, width=w, height=h)
            return True

        # Fallback to OpenCV's image rect
        rect = cv2.getWindowImageRect(window_name)
        if rect and len(rect) >= 4:
            x, y, w, h = rect[0], rect[1], rect[2], rect[3]
            logger.debug(f"Captured window rect (OpenCV): x={x}, y={y}, w={w}, h={h}")
            # save_window_state will apply sanity checks
            save_window_state(window_name, x=x, y=y, width=w, height=h)
            return True
    except Exception as e:
        logger.debug(f"Failed to capture window state: {e}")
    return False


# ==============================================================================
# Public API for window state management
# ==============================================================================


def get_saved_dimensions(window_name: str) -> tuple:
    """
    Get saved window dimensions if available.

    Returns:
        (width, height) tuple if saved, else (None, None)
    """
    state = load_window_state(window_name)
    if "width" in state and "height" in state:
        return state["width"], state["height"]
    return None, None


def get_saved_position(window_name: str) -> tuple:
    """
    Get saved window position if available.

    Returns:
        (x, y) tuple if saved, else (None, None)
    """
    state = load_window_state(window_name)
    if "x" in state and "y" in state:
        return state["x"], state["y"]
    return None, None


def register_on_exit_capture(window_name: str):
    """
    Register an atexit handler to capture and save window state on program exit.
    Safe to call multiple times for the same window.
    """
    if window_name in _exit_handlers_registered:
        return  # Already registered

    def _save_on_exit():
        try:
            logger.debug(f"Capturing window state for {window_name} on exit...")
            capture_window_state(window_name)
        except Exception:
            pass  # Silently fail if we can't capture state

    atexit.register(_save_on_exit)
    _exit_handlers_registered.add(window_name)
    logger.debug(f"Registered exit handler for window: {window_name}")
