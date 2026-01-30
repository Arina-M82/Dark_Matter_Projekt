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

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)

class Video_play(arcade.View):
    # Добавляем аргумент next_video_name, по умолчанию он равен None
    def __init__(self, name, next_video_name=None):
        super().__init__()
        db(1)
        self.name = name
        self.next_video_name = next_video_name

        self.cap = cv2.VideoCapture(get_asset_path(name))
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
            self.finish()

    def on_draw(self):
        self.clear()
        if self.texture:
            arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(SCREEN_WIDTH // 2,
                                                                    SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                                    SCREEN_HEIGHT))
    def finish(self):
        self.cap.release()
        if self.next_video_name:
            next_view = Video_play(self.next_video_name)
            self.window.show_view(next_view)
        else:
            first_video = End()
            self.window.show_view(first_video)


class End(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("picture.png"))
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        close_tex = arcade.load_texture(get_asset_path('gal.png'))
        close = arcade.load_texture(get_asset_path('pres.png'))
        self.close_button = (arcade.gui.UITextureButton(
            x=1450,
            y=662,
            width=80,
            height=80,
            texture=close_tex,
            texture_hovered=close))

        @self.close_button.event("on_click")
        def on_click_close(event):
            from gallery.baze import GalleryView
            main_menu_view = GalleryView(self)
            self.window.show_view(main_menu_view)

        self.manager.add(self.close_button)
        self.flag = True
        self.flags = False
        self.fla = True
        self.print_interval = 0.1
        self.sound = arcade.load_sound(get_asset_path("print_car.mp3"))
        self.text_index = 0
        self.new_text = ''

    def print_text(self, delta_time):
        self.text = ('Умоляю, заберите меня из этого ада, \nгде с небес льется раскаленное стекло! \n'
                     'Пожалуйста, помогите мне вернуться на \nмою родную планету, я не выживу \nздесь больше ни дня!')
        if self.text_index < len(self.text):
            self.new_text += self.text[self.text_index]
            self.text_index += 1
        else:
            arcade.unschedule(self.print_text)
            self.flags = True

    def on_update(self, delta_time):
        if self.flag:
            self.flag = False
            arcade.schedule(self.print_text, self.print_interval)
            self.sound.play()
            return

    def on_draw(self):
        self.clear()
        # Рисуем финальную картинку на весь экран
        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT)
                                 )
        arcade.draw_rect_filled(arcade.rect.XYWH(700, 640, 500, 200),
                                (0, 0, 0, 200), tilt_angle=0)
        arcade.draw_text(self.new_text, 700, 690,
                         arcade.color.WHITE, 20, bold=True, align="center", anchor_x="center", width=700, multiline=True)
        if self.flags and self.fla:
            win_btn_style = {
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.GREEN, font_color=arcade.color.BLACK,
                                                          font_size=30),
                "hover": arcade.gui.UIFlatButton.UIStyle(bg=(192, 254, 185), font_color=arcade.color.BLACK,
                                                         font_size=30),
                "press": arcade.gui.UIFlatButton.UIStyle(bg=(21, 179, 0), font_color=arcade.color.WHITE, font_size=30),
            }
            btn_forward = arcade.gui.UIFlatButton(x=670, y=200, text="ВПЕРЁД!", width=300, height=80, style=win_btn_style)
            self.manager.add(btn_forward)
            self.fla = False

            @btn_forward.event("on_click")
            def on_click_forward(event):
                from METEO.meteor import Video_play
                window = Video_play('intro_meteor.mp4')
                self.window.show_view(window)
        self.manager.draw()


