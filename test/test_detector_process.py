import marimapper.camera
from marimapper.detector_process import DetectorProcess
import pytest
from mock_camera import MockCamera


# This is tricky because the capture sequence needs to include black scenes
# hmmmm
@pytest.mark.skip(reason="in progress")
def test_detector_process_basic(monkeypatch):

    monkeypatch.setattr(marimapper.camera.Camera, "Camera", MockCamera)

    device = "MariMapper-Test-Data/9_point_box/cam_0/capture_0000.png"
    detector_process = DetectorProcess(device, 1, 128, "dummy", "none", display=False)

    detector_process.start()

    detector_process.detect(0, 0)

    results = detector_process.get_results()

    assert results.point.u() == pytest.approx(0.4029418361244019)
    assert results.point.v() == pytest.approx(0.4029538809144072)


if __name__ == "__main__":
    test_detector_process_basic()
