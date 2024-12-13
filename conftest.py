import pytest
import multiprocessing


# This test fixture is due to the fact that Linux uses Fork instead of Spawn as the default start method
# This, strangely, causes issues with open3d calculating the normals (???)
# See https://github.com/TheMariday/marimapper/issues/46
@pytest.fixture(scope="session", autouse=True)
def force_spawn():
    multiprocessing.set_start_method("spawn")
