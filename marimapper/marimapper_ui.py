import logging
import os
import viser
import time
from sidebar import MarimapperSidebar
from marimapper import dummy_backend_ui
from marimapper.custom_ui_elements import notify
from marimapper.ui_style import Color, populate_theme
from marimapper.marimapper_backend import Marimapper
from marimapper.marimapper_backend import MMState
import marimapper.custom_ui_elements as viser_custom
import cv2
import numpy as np
from threading import Lock


import unicodedata
import re
def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


import json
class Project:
    def __init__(self,name:str):
        # These must all be pickleable
        self.name:str = name
        self.backend_option:str = "None"
        self.scan_from = 0
        self.scan_to = 10
        self.webcam_index = 0 # warning, if we load this and it doesn't work then we have an issue
        self.gap_fill_max = 3
        self.webcam_exposure = None

        self.scans = []

    def save(self):
        print("saving")
        json_data = json.dumps(self.__dict__, sort_keys=True, indent=4)
        with open(f"{self.name}.marimapper" , "w") as file:
            file.write(json_data)
        print("saved")

    def load(self, project_filename):
        try:
            with open(project_filename, "r") as file:
                self.__dict__ = json.load(file)
                return True
        except:
            return False



def list_projects(save_dir="."):

    projects_found = []
    for filename in os.listdir(save_dir):
        path = os.path.join(save_dir, filename)
        if os.path.isfile(path):
            if filename.endswith(".marimapper"):
                projects_found.append(filename.replace(".marimapper", ""))
    return projects_found

