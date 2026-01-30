import arcade
import arcade.gui
import math
from random import randrange, randint
import os
from gallery.baze import GalleryView
from gallery.baze import db
db(6)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 750
SCREEN_TITLE = "Внутри корабля"
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20
BG_WIDTH = 1600
BG_HEIGHT = 2396

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)

class Intro_blue(arcade.View):
    def __init__(self):
        super().__init__()
        db(6)
        self.texture = arcade.load_texture(get_asset_path("Blue_star.png"))

        self.ship = arcade.Sprite(get_asset_path("ship.png"), scale=0.6)
        self.ship.center_x = 400
        self.ship.center_y = 0
        self.ship_list = arcade.SpriteList()
        self.ship_list.append(self.ship)

        self.star_x = 800
        self.star_y = 1798

        self.orbit_radius = 400
        self.speed = 230
        self.state = "APPROACH"
        self.orbit_angle = math.pi

        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        self.display_timer = 0.0
        self.wait_time = 15.0

        self.sound_blue_star = arcade.load_sound(get_asset_path('sound_blue_star.mp3'))
        self.sound_blue_star.play()

    def on_update(self, delta_time):
        self.display_timer += delta_time

        if self.state == "APPROACH":
            self.ship.center_y += self.speed * delta_time
            self.ship.angle = 0
            if self.ship.center_y >= self.star_y:
                self.state = "ORBIT"
                self.ship.center_y = self.star_y  # Фиксируем точку входа

        elif self.state == "ORBIT":
            # 2. ОБЛЕТ ПО ДУГЕ
            angular_speed = (self.speed / self.orbit_radius) * delta_time
            # Уменьшаем угол, чтобы лететь по часовой стрелке (вправо)
            self.orbit_angle -= angular_speed
            # Математика круга
            self.ship.center_x = self.star_x + math.cos(self.orbit_angle) * self.orbit_radius
            self.ship.center_y = self.star_y + math.sin(self.orbit_angle) * self.orbit_radius
            self.ship.angle = math.degrees(self.orbit_angle)

            if self.orbit_angle <= math.pi / 2:
                self.state = "EXIT"

        elif self.state == "EXIT":
            # 3. ВЫЛЕТ В БОКОВУЮ ГРАНИЦУ (направо)
            self.ship.center_x += self.speed * delta_time
            self.ship.angle = 90
        cam_x = 800
        cam_y = max(375, min(self.ship.center_y, BG_HEIGHT - 375))
        self.world_camera.position = (cam_x, cam_y)

        if self.ship.center_x > 1700 or self.display_timer >= self.wait_time:
            game_view = Game_Blue()
            self.window.show_view(game_view)

    def on_draw(self):
        self.clear()
        with self.world_camera.activate():
            arcade.draw_texture_rect(
                rect=arcade.rect.XYWH(800, 1198, 1600, 2396),
                texture=self.texture
            )
            self.ship_list.draw()

        with self.gui_camera.activate():
            arcade.draw_text("Загрузка систем корабля...", SCREEN_WIDTH // 2, 50,
                             arcade.color.WHITE, 20, anchor_x="center", bold=True)


