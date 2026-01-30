import arcade
import cv2  # Используется для чтения видеофайлов и извлечения кадров
import os
import subprocess
import sys
import arcade.gui
from PIL import Image  # Используется для преобразования кадров OpenCV в текстуры Arcade
import math
from gallery.baze import GalleryView
from gallery.baze import db
db(11)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 750
SCREEN_TITLE = "Проигрывание видео в Arcade"


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)


class Video_play(arcade.View):
    def __init__(self, name):
        super().__init__()
        db(11)
        self.cap = cv2.VideoCapture(get_asset_path(name))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

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

    def on_draw(self):
        self.clear()
        if self.texture:
            arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(SCREEN_WIDTH // 2,
                                                                    SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                                    SCREEN_HEIGHT))
        self.manager.draw()

    def finish(self):
        self.cap.release()
        self.window.set_update_rate(1 / 60)
        self.window.show_view(Ventil_game(1.0))


class Ventil_game(arcade.View):
    def __init__(self, a):
        super().__init__()
        self.view_scale = a  # Текущее приближение (зум)
        self.texture = arcade.load_texture(get_asset_path("baze2.jpg"))

        close_tex = arcade.load_texture(get_asset_path('gal.png'))
        close = arcade.load_texture(get_asset_path('pres.png'))
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
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
        self.setup()

    def setup(self):
        self.walk_timer = 0.0  # Таймер для покачивания камеры
        self.step_bob = 0.0
        # 3. УПРАВЛЕНИЕ КАМЕРОЙ И ЗУМОМ
        self.view_scale = 1.0  # Текущее приближение (зум)
        self.offset_x = 0  # Сдвиг камеры влево/вправо
        self.move_speed = 900
        self.zoom_speed = 0.9
        self.keys = set()
        # 4. КАМЕРЫ И ЭФФЕКТЫ
        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        # 5. СПРАЙТЫ (Объекты в мире)
        self.ventil_list = arcade.SpriteList()
        self.ventil = Ventil(x=0, y=30)
        self.ventil_list.append(self.ventil)
        self.flag_animation = False

    def on_update(self, delta_time):
        if self.flag_animation:
            game_view = Move_game()
            self.window.show_view(game_view)
            return

        if arcade.key.W in self.keys or arcade.key.UP in self.keys:
            self.view_scale += self.zoom_speed * delta_time
        if arcade.key.S in self.keys or arcade.key.DOWN in self.keys:
            self.view_scale -= self.zoom_speed * delta_time

        if self.view_scale < 1.0:
            self.view_scale = 1.0
        if self.view_scale > 5:
            self.view_scale = 5

        if arcade.key.A in self.keys or arcade.key.LEFT in self.keys:
            self.offset_x += self.move_speed * delta_time  # Двигаем картинку вправо, чтобы видеть левую часть
        if arcade.key.D in self.keys or arcade.key.RIGHT in self.keys:
            self.offset_x -= self.move_speed * delta_time
        max_limit = (SCREEN_WIDTH * self.view_scale - SCREEN_WIDTH) / 2

        if self.offset_x > max_limit:
            self.offset_x = max_limit
        if self.offset_x < -max_limit:
            self.offset_x = -max_limit

        if self.keys:
            self.walk_timer += delta_time * 15.0
            self.step_bob = abs(math.sin(self.walk_timer)) * 15.0
        else:
            self.step_bob = 0
            self.walk_timer = 0
        self.ventil.sync_with_door(self.view_scale, self.offset_x)

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
        self.ventil_list.draw()
        if self.view_scale < 4:
            arcade.draw_text("Нужно подойти ближе к вентиляции!",
                             draw_x - self.offset_x, 700,
                             arcade.color.RED, 30, anchor_x="center", bold=True)
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        """Проверка клика"""
        a = self.world_camera.unproject((x, y))[:2]
        if self.ventil.collides_with_point(a):
            # Передаем: название папки, текстуру базы, текущий зум и оффсет
            if self.view_scale >= 4.0:
                # Запускаем анимацию и передаем СЕБЯ (self) как родителя
                view = Play_animation("kac.mkv", self)
                self.window.show_view(view)
                self.flag_animation = True


