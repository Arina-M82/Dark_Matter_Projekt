import arcade
import os
import cv2
from PIL import Image
import math
from arcade.gui import UIManager, UIFlatButton, UIMessageBox, UIAnchorLayout
import sys

from gallery.baze import GalleryView
from gallery.baze import db
db(9)
db(10)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 750
SCREEN_TITLE = "Кеплер: Дверь"  # Переименовал для ясности

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)


class Video_play(arcade.View):
    def __init__(self, name):
        super().__init__()
        self.cap = cv2.VideoCapture(get_asset_path(name))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0
        self.sound_kepler = arcade.load_sound(get_asset_path('sound_kepler.mp3'))
        self.sound_kepler.play()

    def on_update(self, delta_time):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            pil_image = Image.fromarray(frame_rgba)
            self.texture = arcade.Texture(pil_image, hit_box_algorithm=None)
            self.count += 1
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
        game_view = Kepler_game()
        self.window.show_view(game_view)


class Kepler_game(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("door.jpg"))


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
        # Добавляем в менеджер
        self.manager.add(self.close_button)
        self.setup()

    def setup(self):
        self.walk_timer = 0.0
        self.step_bob = 0.0
        self.view_scale = 1.0
        self.offset_x = 0
        self.move_speed = 900
        self.zoom_speed = 0.8
        self.keys = set()
        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.pinkod_list = arcade.SpriteList()
        self.pinkod = Pinkod(x=310, y=50)
        self.pinkod_list.append(self.pinkod)

    def on_update(self, delta_time):
        if arcade.key.W in self.keys or arcade.key.UP in self.keys:
            self.view_scale += self.zoom_speed * delta_time
        if arcade.key.S in self.keys or arcade.key.DOWN in self.keys:
            self.view_scale -= self.zoom_speed * delta_time

        if self.view_scale < 1.0:
            self.view_scale = 1.0
        if self.view_scale > 2.1:
            self.view_scale = 2.1

        if arcade.key.A in self.keys or arcade.key.LEFT in self.keys:
            self.offset_x += self.move_speed * delta_time
        if arcade.key.D in self.keys or arcade.key.RIGHT in self.keys:
            self.offset_x -= self.move_speed * delta_time
        max_limit = (SCREEN_WIDTH * self.view_scale - SCREEN_WIDTH) / 2

        if self.offset_x > max_limit:
            self.offset_x = max_limit
        if self.offset_x < -max_limit:
            self.offset_x = -max_limit

        if self.keys:
            self.walk_timer += delta_time * 18.0
            self.step_bob = abs(math.sin(self.walk_timer)) * 18.0
        else:
            self.step_bob = 0
            self.walk_timer = 0
        self.pinkod.sync_with_door(self.view_scale, self.offset_x)

        self.world_camera.position = (SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + self.step_bob)

    def on_key_press(self, key, modifiers):
        self.keys.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.keys:
            self.keys.remove(key)

    def on_draw(self):
        self.clear()
        self.world_camera.use()
        current_w = SCREEN_WIDTH * self.view_scale
        current_h = SCREEN_HEIGHT * self.view_scale
        draw_x = SCREEN_WIDTH // 2 + self.offset_x
        draw_y = SCREEN_HEIGHT // 2
        arcade.draw_texture_rect(rect=arcade.rect.XYWH(draw_x, draw_y, current_w, current_h), texture=self.texture)
        self.pinkod_list.draw()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        """Проверка клика"""
        a = self.world_camera.unproject((x, y))[:2]
        if self.pinkod.collides_with_point(a):
            game = GridGame()
            self.window.show_view(game)


