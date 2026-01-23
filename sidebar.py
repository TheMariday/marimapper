import viser
import marimapper.custom_ui_elements as viser_custom
import numpy as np
from marimapper.dummy_backend_ui import BackendUI as dummy_backend_ui
import cv2

from MMState import MMState

class MarimapperSidebar:

    def __init__(self, gui: viser.GuiApi):

        self.project_name_text = gui.add_markdown("Unknown")

        self.tabs = gui.add_tab_group()

        with self.tabs.add_tab("Capture", icon=viser.Icon.DEVICE_COMPUTER_CAMERA):

            self.backend_folder = gui.add_folder("Backend")
            with self.backend_folder:
                self.backend_dropdown = gui.add_dropdown("Backend Type", ["None", "PixelBlaze", "FCMega"])
                self.led_driver_ui = dummy_backend_ui()
                self.led_driver_connect = gui.add_button("Connect")

            with gui.add_folder("Scan Control"):

                self.scan_start_button = gui.add_button("Start Scan")
                self.scan_stop_button = gui.add_button("Stop Scan", disabled=True)

                self.scan_led_from_number = gui.add_number("From", 0)

                self.scan_led_to_number = gui.add_number("To", 10)

                self.scan_progress = viser_custom.CustomProgress(gui, 0, 10)

            with gui.add_folder("Webcam"):
                self.webcam_number = gui.add_number("Webcam Index", 0, min=0, max=10)

                self.webcam_viewer = gui.add_image(np.zeros((480,640,3)), label="Webcam Viewer")

                self.webcam_exposure = gui.add_slider("Exposure", -11, 0, 1, 0)
                self.webcam_threshold = gui.add_slider("Threshold", 0, 255, 1, 128)
                self.webcam_test = gui.add_button("Test Backend")
                self.webcam_test_led_index = gui.add_number("Test LED ID", 0)


        with self.tabs.add_tab("Reconstruction", icon=viser.Icon.CIRCUIT_CHANGEOVER):

            with gui.add_folder("Statistics"):
                self.reconstruction_statistics = gui.add_markdown("some statistics here")

            with gui.add_folder("Post-processing"):
                self.reconstruction_processing_gap_fill_number = gui.add_number("Max gap fill", 3)


        with self.tabs.add_tab("File", icon=viser.Icon.FILE_DOWNLOAD):

            with gui.add_folder("Project"):
                self.file_project_load_button = gui.add_button("Load Project")
                self.file_project_new_button = gui.add_button("New Project")
                self.file_project_save_button = gui.add_button("Save Project")


        # callbacks
        self.scan_led_from_number.on_update(self.update_led_range_from)
        self.scan_led_to_number.on_update(self.update_led_range_to)

    def set_led_driver_ui(self, led_driver_ui):
        self.led_driver_ui = led_driver_ui


    def transition_callback(self, state:MMState):

        self.webcam_test.label          = "Done" if state.camera_testing else "Test"
        self.webcam_test.disabled       = state.scanning or not state.backend_connected
        self.webcam_threshold.disabled  = not state.camera_testing
        self.webcam_exposure.disabled   = not state.camera_testing
        self.webcam_test_led_index.disabled = not state.camera_testing


        self.scan_stop_button.disabled  = not state.scanning

        self.scan_start_button.disabled = not (state.backend_connected and not state.camera_testing)

        self.scan_led_from_number.disabled  = state.ready()
        self.scan_led_to_number.disabled    = state.ready()

        self.webcam_number.disabled         = state.scanning

        self.led_driver_ui.disabled(state.backend_connected)

        self.led_driver_connect.label = "Disconnect" if state.backend_connected else "Connect"


    def update_led_range_from(self,event):
        if event and not event.client:
            return

        self.scan_led_from_number.value = max(self.scan_led_from_number.value, 0)
        self.scan_led_to_number.value = max(self.scan_led_to_number.value, self.scan_led_from_number.value+1)
        self.scan_progress.set_range(self.scan_led_from_number.value, self.scan_led_to_number.value)

    def update_led_range_to(self,event):
        if event and not event.client:
            return

        self.scan_led_to_number.value = max(self.scan_led_to_number.value, 1)
        self.scan_led_from_number.value = min(self.scan_led_to_number.value-1, self.scan_led_from_number.value)
        self.scan_progress.set_range(self.scan_led_from_number.value, self.scan_led_to_number.value)

    def webcam_callback(self, image):
        self.webcam_viewer.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def from_json(self, json_data):

        try:
            self.project_name_text.content = json_data["name"]
        except KeyError:
            pass
        try:
            self.backend_dropdown.value = json_data["backend"]
        except KeyError:
            pass
        try:
            self.scan_led_from_number.value = json_data["scan_led_from"]
        except KeyError:
            pass
        try:
            self.scan_led_to_number.value = json_data["scan_led_to"]
        except KeyError:
            pass
        try:
            self.webcam_number.value = json_data["webcam_number"]
        except KeyError:
            pass
        try:
            self.reconstruction_processing_gap_fill_number.value = json_data["led_fill"]
        except KeyError:
            pass
        try:
            self.webcam_threshold.value = json_data["webcam_threshold"]
        except KeyError:
            pass

        try:
            self.webcam_exposure.value = json_data["webcam_exposure"]
        except KeyError:
            pass

        self.scan_progress.set_range(self.scan_led_from_number.value, self.scan_led_to_number.value)

    def to_json(self) -> dict:

        return {"name": self.project_name_text.content,
                "backend": self.backend_dropdown.value,
                "scan_led_from": self.scan_led_from_number.value,
                "scan_led_to": self.scan_led_to_number.value,
                "webcam_number": self.webcam_number.value,
                "webcam_threshold": self.webcam_threshold.value,
                "led_fill": self.reconstruction_processing_gap_fill_number.value
                }
