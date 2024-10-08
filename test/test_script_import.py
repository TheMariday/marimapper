# This is an incredibly simple test to just make sure that the scripts are interpretable by python, nothing more
import pytest


def test_check_backend_cli():
    from marimapper.scripts.check_backend_cli import main

    with pytest.raises(SystemExit):
        main()  # This should fail gracefully without any arguments


def test_check_camera_cli():
    from marimapper.scripts.check_camera_cli import main

    with pytest.raises(SystemExit):
        main()  # this should fail if no cameras are available


def test_view_2d_map_cli():
    from marimapper.scripts.view_2d_map_cli import main

    with pytest.raises(SystemExit):
        main()  # This should fail gracefully without any arguments


def test_upload_to_pixelblaze_cli():
    from marimapper.scripts.upload_map_to_pixelblaze_cli import main

    with pytest.raises(SystemExit):
        main()  # This should fail gracefully without any arguments


# Do not test scanner_cli due to it calling system level sig-kill commands!