class Ventil(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(get_asset_path("ventil.png"), scale=1.0)
        self.x = x
        self.y = y
        self.base_scale = 0.12

    def sync_with_door(self, view_scale, offset_x):
        """Синхронизация позиции и размера с фоном корабля"""
        bg_center_x = SCREEN_WIDTH // 2 + offset_x
        bg_center_y = SCREEN_HEIGHT // 2
        self.center_x = bg_center_x + (self.x * view_scale)
        self.center_y = bg_center_y + (self.y * view_scale)
        self.scale = self.base_scale * view_scale


class Play_animation(arcade.View):
    """ Главный класс для проигрывания видео путем чтения кадров в реальном времени """

    def __init__(self, name, parent_view):
        super().__init__()
        self.name = get_asset_path(name)
        self.parent_view = parent_view
        self.crazy_maximum = 11
        self.setup(self.name)

    def setup(self, name):
        self.count = 0
        xz = ''
        vidos = name  # имя
        file = os.path.join(xz, vidos)
        self.cap = cv2.VideoCapture(file)
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_delay = 1.0 / self.video_fps  # Рассчитываем, сколько времени должен показываться каждый кад

        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def frame(self):
        ret, frame = self.cap.read()  # Читаем следующий кадр из видеопотока
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        pil_image = Image.fromarray(frame_rgb)
        self.texture = arcade.Texture(image=pil_image)
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(SCREEN_WIDTH // 2,
                                                                SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                                SCREEN_HEIGHT))

    def on_draw(self):
        self.clear()
        # 1. Сначала рисуем саму игру (фон и вентиль) на заднем плане
        self.parent_view.on_draw()
        # 2. Поверх рисуем кадр видео
        self.count += 1
        if self.count < self.crazy_maximum:
            self.frame()
        else:
            # Когда видео кончилось, возвращаемся в ТУ ЖЕ игру, не создавая новую
            self.cap.release()
            self.window.show_view(self.parent_view)


class Move_game(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("baze.png"))

        self.sprite_list = arcade.SpriteList()
        # Теперь храним не "факт перетаскивания", а "какой объект тащим"
        self.dragged_sprite = None
        self.video = False


        close_tex = arcade.load_texture(get_asset_path('gal.png'))
        close = arcade.load_texture(get_asset_path('pres.png'))
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
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
        self.setup()

    def setup(self):
        stone1 = arcade.Sprite(get_asset_path("Камень 1.png"), center_x=791, center_y=391, scale=0.15)
        self.sprite_list.append(stone1)

        stone2 = arcade.Sprite(get_asset_path("Камень 2.png"), center_x=731, center_y=493, scale=0.15)
        self.sprite_list.append(stone2)

        stone3 = arcade.Sprite(get_asset_path("Камень 3.png"), center_x=821, center_y=583, scale=0.15)
        self.sprite_list.append(stone3)

        stone4 = arcade.Sprite(get_asset_path("Камень 4.png"), center_x=880, center_y=431, scale=0.15)
        self.sprite_list.append(stone4)

        stone5 = arcade.Sprite(get_asset_path("Камень 5.png"), center_x=951, center_y=493, scale=0.15)
        self.sprite_list.append(stone5)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(
            rect=arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
            texture=self.texture
        )
        arcade.draw_text("Очисти вентиляцию!",
                         800, 700,
                         arcade.color.RED, 30, anchor_x="center", bold=True)
        self.sprite_list.draw()
        self.manager.draw()

    def on_update(self, delta_time):
        if self.video:
            return
        flag = True
        for c in self.sprite_list:
            if 652 < c.center_x < 1008 and 308 < c.center_y < 660:
                flag = False
        if flag:
            self.video = True
            view = Video_end(get_asset_path("Kac2.mp4"))
            self.window.show_view(view)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for sprite in self.sprite_list:
                if sprite.collides_with_point((x, y)):
                    self.dragged_sprite = sprite
                    break

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.dragged_sprite = None

    def on_mouse_motion(self, x, y, dx, dy):
        if self.dragged_sprite is not None:
            self.dragged_sprite.center_x = x
            self.dragged_sprite.center_y = y
            print(x, y)


class Video_end(arcade.View):
    def __init__(self, name):
        super().__init__()
        self.cap = cv2.VideoCapture(get_asset_path(name))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0

        self.new_text = ''
        self.text_index = 0

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
        view = End()
        self.window.show_view(view)