class MarimapperUI:

    def __init__(self):
        logging.info("Marimapper UI initialising")
        self.server = viser.ViserServer()
        self.reset_gui()
        self.loading_lock = Lock()

        self.last_project_save = None
        self.initialised = False

        self.sidebar:MarimapperSidebar|None = None
        self.server.on_client_connect(self.on_client_connect)
        self.marimapper: Marimapper | None = None
        logging.info("Marimapper UI initialised")


    def on_client_connect(self, client):
        if not self.initialised:
            logging.info("Marimapper UI new client connect whilst project is none")
            self.show_splash(client, welcome=True)
        else:
            logging.info("Marimapper UI new client connect")

    def reset_gui(self):
        logging.info("Marimapper UI resetting gui")
        self.server.gui.reset()
        populate_theme(self.server.gui)
        logging.info("Marimapper UI gui reset")

    def init_project(self, project):
        logging.info("Marimapper UI project initialising")

        if self.initialised:
            self.save_project()

        if self.marimapper is not None:
            self.marimapper.stop()
            self.marimapper = None

        if self.sidebar is not None:
            self.sidebar = None
            self.reset_gui()

        self.last_project_save = project
        self.sidebar = MarimapperSidebar(self.server.gui, project)
        self.sidebar.scan_start_button.on_click(self.start_scan)
        self.sidebar.scan_stop_button.on_click(self.stop_scan)
        self.sidebar.file_project_load_button.on_click(lambda event: self.show_splash(event.client, new_visible=False))
        self.sidebar.file_project_new_button.on_click(lambda event: self.new_project_modal(event.client))
        self.sidebar.backend_dropdown.on_update(self.load_backend)
        self.sidebar.webcam_number.on_update(self.change_webcam)
        self.sidebar.webcam_exposure.on_update(lambda _: self.marimapper.set_camera_exposure(self.sidebar.webcam_exposure.value))

        self.sidebar.webcam_threshold.on_update(lambda _: self.marimapper.set_threshold(self.sidebar.webcam_threshold.value))

        self.sidebar.webcam_test_led_index.on_update(lambda _: self.update_test_led())

        self.marimapper = Marimapper(self.sidebar.transition_callback, self.sidebar.webcam_callback)
        self.marimapper.set_camera_id(self.sidebar.webcam_number.value)
        self.sidebar.webcam_exposure.value = self.marimapper.get_camera_exposure()

        self.sidebar.webcam_test.on_click(lambda _:self.marimapper.toggle_test())

        # Needs to be done after marimapper due to callbacks in marimapper
        self.load_backend_from_name(self.sidebar.backend_dropdown.value)

        self.initialised = True

        self.save_project()

        logging.info("Marimapper UI project initialised")

    def update_test_led(self):
        self.sidebar.backend_ui.get_backend().set_led(self.sidebar.webcam_test_led_index.value, True)

    def load_project(self, project_name):
        logging.info("Marimapper UI loading project")
        project = Project(project_name)
        if not project.load(project_name+ ".marimapper"):
            logging.info("Marimapper UI failed to load project")
            return False

        self.init_project(project)

        logging.info("Marimapper UI loaded project")
        return True

    def save_project(self):
        if not self.initialised: return

        logging.info("Marimapper UI saving project")
        self.sidebar.update_project(self.last_project_save)
        self.last_project_save.save()

    def new_project_modal(self, client, parent_modal=None):
        logging.info("Marimapper UI launching new project modal")

        with client.gui.add_modal("Name your project") as text_modal:
            project_name_text = client.gui.add_text("project name", "")
            project_new_button = client.gui.add_button("New Project", disabled=True)
            project_close_button = client.gui.add_button("Close")

            project_close_button.on_click(lambda _: text_modal.close())

            @project_new_button.on_click
            def _(event):
                logging.info("Marimapper UI creating new project")
                with viser_custom.ProgressWrapper(project_name_text, project_new_button, project_close_button):
                    project_name = slugify(project_name_text.value)
                    if project_name == "":
                        notify(event.client, "cannot create new project with an empty name, how did you do that?")
                        return
                    ap = list_projects(".")
                    if project_name in ap:
                        notify(event.client, f"Project named {project_name} already exists.", notification=False, modal=True, color=Color.ERROR)
                        return

                    self.init_project(Project(project_name))
                    text_modal.close()
                    if parent_modal:
                        parent_modal.close()

            @project_name_text.on_update
            def _(event):
                if not event.client: return
                project_new_button.disabled = slugify(project_name_text.value) == ""

    def show_splash(self,client, welcome=False, new_visible=True):
        if client is None: return

        logging.info("Marimapper UI showing splash")

        with (client.gui.add_modal("welcome!" if welcome else "Save/Load") as splash_modal):
            if welcome:
                client.gui.add_image(cv2.imread("C:\\Users\\marti\\Downloads\\1395867442.akliasin_murr.png"))
            new_project_button = client.gui.add_button("New Project")
            new_project_button.on_click(lambda _: self.new_project_modal(client, splash_modal))
            new_project_button.visible = new_visible
            close_button = client.gui.add_button("close")
            close_button.on_click(lambda _: splash_modal.close())
            close_button.visible = self.initialised
            load_buttons = []

            def delete_project(project_name):
                os.remove(project_name + ".marimapper")
                for button in load_buttons:
                    if button.label == project_name:
                        button.visible = False
                        print("hiding", button.label)

            def load_previous_save(event):
                with viser_custom.ProgressWrapper(new_project_button, close_button):
                    project_name = event.target.label
                    match event.target.value:
                        case "Load":
                            if self.load_project(project_name):
                                splash_modal.close()
                            else:
                                notify(event.client, f"Failed to load {project_name}")
                        case "Delete":
                            viser_custom.get_confirmation(event.client, f"are you sure you want to delete {project_name}?", lambda: delete_project(project_name))
                        case _:
                            pass

            with client.gui.add_folder("Load previous project"):
                for project_name in list_projects("."):
                    if self.last_project_save and self.last_project_save.name == project_name:
                        continue

                    load_buttons.append(client.gui.add_button_group(project_name, ["Load", "Delete"]))
                    load_buttons[-1].on_click(load_previous_save)

    def start_scan(self, event):
        if not event.client:
            return

        def func():
            try:
                self.sidebar.scan_progress.reset()
                self.marimapper.do_scan(self.sidebar.scan_progress.set, range(self.sidebar.scan_led_from_number.value, self.sidebar.scan_led_to_number.value), self.sidebar.backend_ui.get_backend())
            except RuntimeError as e:
                viser_custom.notify(clients=event.client, message=e.__str__(), modal=True, notification=False, color=Color.ERROR)


        viser_custom.get_confirmation(client=event.client, message="Are you sure you want to start a scan?", yes_lambda=func)

    def stop_scan(self, event):
        if not event.client:
            return

        viser_custom.get_confirmation(client=event.client, message="Are you sure you want to stop the current scan?", yes_lambda=lambda: self.marimapper.stop_scan())

    def change_webcam(self, event):

        notify(event.client, "Warning! All captures in a project must be done with the same camera. Is this the camera you did the rest with?", color=Color.WARNING)

        with viser_custom.ProgressWrapper(self.sidebar.webcam_number):
            pass
            success = self.marimapper.set_camera_id(self.sidebar.webcam_number.value)
            if not success:
                viser_custom.notify(event.client, f"Failed to set webcam index to {self.sidebar.webcam_number.value}", color=Color.ERROR)
                self.sidebar.webcam_number.value = self.marimapper.camera.device_id

    def load_backend_from_name(self, name):
        with self.sidebar.backend_folder:

            match name:
                case "None":
                    import dummy_backend_ui
                    new_backend = dummy_backend_ui.BackendUI()
                    self.marimapper.backend_ready(False)
                    self.sidebar.backend_ui.remove()
                    self.sidebar.backend_ui = new_backend
                case "FCMega":
                    import fcmega_backend_ui
                    new_backend = fcmega_backend_ui.BackendUI(self.server.gui, self.marimapper.backend_ready)
                    self.marimapper.backend_ready(False)
                    self.sidebar.backend_ui.remove()
                    self.sidebar.backend_ui = new_backend
                case "PixelBlaze":
                    import pixelblaze_backend_ui
                    self.marimapper.backend_ready(False)
                    self.sidebar.backend_ui.remove()
                    self.sidebar.backend_ui = pixelblaze_backend_ui.BackendUI(self.server.gui,
                                                                              self.marimapper.backend_ready)
                case _:
                    pass

    def load_backend(self, event):
        if not event.client: return

        self.load_backend_from_name(self.sidebar.backend_dropdown.value)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    marimapper_ui = MarimapperUI()

    try:
        while True:
            time.sleep(60)
            marimapper_ui.save_project()
    except KeyboardInterrupt:
        print("shutting down")
    finally:
        marimapper_ui.save_project()