class Game_Blue(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("baze_blue.png"))
        self.sound_print = arcade.load_sound(get_asset_path("print_car.mp3"))
        self.sound_generator = arcade.load_sound(get_asset_path("generator.wav"))
        self.full_text = ("Критический перегрев основных систем.\n"
                          "Температура ядра превысила допустимые значения.\n"
                          "Требуется ручная активация системы охлаждения корабля.")
        self.baze_img = arcade.load_texture(get_asset_path("baze.jpg"))
        self.setup()

    """Метод для (пере)запуска игры. Обнуляет всё состояние."""

    def setup(self):
        # 1. ОБЩЕЕ СОСТОЯНИЕ И ФЛАГИ (Логика игры)
        self.game_flag = True
        self.win_flag = False
        self.activated = False  # Активирована ли система охлаждения
        self.visible = False
        self.status = "СТАТУС: ВЫКЛ"
        # 2. ТАЙМЕРЫ И ПЕРЕМЕННЫЕ ДЛЯ ТЕКСТА
        self.game_timer = 0.0
        self.walk_timer = 0.0  # Таймер для покачивания камеры
        self.step_bob = 0.0  # Сама величина смещения камеры
        self.text_flag = False
        self.new_text = ""
        self.text_index = 0
        # 3. УПРАВЛЕНИЕ КАМЕРОЙ И ЗУМОМ
        self.view_scale = 1.0  # Текущее приближение (зум)
        self.offset_x = 0  # Сдвиг камеры влево/вправо
        self.move_speed = 900
        self.zoom_speed = 0.8
        self.keys = set()
        # 4. КАМЕРЫ И ЭФФЕКТЫ
        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,
            max_amplitude=3,
            acceleration_duration=100.0,
            shake_frequency=0.0,
        )
        self.camera_shake.start()
        # 5. СПРАЙТЫ (Объекты в мире)
        self.split_list = arcade.SpriteList()
        self.split = Split(x=250, y=-110)
        self.split_list.append(self.split)

        self.batery_list = arcade.SpriteList()
        self.batery = Battery(x=-250, y=-110)
        self.batery_list.append(self.batery)
        # 6. GUI
        # Пересоздаем менеджер, если он уже был
        if hasattr(self, "manager"):
            self.manager.disable()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

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
        self.ui_manager.add(self.close_button)
        # Подготовка коробок для меню
        self.ui_container = arcade.gui.UIAnchorLayout()
        self.v_box = arcade.gui.UIBoxLayout(space_between=15)
        self.ui_panel = self.v_box.with_padding(all=20)
        self.over_ui_flag = True
        self.win_ui_flag = True

    def ui(self, mode=None):
        """Включает или выключает меню. mode может быть 'split' или 'battery'"""
        self.visible = not self.visible

        if self.visible:
            self.v_box.clear()  # Очищаем старые элементы перед добавлением новых

            if mode == "split":
                # --- ЛОГИКА ДЛЯ ЩИТКА (Слайдер) ---
                title = arcade.gui.UILabel(text="СИСТЕМА ОХЛАЖДЕНИЯ", font_size=30, bold=True)
                self.v_box.add(title)

                if not self.activated:
                    self.ui_slider = arcade.gui.UISlider(value=0, min_value=0, max_value=100, width=300)
                    self.v_box.add(self.ui_slider)
                    self.v_box.add(
                        arcade.gui.UILabel(text="СТАТУС: ВЫКЛ", font_size=18, text_color=arcade.color.RED, bold=True))
                    self.status = "СТАТУС: ВЫКЛ"

                    @self.ui_slider.event("on_change")
                    def on_change(event):
                        if self.ui_slider.value >= 98:
                            self.activated = True
                            self.sound_generator.play()
                            # Закрываем и открываем заново, чтобы обновить экран на "Активировано"
                            self.ui()  # Закрыть
                            self.ui("split")  # Открыть обновленным
                else:
                    self.v_box.add(
                        arcade.gui.UILabel(text="СИСТЕМА АКТИВИРОВАНА", font_size=18, text_color=arcade.color.GREEN,
                                           bold=True))
                    self.v_box.add(
                        arcade.gui.UILabel(text="СТАТУС: ВКЛ", font_size=18, text_color=arcade.color.GREEN, bold=True))
                    self.status = "СТАТУС: ВКЛ"

            elif mode == "batery":
                # --- ЛОГИКА ДЛЯ БАТАРЕИ (Текст) ---
                title = arcade.gui.UILabel(text="СИСТЕМА ОТОПЛЕНИЯ", font_size=30, bold=True)
                self.v_box.add(title)
                self.v_box.add(
                    arcade.gui.UILabel(text="СИСТЕМА НЕ АКТИВИРОВАНА", font_size=18, text_color=arcade.color.ORANGE,
                                       bold=True))
                self.v_box.add(
                    arcade.gui.UILabel(text="СТАТУС: ВЫКЛ", font_size=18, text_color=arcade.color.RED, bold=True))
            # Общая кнопка закрытия
            style = {
                "normal": arcade.gui.UIFlatButton.UIStyle(
                    font_size=12,
                    font_color=arcade.color.WHITE,
                    bg=arcade.color.RED,  # Цвет кнопки в покое
                ),
                "hover": arcade.gui.UIFlatButton.UIStyle(
                    bg=(251, 90, 86),  # Цвет при наведении мыши
                ),
                "press": arcade.gui.UIFlatButton.UIStyle(
                    bg=arcade.color.DARK_RED,  # Цвет при нажатии
                ),
            }

            # Показываем панель
            self.ui_container.add(self.ui_panel, anchor_x="center", anchor_y="center")
            self.manager.add(self.ui_container)

            close_button = arcade.gui.UIFlatButton(text="ЗАКРЫТЬ", width=150, style=style)
            self.v_box.add(close_button)

            @close_button.event("on_click")
            def on_click_close(event):
                self.ui()
        else:
            # Скрываем панель
            self.ui_container.remove(self.ui_panel)
            self.manager.remove(self.ui_container)

    def print_text(self, delta_time):
        """Метод для эффекта печатной машинки"""
        if self.text_index < len(self.full_text):
            self.new_text += self.full_text[self.text_index]
            self.text_index += 1
        else:
            arcade.unschedule(self.print_text)

    def draw_message(self):
        """Отрисовка окна сообщения"""
        arcade.draw_rect_filled(arcade.rect.XYWH(800, 375, 1600, 750), (254, 222, 185, 90))
        arcade.draw_rect_filled(arcade.rect.XYWH(800, 640, 560, 140), (0, 0, 0, 150))
        arcade.draw_text("БАЗА", 550, 670, arcade.color.GREEN, 20, bold=True)
        arcade.draw_text(self.new_text, 900, 640, arcade.color.WHITE, 16,
                         width=700, multiline=True, anchor_x="center")
        arcade.draw_texture_rect(rect=arcade.rect.XYWH(470, 640, 140, 140), texture=self.baze_img)

    def game_over(self):
        """Создает графический интерфейс для экрана проигрыша"""
        self.manager.clear()  # Полностью очищаем старый интерфейс (слайдер и т.д.)

        # Контейнеры
        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout(space_between=20)
        title_label = arcade.gui.UILabel(
            text="GAME OVER",
            font_size=80,
            font_name="Kenney Future",
            text_color=arcade.color.RED,
            bold=True
        )
        v_box.add(title_label)
        descr_label = arcade.gui.UILabel(
            text="ВЫ ЗАЖАРИЛИСЬ",
            font_size=24,
            bold=True,
            text_color=arcade.color.RED
        )
        v_box.add(descr_label)
        restart_style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.GREEN, font_color=arcade.color.BLACK,
                                                      font_size=24),
            "hover": arcade.gui.UIFlatButton.UIStyle(bg=(192, 254, 185), font_color=arcade.color.BLACK, font_size=24),
            "press": arcade.gui.UIFlatButton.UIStyle(bg=(21, 179, 0), font_color=arcade.color.WHITE, font_size=24),
        }
        exit_style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.RED, font_color=arcade.color.BLACK, font_size=24),
            "hover": arcade.gui.UIFlatButton.UIStyle(bg=(254, 185, 188), font_color=arcade.color.BLACK, font_size=24),
            "press": arcade.gui.UIFlatButton.UIStyle(bg=(179, 0, 8), font_color=arcade.color.WHITE, font_size=24),
        }
        btn_restart = arcade.gui.UIFlatButton(text="RESTART", width=250, height=80, style=restart_style)
        v_box.add(btn_restart)
        btn_exit = arcade.gui.UIFlatButton(text="EXIT", width=250, height=80, style=exit_style)
        v_box.add(btn_exit)

        @btn_restart.event("on_click")
        def on_restart(event):
            self.setup()

        @btn_exit.event("on_click")
        def on_exit(event):
            arcade.exit()

        # Добавляем всё на экран
        anchor.add(v_box, anchor_x="center", anchor_y="center")
        self.manager.add(anchor)

    def game_win(self):
        self.manager.clear()
        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout(space_between=30)

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
            from MINI_LEVEL_3.blazar import Intro_blasar
            next_level_view = Intro_blasar()
            self.window.show_view(next_level_view)

        anchor.add(v_box, anchor_x="center", anchor_y="center")
        self.manager.add(anchor)

    def on_key_press(self, key, modifiers):
        self.keys.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.keys:
            self.keys.remove(key)

    def on_update(self, delta_time):
        self.game_timer += delta_time
        if self.status == "СТАТУС: ВЫКЛ" and self.game_timer > 25.0 and self.over_ui_flag:
            self.game_flag = False
            self.game_over()
            self.over_ui_flag = False
            return
        if self.game_timer > 30 and self.game_flag and self.win_ui_flag:
            self.win_flag = True
            self.win_ui_flag = False
            self.game_win()
        if 10.0 <= self.game_timer and not self.text_flag and self.status == "СТАТУС: ВЫКЛ":
            self.text_flag = True
            arcade.schedule(self.print_text, 0.05)
            self.sound_print.play()
        elif self.text_flag and self.status == "СТАТУС: ВКЛ":
            self.text_flag = False

        if arcade.key.W in self.keys or arcade.key.UP in self.keys:
            self.view_scale += self.zoom_speed * delta_time
        if arcade.key.S in self.keys or arcade.key.DOWN in self.keys:
            self.view_scale -= self.zoom_speed * delta_time

        if self.view_scale < 1.0:
            self.view_scale = 1.0
        if self.view_scale > 2.0:
            self.view_scale = 2.0
        if arcade.key.A in self.keys or arcade.key.LEFT in self.keys:
            self.offset_x += self.move_speed * delta_time  # Двигаем картинку вправо, чтобы видеть левую часть
        if arcade.key.D in self.keys or arcade.key.RIGHT in self.keys:
            self.offset_x -= self.move_speed * delta_time
        max_limit = (SCREEN_WIDTH * self.view_scale - SCREEN_WIDTH) / 2

        if self.offset_x > max_limit:
            self.offset_x = max_limit
        if self.offset_x < -max_limit:
            self.offset_x = -max_limit
        self.camera_shake.update(delta_time)
        if self.keys:
            self.walk_timer += delta_time * 18.0
            self.step_bob = abs(math.sin(self.walk_timer)) * 18.0
        else:
            self.step_bob = 0
            self.walk_timer = 0

        self.world_camera.position = (SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + self.step_bob)
        self.camera_shake.update(delta_time)
        self.split.sync_with_ship(self.view_scale, self.offset_x)
        self.batery.sync_with_ship(self.view_scale, self.offset_x)

    def on_draw(self):
        self.clear()
        self.camera_shake.update_camera()
        self.world_camera.use()
        current_w = SCREEN_WIDTH * self.view_scale
        current_h = SCREEN_HEIGHT * self.view_scale
        draw_x = SCREEN_WIDTH // 2 + self.offset_x
        draw_y = SCREEN_HEIGHT // 2
        arcade.draw_texture_rect(rect=arcade.rect.XYWH(draw_x, draw_y, current_w, current_h), texture=self.texture)
        self.camera_shake.readjust_camera()

        self.split_list.draw()
        self.batery_list.draw()
        if self.win_flag:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(800, 375, 700, 500),
                (0, 0, 0, 180))
            arcade.draw_rect_outline(
                arcade.rect.XYWH(800, 375, 700, 500),
                arcade.color.WHITE, 1)
        if self.text_flag:
            self.draw_message()
            # 2. Текст базы (GUI камера)
            self.gui_camera.use()
        if self.game_flag:
            if self.visible:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(800, 375, 450, 300),
                    (0, 0, 0, 180))
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(800, 375, 450, 300),
                    arcade.color.WHITE, 1)
        else:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(800, 375, 700, 500),
                (0, 0, 0, 180))
            arcade.draw_rect_outline(
                arcade.rect.XYWH(800, 375, 700, 500),
                arcade.color.WHITE, 1)
        self.manager.draw()
        self.ui_manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        """Проверка клика"""
        if self.visible:
            return
            # Если UI закрыт, проверяем клик по батарейке
        a = self.world_camera.unproject((x, y))[:2]
        if self.split.collides_with_point(a) and self.game_timer >= 10.0:
            self.ui("split")
        if self.batery.collides_with_point(a):
            self.ui("batery")


class Split(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(get_asset_path("split.png"), scale=1.0)
        self.x = x
        self.y = y
        self.base_scale = 0.7

    def sync_with_ship(self, view_scale, offset_x):
        """Синхронизация позиции и размера с фоном корабля"""
        bg_center_x = SCREEN_WIDTH // 2 + offset_x
        bg_center_y = SCREEN_HEIGHT // 2
        self.center_x = bg_center_x + (self.x * view_scale)
        self.center_y = bg_center_y + (self.y * view_scale)
        self.scale = self.base_scale * view_scale


class Battery(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(get_asset_path("batery.png"), scale=1.0)
        self.x = x
        self.y = y
        self.base_scale = 0.7

    def sync_with_ship(self, view_scale, offset_x):
        """Синхронизация позиции и размера с фоном корабля"""
        bg_center_x = SCREEN_WIDTH // 2 + offset_x
        bg_center_y = SCREEN_HEIGHT // 2
        self.center_x = bg_center_x + (self.x * view_scale)
        self.center_y = bg_center_y + (self.y * view_scale)
        self.scale = self.base_scale * view_scale



