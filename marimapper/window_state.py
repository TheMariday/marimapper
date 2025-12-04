import json
import cv2
import platform
import subprocess
from pathlib import Path
from multiprocessing import get_logger

logger = get_logger()


def get_state_file():
    """Get the path to the window state configuration file."""
    config_dir = Path.home() / ".config" / "marimapper"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "window_state.json"


def load_window_state(window_name="MariMapper - Detector"):
    """Load saved window state for a given window name."""
    try:
        state_file = get_state_file()
        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)
                return state.get(window_name, {})
    except Exception as e:
        logger.debug(f"Failed to load window state: {e}")
    return {}


def save_window_state(window_name="MariMapper - Detector", x=None, y=None, width=None, height=None):
    """Save window state to configuration file."""
    try:
        state_file = get_state_file()
        state = {}
        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)

        window_state = {}
        if x is not None:
            window_state["x"] = x
        if y is not None:
            window_state["y"] = y
        if width is not None:
            window_state["width"] = width
        if height is not None:
            window_state["height"] = height

        if window_state:  # Only update if we have something to save
            state[window_name] = window_state
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Saved window state for {window_name}: {window_state}")
    except Exception as e:
        logger.debug(f"Failed to save window state: {e}")


def apply_window_state(window_name="MariMapper - Detector"):
    """Apply saved window state (position and size) to a window."""
    state = load_window_state(window_name)

    if not state:
        logger.debug(f"No saved state found for {window_name}")
        return False

    try:
        logger.debug(f"Attempting to apply window state: {state}")
        # Apply size first (if window was created with cv2.WINDOW_NORMAL)
        if "width" in state and "height" in state:
            logger.debug(f"Resizing window to {state['width']}x{state['height']}")
            cv2.resizeWindow(window_name, state["width"], state["height"])
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
    """Attempt to capture and save window state (position and size)."""
    try:
        # Try platform-specific method to get window position and size
        size_info = get_window_size_platform_specific(window_name)
        if size_info:
            x, y, w, h = size_info[0], size_info[1], size_info[2], size_info[3]
            save_window_state(window_name, x=x, y=y, width=w, height=h)
            return True

        # Fallback to OpenCV's image rect
        rect = cv2.getWindowImageRect(window_name)
        if rect and len(rect) >= 4:
            x, y, w, h = rect[0], rect[1], rect[2], rect[3]
            save_window_state(window_name, x=x, y=y, width=w, height=h)
            return True
    except Exception as e:
        logger.debug(f"Failed to capture window state: {e}")
    return False
