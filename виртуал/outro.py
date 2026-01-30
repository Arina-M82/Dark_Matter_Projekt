import arcade
import os
import cv2
from PIL import Image
import math
from arcade.gui import UIManager, UIFlatButton, UIMessageBox, UIAnchorLayout
import sys

from gallery.baze import db
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 750
CELL_SIZE = 35
SCREEN_TITLE = ":)"
class Video_play(arcade.View):
    # Добавляем аргумент next_video_name, по умолчанию он равен None
    def __init__(self, name):
        super().__init__()
        db(1)
        self.name = name

        self.cap = cv2.VideoCapture(name)
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None

    def on_update(self, delta_time):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            pil_image = Image.fromarray(frame_rgba)
            self.texture = arcade.Texture(pil_image, hit_box_algorithm=None)
        else:
            arcade.schedule_once(self.close_app, 2.0)

    def close_app(self, delta_time):
        arcade.exit()

    def on_draw(self):
        self.clear()
        if self.texture:
            arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(SCREEN_WIDTH // 2,
                                                                    SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                                    SCREEN_HEIGHT))
    def finish(self):
        self.cap.release()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu = Video_play('outro.mp4')
    window.set_location(0, 50)
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()