class Pinkod(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(get_asset_path("Kod.png"), scale=1.0)
        self.x = x
        self.y = y
        self.base_scale = 0.1

    def sync_with_door(self, view_scale, offset_x):
        """Синхронизация позиции и размера с фоном корабля"""
        bg_center_x = SCREEN_WIDTH // 2 + offset_x
        bg_center_y = SCREEN_HEIGHT // 2
        self.center_x = bg_center_x + (self.x * view_scale)
        self.center_y = bg_center_y + (self.y * view_scale)
        self.scale = self.base_scale * view_scale


class GridGame(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager()


        self.cell_size = 35
        self.rows = 15
        self.cols = 15
        self.texture = None
        self.key = False
        self.flat_button = None
        self.message_box = None

        self.exemple = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 2, 1, 1, 1, 2, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 2, 1, 0, 0, 0, 1, 2, 0, 0, 0, 0],
            [0, 0, 2, 2, 1, 0, 0, 0, 0, 0, 1, 2, 2, 0, 0],
            [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2],
            [0, 0, 2, 2, 1, 0, 0, 0, 0, 0, 1, 2, 2, 0, 0],
            [0, 1, 0, 0, 2, 1, 0, 0, 0, 1, 2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 2, 1, 1, 1, 2, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        ]

        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        self.grid_width = self.cols * self.cell_size
        self.grid_height = self.rows * self.cell_size

        self.left_grid_offset_x = (SCREEN_WIDTH // 2 - self.grid_width) - self.cell_size
        self.right_grid_offset_x = (SCREEN_WIDTH // 2) + self.cell_size
        self.grid_offset_y = (SCREEN_HEIGHT // 2 - self.grid_height // 2)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_CYAN)

        self.ui_manager.enable()
        self.texture = arcade.load_texture(get_asset_path("pin.png"))
        self.key = False
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self._setup_ui_elements()

    def on_hide_view(self):
        self.ui_manager.disable()
        self.ui_manager.clear()  # Очищаем все виджеты из UIManager
        super().on_hide_view()

    def _setup_ui_elements(self):
        self.ui_manager.clear()  # Очищаем менеджер, чтобы гарантировать, что кнопка не дублируется

        style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(bg=(175, 77, 14), font_color=arcade.color.BLACK,
                                                      font_size=30),
            "hover": arcade.gui.UIFlatButton.UIStyle(bg=(242, 200, 146), font_color=arcade.color.BLACK,
                                                     font_size=30),
            "press": arcade.gui.UIFlatButton.UIStyle(bg=(103, 47, 10), font_color=arcade.color.WHITE, font_size=30),
        }
        self.flat_button = UIFlatButton(
            text="Ввод окончен.",
            x=self.window.width // 2 - 150,
            y=self.window.height - 100,
            width=300,
            height=75,
            style=style
        )
        self.ui_manager.add(self.flat_button)
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
            main_menu_view = GalleryView(self)
            self.window.show_view(main_menu_view)

        self.ui_manager.add(self.close_button)

        @self.flat_button.event("on_click")
        def on_click_button(event):
            self.button_was_clicked()

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))
        arcade.draw_rect_filled(arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
                                (0, 25, 51, 100))

        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size + self.cell_size // 2 + self.left_grid_offset_x
                y = row * self.cell_size + self.cell_size // 2 + self.grid_offset_y

                if self.grid[row][col] == 1:
                    color = arcade.color.BANANA_MANIA
                elif self.grid[row][col] == 2:
                    color = arcade.color.BURNT_ORANGE
                else:
                    color = arcade.color.BLACK
                arcade.draw_rect_filled(arcade.rect.XYWH(x, y,
                                                         self.cell_size - 2,
                                                         self.cell_size - 2),
                                        color)
                arcade.draw_rect_outline(arcade.rect.XYWH(x, y,
                                                          self.cell_size - 2,
                                                          self.cell_size - 2),
                                         arcade.color.BLACK, 1)

        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size + self.cell_size // 2 + self.right_grid_offset_x
                y = row * self.cell_size + self.cell_size // 2 + self.grid_offset_y

                if self.exemple[row][col] == 1:
                    color = arcade.color.BANANA_MANIA
                elif self.exemple[row][col] == 2:
                    color = arcade.color.BURNT_ORANGE
                else:
                    color = arcade.color.BLACK
                arcade.draw_rect_filled(arcade.rect.XYWH(x, y,
                                                         self.cell_size - 2,
                                                         self.cell_size - 2),
                                        color)
                arcade.draw_rect_outline(arcade.rect.XYWH(x, y,
                                                          self.cell_size - 2,
                                                          self.cell_size - 2),
                                         arcade.color.BLACK, 1)

        arcade.draw_text("ЛКМ - увеличить, ПКМ - уменьшить",
                         self.window.width // 2, 50, arcade.color.WHITE, 17,
                         anchor_x="center")

        self.ui_manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        col = int((x - self.left_grid_offset_x) // self.cell_size)
        row = int((y - self.grid_offset_y) // self.cell_size)

        if 0 <= row < self.rows and 0 <= col < self.cols:
            if button == arcade.MOUSE_BUTTON_LEFT:
                self.grid[row][col] = (self.grid[row][col] + 1) % 3
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                self.grid[row][col] = (self.grid[row][col] - 1 + 3) % 3

    def button_was_clicked(self):
        self.key = True
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] != self.exemple[i][j]:
                    self.key = False

        if self.key:
            self.show_win()
        else:
            self.show_over()

    def show_win(self):
        message_box = UIMessageBox(
            width=400,
            height=200,
            message_text="Личность подтверждена. Входите",
            buttons=["OK"]
        )
        message_box.on_action = self.on_message_button_win
        self.ui_manager.add(message_box)

    def show_over(self):
        message_box = UIMessageBox(
            width=400,
            height=200,
            message_text="Пароль неверный. Попробуйте еще раз.",
            buttons=["OK"]
        )
        message_box.on_action = self.on_message_button_over
        self.ui_manager.add(message_box)

    def on_message_button_win(self, event):
        video_view = Video_play_end(get_asset_path("Ворота.mp4"))
        self.window.show_view(video_view)

    def on_message_button_over(self, event):
        self.ui_manager.remove_widget(event.origin)
        self.key = False


class Video_play_end(arcade.View):
    def __init__(self, name):
        super().__init__()
        self.cap = cv2.VideoCapture(get_asset_path(name))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0

    def on_update(self, delta_time):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            pil_image = Image.fromarray(frame_rgba)
            self.texture = arcade.Texture(pil_image, hit_box_algorithm=None)
            self.count += 1
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

        # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: ЧТО ДАЛЬШЕ? ---
        # Здесь мы возвращаемся в главное меню.
        # Убедитесь, что 'menu.py' находится в корневой папке проекта.
        kepler_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.dirname(kepler_dir)

        if project_root_dir not in sys.path:
            sys.path.append(project_root_dir)

        from вентиляция.ventil import Video_play
        main_menu_view = Video_play('tyman.mp4')
        self.window.show_view(main_menu_view)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu = Video_play('intro.mp4')
    window.set_location(0, 50)
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()