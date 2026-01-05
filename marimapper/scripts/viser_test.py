import itertools

import cv2
import trimesh.creation
import viser
from trimesh.transformations import quaternion_about_axis
from viser import SceneNodePointerEvent
from viser.theme import TitlebarButton, TitlebarImage, TitlebarConfig

from marimapper.led import LED3D, View
import numpy as np
import pickle

# from marimapper.sfm import sfm
#
# scan_path = Path("C:/Users/marti/PycharmProjects/marimapper/test/MariMapper-Test-Data/highbeam")
#
# existing_leds = get_all_2d_led_maps(scan_path)
#
# leds_3d = sfm(existing_leds)
#
# with open('highbeam.pickle', 'wb') as handle:
#     pickle.dump(leds_3d, handle, protocol=pickle.HIGHEST_PROTOCOL)

def get_all_views(leds: list[LED3D]) -> list[View]:
    views = []
    for led in leds:
        for view in led.views:
            if view.view_id not in [v.view_id for v in views]:
                views.append(view)

    return views

def deg_to_rad(v):
    return v*(np.pi/180.0)


class ObjectHandler:

    def __init__(self):
        self.server = viser.ViserServer()
        self.grid = self.server.scene.add_grid("floor", 10, 10)
        self.root = self.server.scene.add_transform_controls("/root")
        with open('highbeam.pickle', 'rb') as handle:
            self.leds_3d: [list[LED3D]] = pickle.load(handle)

        self.views = get_all_views(self.leds_3d)

        button_group = self.server.gui.add_button_group("controls",options="play pause continue".split(" "))

        self.progress = self.server.gui.add_progress_bar(0)

        self.progress_custom = self.server.gui.add_image(np.zeros((10,1000,3), dtype=np.uint8))

        self.server.gui.add_upload_button("upload")

        tab_group = self.server.gui.add_tab_group()

        with tab_group.add_tab("export", icon=viser.Icon.FILE_EXPORT):
            self.server.gui.add_button("export").on_click(self.export)


        with tab_group.add_tab("transform", icon=viser.Icon.ROTATE):
            self.root_reset = self.server.gui.add_button("reset")
            self.root_reset.on_click(self.reset_root)

        with tab_group.add_tab("video", icon=viser.Icon.DEVICE_COMPUTER_CAMERA):
            self.image = self.server.gui.add_image(np.zeros((480, 640, 3), np.uint8))
            self.fullscreen = self.server.gui.add_checkbox("fullscreen", False)

        self.map = None
        self.cams = []
        self.cam_labels = []

        self.update_map()

        self.theme()

    def theme(self):

        buttons = (
            TitlebarButton(
                text="Help",
                icon="Description",
                href="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            TitlebarButton(
                text="Github",
                icon="GitHub",
                href="https://github.com/nerfstudio-project/nerfstudio",
            ),
        )
        image = TitlebarImage(
            image_url_light="https://gcdnb.pbrd.co/images/egyusIRKgbWg.png?o=1",
            image_url_dark="https://gcdnb.pbrd.co/images/egyusIRKgbWg.png?o=1",
            image_alt="marimapper Logo",
            href="https://github.com/TheMariday/marimapper/",
        )
        titlebar_theme = TitlebarConfig(buttons=buttons, image=image)

        self.server.gui.configure_theme(
            titlebar_content=titlebar_theme,
            control_layout="floating",
            control_width="large",
            dark_mode=False,
            show_logo=True,
            show_share_button=True,
            brand_color=(0,255-101,255-26)
        )

    def select_camera(self, event_info):

        for cam in self.cams:
            if cam.name == event_info.target.name:
                with self.server.scene.add_3d_gui_container(cam.name + "dropdown", position=cam.position):
                    self.server.gui.add_button("close")
                pass

    def export(self,_=None):
        self.server.send_file_download("test_file.txt",b"bytes", save_immediately=True)

    def update_with_image(self, image):
        if self.fullscreen.value:
            self.server.scene.set_global_visibility(False)
            self.server.scene.set_background_image(self.image.image)
        else:
            self.server.scene.set_global_visibility(True)
            self.server.scene.set_background_image(None)

        self.image.image = image


    def reset_root(self, _):
        self.root.position = (0,0,0)
        self.root.wxyz = (1,0,0,0)

    def update_map(self,_=None):

        positions = np.zeros((len(self.leds_3d), 3), dtype=np.float32)
        for i, led in enumerate(self.leds_3d):
            a = quaternion_about_axis(0, led.point.normal)
            positions[i, :] = led.point.position

        sphere = trimesh.creation.icosphere(radius=0.02, subdivisions=1,face_colors=(0,255-101,255-26))

        if self.map:
            self.map.remove()
        self.map = self.server.scene.add_batched_meshes_trimesh(
            "/root/pc",
            sphere,
            batched_positions=positions,
            batched_wxyzs=np.array([(1.0,0.0,0.0,0.0) for _ in range(len(self.leds_3d))])
        )

        line_points = []
        for start, end in itertools.pairwise(positions):
            line_points.append([start, end])

        self.lines = self.server.scene.add_line_segments("/root/lines",
            points=line_points,colors=(128,128,128),line_width=3
        )

        self.map.on_click(self.led_click)

        for cam in self.cams:
            cam.remove()

        for label in self.cam_labels:
            label.remove()

        for view in get_all_views(self.leds_3d):
            self.cams.append(self.server.scene.add_camera_frustum(name=f"/root/camera_{view.view_id}", fov=1.5, aspect=1.0,
                                                  position=view.position, wxyz=view.rotation, color=(128, 128, 128),
                                                  variant="filled"))
            self.cam_labels.append(self.server.scene.add_label(name=f"/root/camera_label_{view.view_id}", text=f"camera_{view.view_id}",
                                   position=view.position))
        for cam in self.cams:
            cam.on_click(self.select_camera)

    def led_click(self,event:SceneNodePointerEvent):
        event.client.add_notification(
            f"Clicked on vertex {event.instance_index}",
            body="",
            auto_close=3000,
        )
def main():

    marimapper = ObjectHandler()
    device = cv2.VideoCapture(0)

    import random


    while True:

        ret_val, image = device.read()
        marimapper.update_with_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        marimapper.progress.value = random.randint(0,99)

        loading = np.zeros((100,1000,3),dtype=np.uint8)

        loading[:, :marimapper.progress.value*10] = (0,255-101,255-26)

        marimapper.progress_custom.image = loading




if __name__ == "__main__":
    main()