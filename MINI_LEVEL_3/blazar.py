import arcade
import arcade.gui
from random import randrange, randint
from gallery.baze import GalleryView
from gallery.baze import db
db(7)
db(8)

import os
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 750
SCREEN_TITLE = "Внутри корабля"
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)

class Intro_blasar(arcade.View):
    def __init__(self):
        super().__init__()
        db(7)
        db(8)
        self.texture = arcade.load_texture(get_asset_path("blazar.jpg"))

        self.ship_list = arcade.SpriteList()
        self.ship = arcade.Sprite(get_asset_path("ship.png"), scale=0.6)
        self.ship.center_x = 800
        self.ship.center_y = 0
        self.speed = 90
        self.ship_list.append(self.ship)

        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.world_camera.position = (self.ship.center_x, SCREEN_HEIGHT // 2)
        self.timer = 0.0
        self.wait_time = 18

        self.sound_blue_star = arcade.load_sound(get_asset_path('sound_blazar.mp3'))
        self.sound_blue_star.play()

    def on_update(self, delta_time):
        self.timer += delta_time
        self.ship.center_y += (delta_time * self.speed)
        cam_x = 800
        cam_y = self.ship.center_y
        if cam_y < SCREEN_HEIGHT // 2:
            cam_y = SCREEN_HEIGHT // 2
        elif cam_y > 2396 - SCREEN_HEIGHT // 2:
            cam_y = 2396 - SCREEN_HEIGHT // 2
        if self.ship.center_y > 1100:
            cam_y = 1100
        self.world_camera.position = (cam_x, cam_y)
        if self.timer >= self.wait_time:
            game_view = Game_blasar()
            self.window.show_view(game_view)

    def on_draw(self):
        self.clear()
        with self.world_camera.activate():
            arcade.draw_texture_rect(
                rect=arcade.rect.XYWH(800, 742, 1600, 1484),
                texture=self.texture
            )
            self.ship_list.draw()


class Game_blasar(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("blazar.webp"))
        self.sound_print = arcade.load_sound(get_asset_path("print_car.mp3"))
        self.sound_flash = arcade.load_sound(get_asset_path('flash.mp3'))
        self.full_text = ("ВНИМАНИЕ: Зафиксирован выброс релятивистского джета блазара.\n"
                          "Уровень радиации превысил предел устойчивости защиты.\n"
                          "Срочно активируйте резервный генератор радиационной защиты.")
        self.baze_img = arcade.load_texture(get_asset_path("baze.jpg"))
        self.ship = arcade.Sprite(get_asset_path("ship.png"), scale=0.6)
        self.ship.center_x = 1300
        self.ship.center_y = 400
        self.ship_list = arcade.SpriteList()
        self.ship_list.append(self.ship)

        self.setup()

    def setup(self):
        self.game_flag = True
        self.win_flag = False
        self.over_flag = False
        self.health = 3
        self.moro_number = 0
        self.max_waves = 6

        self.game_timer = 0.0
        self.wave_timer = 0.0
        self.moro_lumina = False  # Идет ли сейчас ожидание нажатия кнопки
        self.button_clicked = False  # Нажал ли игрок кнопку в текущей волне

        self.text_flag = False
        self.new_text = ""
        self.text_index = 0
        self.gost = 0  # В начале экран прозрачный

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
        self.v_box = arcade.gui.UIBoxLayout()  # Контейнер для кнопки защиты
        self.manager.add(arcade.gui.UIAnchorLayout()).add(self.v_box)
        self.over_ui_flag = True
        self.win_ui_flag = True

    def wave_ui(self):
        self.moro_lumina = True
        self.button_clicked = False
        self.wave_timer = 0
        self.v_box.clear()

        style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.RED, font_color=arcade.color.BLACK, font_size=24),
            "hover": arcade.gui.UIFlatButton.UIStyle(bg=(254, 185, 188), font_color=arcade.color.BLACK, font_size=24),
            "press": arcade.gui.UIFlatButton.UIStyle(bg=(179, 0, 8), font_color=arcade.color.WHITE, font_size=24),
        }

        # Создаем кнопку защиты
        btn = arcade.gui.UIFlatButton(text="ЗАЩИТА", width=150, height=60, style=style)
        # Рандомное место (учитываем границы экрана)
        rand_x = randint(200, SCREEN_WIDTH - 200)
        rand_y = randint(100, SCREEN_HEIGHT - 200)
        # Размещаем кнопку через Anchor или просто меняем её позицию вручную
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(btn, anchor_x="left", anchor_y="bottom",
                   align_x=rand_x, align_y=rand_y)
        self.manager.clear()
        self.manager.add(anchor)

        @btn.event("on_click")
        def on_click_btn(event):
            self.button_clicked = True
            self.v_box.clear()
            self.manager.clear()

    def phantom(self):
        """Логика вспышки и проверки урона"""
        self.gost = 255  # Делаем экран полностью белым
        self.moro_number += 1
        if not self.button_clicked:
            self.health -= 1
        if self.health <= 0:
            self.over_flag = True
        elif self.moro_number >= self.max_waves and self.health > 0:
            self.win_flag = True

    def game_over(self):
        """Создает графический интерфейс для экрана проигрыша"""
        self.manager.clear()
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
            text="Поздравляю! Твои кости светятся в темноте.",
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
            arcade.exit()  # Это мягко остановит текущий arcade.run()
            self.window.close()
            from кеплер import kepler
            kepler.main()

        anchor.add(v_box, anchor_x="center", anchor_y="center")
        self.manager.add(anchor)

    def color(self, delta_time):
        speed = 100
        color = round(speed * delta_time)
        self.gost -= color
        if self.gost <= 0:
            self.gost = 0
            self.flag_sound = False

    def print_text(self, delta_time):
        """Метод для эффекта печатной машинки"""
        if self.text_index < len(self.full_text):
            self.new_text += self.full_text[self.text_index]
            self.text_index += 1
        else:
            arcade.unschedule(self.print_text)

    def draw_message(self):
        """Отрисовка окна сообщения"""
        # arcade.draw_rect_filled(arcade.rect.XYWH(800, 375, 1600, 750), (254, 222, 185, 90))
        arcade.draw_rect_filled(arcade.rect.XYWH(800, 640, 650, 140), (0, 0, 0, 150))
        arcade.draw_text("БАЗА", 500, 670, arcade.color.GREEN, 20, bold=True)
        arcade.draw_text(self.new_text, 850, 640, arcade.color.WHITE, 16,
                         width=700, multiline=True, anchor_x="center")
        arcade.draw_texture_rect(rect=arcade.rect.XYWH(420, 640, 140, 140), texture=self.baze_img)

    def on_update(self, delta_time):
        if self.win_flag and self.win_ui_flag:
            self.win_flag = True
            self.win_ui_flag = False
            self.game_win()
        elif self.over_flag and self.over_ui_flag:
            self.over_flag = True
            self.over_ui_flag = False
            self.game_over()
        self.game_timer += delta_time
        self.color(delta_time)
        if 1 <= self.game_timer and not self.text_flag:
            self.text_flag = True
            arcade.schedule(self.print_text, 0.05)
            self.sound_print.play()
        if self.text_index >= len(self.full_text) and self.health > 0 and self.moro_number < self.max_waves:
            if not self.moro_lumina and self.gost <= 0:
                self.wave_ui()

        if self.moro_lumina:
            self.wave_timer += delta_time
            if self.wave_timer >= 0.8:  # 2 секунды на нажатие
                self.moro_lumina = False
                self.manager.clear()
                self.phantom()
                self.sound_flash.play()

        if self.gost > 0:
            self.color(delta_time)
        if self.over_flag or self.win_flag:
            return

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(SCREEN_WIDTH // 2,
                                                                SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                                SCREEN_HEIGHT))
        arcade.draw_rect_filled(
            arcade.rect.XYWH(800, 375, 1600, 750),
            (255, 255, 255, self.gost))
        if self.text_flag:
            self.draw_message()
        self.ship_list.draw()
        if self.win_flag or self.over_flag:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(800, 375, 700, 500),
                (0, 0, 0, 180))
            arcade.draw_rect_outline(
                arcade.rect.XYWH(800, 375, 700, 500),
                arcade.color.WHITE, 1)
        self.manager.draw()
        # Жизни (сердечки или текст)
        arcade.draw_text(f"ЦЕЛОСТНОСТЬ КОРПУСА: {self.health}", 50, 50, arcade.color.RED, 20, bold=True)
        arcade.draw_text(f"ВОЛНА: {self.moro_number}", 50, 80, arcade.color.WHITE, 18)
        # Вспышка Блазара (рисуем ПОВЕРХ ВСЕГО)
        if self.gost > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
                (255, 255, 255, int(self.gost)))