class End(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("Finaly.jpg"))
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
        self.print_interval = 0.1
        self.sound = arcade.load_sound(get_asset_path("sound1.mp3"))
        self.baze_img = arcade.load_texture(get_asset_path("baze.jpg"))
        self.text_index = 0
        self.new_text = ''
        self.manager.add(arcade.gui.UIAnchorLayout())
        self.flags = False

    def on_update(self, delta_time):
        if self.flag:
            self.flag = False
            arcade.schedule(self.print_text, self.print_interval)
            self.sound.play()
            return

    def print_text(self, delta_time):
        self.text = ('Вентиляция отчищена.\nПора двигаться дальше')
        if self.text_index < len(self.text):
            self.new_text += self.text[self.text_index]
            self.text_index += 1
        else:
            arcade.unschedule(self.print_text)
            arcade.schedule(self.game_win, 4.0)

    def game_win(self, delta_time):
        self.flags = True
        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout(space_between=30)

        arcade.draw_rect_filled(
            arcade.rect.XYWH(800, 375, 700, 500),
            (0, 0, 0, 180))
        title_label = arcade.gui.UILabel(
            text="ЛЕТИМ ДАЛЬШЕ",
            font_size=60,
            text_color=arcade.color.RED,
            bold=True
        )
        v_box.add(title_label)
        win_btn_style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.GREEN, font_color=arcade.color.BLACK,
                                                      font_size=30),
            "hover": arcade.gui.UIFlatButton.UIStyle(bg=(192, 254, 185), font_color=arcade.color.BLACK, font_size=30),
            "press": arcade.gui.UIFlatButton.UIStyle(bg=(21, 179, 0), font_color=arcade.color.WHITE, font_size=30),
        }
        btn_forward = arcade.gui.UIFlatButton(text="ВПЕРЁД!", width=300, height=80, style=win_btn_style)
        v_box.add(btn_forward)

        @btn_forward.event("on_click")
        def on_click_forward(event):
            view = Video_play_monster('intro_monster.mp4')
            self.window.show_view(view)

        anchor.add(v_box, anchor_x="center", anchor_y="center")
        self.manager.add(anchor)

    def on_draw(self):
        self.clear()
        # Рисуем финальную картинку на весь экран
        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT)
                                 )
        arcade.draw_rect_filled(arcade.rect.XYWH(815, 640, 400, 140),
                                (0, 0, 0, 200), tilt_angle=0)
        arcade.draw_text("База", 660, 670,
                         arcade.color.WHITE, 25, bold=True, align="center")
        arcade.draw_text(self.new_text, 1010, 630,
                         arcade.color.WHITE, 20, bold=True, align="left", anchor_x="center", width=700, multiline=True)
        arcade.draw_texture_rect(rect=arcade.rect.XYWH(560, 640, 140, 140), texture=self.baze_img)
        if self.flags:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(800, 375, 700, 500),
                (0, 0, 0, 180))
        self.manager.draw()


class Video_play_monster(arcade.View):
    def __init__(self, name):
        super().__init__()

        db(12)
        db(13)
        db(14)
        db(15)

        self.cap = cv2.VideoCapture(get_asset_path(name))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0
        self.sound_kepler = arcade.load_sound(get_asset_path('monster_sound.mp3'))
        self.sound_kepler.play()
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
        self.manager.draw()

    def finish(self):
        self.cap.release()
        arcade.schedule(self.over, 2.0)

    def over(self, delt):
        import subprocess
        import sys
        import os

        # 1. Сначала закрываем окно Arcade, чтобы освободить видеокарту
        self.window.close()

        # 2. Рассчитываем пути (БЕЗ ЭТОГО НЕ РАБОТАЕТ)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(current_dir)
        script_path = os.path.join(base_dir, 'виртуал', 'new.py')
        target_folder = os.path.dirname(script_path)

        # 3. Путь к интерпретатору Python из твоего venv
        python_exe = sys.executable

        if os.path.exists(script_path):
            # Запускаем Ursina как полностью независимый процесс
            # Мы используем stdout/stderr в DEVNULL, чтобы процесс не ждал родителя
            subprocess.Popen(
                [python_exe, script_path],
                cwd=target_folder,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # Для Windows
            )
            print("Процесс Ursina запущен.")
        else:
            print(f"ОШИБКА: Файл не найден: {script_path}")

        # 4. Завершаем Arcade полностью
        arcade.exit()
        sys.exit()