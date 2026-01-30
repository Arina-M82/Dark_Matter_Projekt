import arcade
import arcade.gui
import math
from random import randrange, randint, choice, uniform
from arcade.particles import FadeParticle, Emitter, EmitBurst, EmitInterval, EmitMaintainCount
import cv2
import os
import sys
from PIL import Image
from gallery.baze import GalleryView
from gallery.baze import db

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 750
SCREEN_TITLE = "Уровень астероиды"
SPARK_TEX = [
    arcade.make_soft_circle_texture(8, arcade.color.PASTEL_YELLOW),
    arcade.make_soft_circle_texture(8, arcade.color.PEACH),
    arcade.make_soft_circle_texture(8, arcade.color.BABY_BLUE),
    arcade.make_soft_circle_texture(8, arcade.color.ELECTRIC_CRIMSON),
]

SMOKE_TEX = arcade.make_soft_circle_texture(20, arcade.color.LIGHT_GRAY, 255, 80)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)


def make_explosion(x, y, count=80):
    # Разовый взрыв с искрами во все стороны
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitBurst(count),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=choice(SPARK_TEX),
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 9.0),
            lifetime=uniform(0.5, 1.1),
            start_alpha=255, end_alpha=0,
            scale=uniform(0.35, 0.6),
            mutation_callback=gravity_drag,
        ),
    )


def make_smoke_puff(x, y):
    # Короткий «пых» дыма: медленно плывёт и распухает
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitBurst(12),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=SMOKE_TEX,
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 0.6),
            lifetime=uniform(1.5, 2.5),
            start_alpha=200, end_alpha=0,
            scale=uniform(0.6, 0.9),
            mutation_callback=smoke_mutator,
        ),
    )


def smoke_mutator(p):  # Дым раздувается и плавно исчезает
    p.scale_x *= 1.02
    p.scale_y *= 1.02
    p.alpha = max(0, p.alpha - 2)


def gravity_drag(p):  # Для искр: чуть вниз и затухание скорости
    p.change_y += -0.03
    p.change_x *= 0.92
    p.change_y *= 0.92


class Video_play(arcade.View):
    def __init__(self, name):
        super().__init__()
        db(2)
        db(3)
        db(4)
        self.cap = cv2.VideoCapture(get_asset_path(name))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.window.set_update_rate(1 / self.video_fps)
        self.window.set_vsync(False)
        self.texture = None
        self.crazy_maximum = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0
        self.sound_kepler = arcade.load_sound(get_asset_path('sound_meteor.mp3'))
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
        # Добавляем в менеджер
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
        game = MyGame()
        self.window.show_view(game)
        game.setup()


class Boom(arcade.Sprite):
    def __init__(self, center_x, center_y):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("boom.png"))

        self.center_x = center_x
        self.center_y = center_y
        self.scale = 0.2

        self.lifetime = 5.0
        self.timer = 0.0
        self.change_y = 0

    def update(self, delta_time):
        self.timer += delta_time
        self.center_y += self.change_y * delta_time
        if self.timer >= self.lifetime or self.top < 0:
            self.remove_from_sprite_lists()


class Meteor(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.damage = randint(1, 4)
        self.scale = 0.1 * self.damage
        self.texture = arcade.load_texture(get_asset_path("meteor.png"))
        self.center_x = randrange(30, 1550)
        self.center_y = SCREEN_HEIGHT
        self.change_x = 0  # По горизонтали не движется
        self.change_y = 0  # Движется только вверх
        self.angle = 90  # Поворачиваем спрайт пули вертикально
        self.speed = 800 - (160 * self.damage)

        # --- СОЗДАНИЕ ТЕКСТУРНОЙ КНОПКИ ---

    def update(self, delta_time, center_x, center_y):
        x_diff = center_x - self.center_x
        y_diff = center_y - self.center_y

        angle = math.atan2(y_diff, x_diff)

        # 2. Установка новых векторов скорости, масштабированных на self.speed
        self.change_x = math.cos(angle) * self.speed
        self.change_y = math.sin(angle) * self.speed
        self.angle = math.degrees(-angle)

        # 3. Применяем движение
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

        # Удаляем, если улетел далеко (ниже игрока или слишком далеко в стороны)
        if self.bottom < -100 or abs(self.center_x - center_x) > SCREEN_WIDTH / 2 + 100:
            self.remove_from_sprite_lists()


class Hero(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.scale = 0.5
        self.speed = 300

        self.texture = arcade.load_texture(get_asset_path("ship.png"))

        self.center_x = SCREEN_WIDTH // 2
        self.center_y = 90
        self.keys_pressed = set()

    def update(self, delta_time):
        dx, dy = 0, 0
        if arcade.key.LEFT in self.keys_pressed or arcade.key.A in self.keys_pressed:
            dx -= self.speed * delta_time
        if arcade.key.RIGHT in self.keys_pressed or arcade.key.D in self.keys_pressed:
            dx += self.speed * delta_time
        if arcade.key.UP in self.keys_pressed or arcade.key.W in self.keys_pressed:
            pass
        if arcade.key.DOWN in self.keys_pressed or arcade.key.S in self.keys_pressed:
            pass

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        self.center_x += dx
        self.center_y += dy
        self.center_x = max(20, min(SCREEN_WIDTH - 20, self.center_x))
        self.center_y = max(20, min(SCREEN_HEIGHT - 20, self.center_y))


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, k, speed=800, damage=10):
        super().__init__()
        self.texture = arcade.load_texture(get_asset_path("bulong.png"))
        self.center_x = start_x - (25 * k)
        self.center_y = start_y
        self.speed = speed
        self.damage = damage
        self.scale = 0.5

        # Рассчитываем направление
        self.change_x = 0  # По горизонтали не движется
        self.change_y = speed  # Движется только вверх
        self.angle = 90

    def update(self, delta_time):
        if self.bottom > SCREEN_HEIGHT:
            self.remove_from_sprite_lists()

        # Используем delta_time для плавного движения
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time


class MyGame(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_texture = arcade.load_texture(get_asset_path('back.webp'))
        self.shoot_interval, self.meteor_interval = 0.3, 2.0
        self.print_interval = 0.1
        self.sound = arcade.load_sound(get_asset_path("sound1.mp3"))
        self.baze_img = arcade.load_texture(get_asset_path("baze.jpg"))
        self.boom_sound = arcade.load_sound(get_asset_path('boom.mp3'))

    def setup(self):
        self.emitters = []
        self.player_list = arcade.SpriteList()
        self.hero = Hero()
        self.player_list.append(self.hero)
        self.bullet_list = arcade.SpriteList()
        self.meteor_list = arcade.SpriteList()
        self.shoot_timer, self.meteor_timer, self.game_timer = 0, 0, 0
        self.game_duration = 30
        self.boom_list = arcade.SpriteList()
        self.flag = True
        self.health = 3

        self.new_text = ''
        self.text_index = 0

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

    def game_win(self):
        '''
        arcade.draw_rect_filled(arcade.rect.XYWH(800, 375, 750, 500),
                                (0, 0, 0, 100), tilt_angle=0)
        arcade.draw_text(f"Вы выбрались из пояса", 465, 430,
                         arcade.color.RED, 50, bold=True, align="center")
        arcade.draw_text("астероидов!", 660, 360,
                         arcade.color.RED, 50, bold=True, align="center")
        arcade.draw_rect_filled(arcade.rect.XYWH(810, 250, 550, 90),
                                (25, 255, 25), tilt_angle=0)
        arcade.draw_text("Летим дальше!", 580, 230,
                         arcade.color.BLACK, 50, bold=True, align="center")
        arcade.draw_rect_filled(arcade.rect.XYWH(800, 680, 650, 100),
                                (0, 0, 0, 100), tilt_angle=0)
                '''
        arcade.draw_rect_filled(arcade.rect.XYWH(815, 640, 400, 140),
                                (0, 0, 0, 100), tilt_angle=0)
        arcade.draw_text("База", 660, 670,
                         arcade.color.WHITE, 25, bold=True, align="center")
        arcade.draw_text(self.new_text, 1010, 630,
                         arcade.color.WHITE, 20, bold=True, align="left", anchor_x="center", width=700, multiline=True)
        arcade.draw_texture_rect(rect=arcade.rect.XYWH(560, 640, 140, 140), texture=self.baze_img)
        arcade.draw_rect_filled(arcade.rect.XYWH(755, 500, 530, 50),
                                (25, 255, 25), tilt_angle=0)
        arcade.draw_text("ВПЕРЁД!", 700, 485,
                         arcade.color.BLACK, 25, bold=True, align="center")

    def game_over(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(800, 375, 750, 500),
                                (0, 0, 0, 100), tilt_angle=0)
        arcade.draw_text("GAME OVER", 460, 400,
                         arcade.color.RED, 100, bold=True, align="center")
        arcade.draw_rect_filled(arcade.rect.XYWH(600, 200, 250, 80),
                                (25, 255, 25), tilt_angle=0)
        arcade.draw_text("RESTART", 480, 180,
                         arcade.color.BLACK, 50, bold=True, align="center")
        arcade.draw_rect_filled(arcade.rect.XYWH(1000, 200, 250, 80),
                                (255, 0, 25), tilt_angle=0)
        arcade.draw_text("EXIT", 940, 180,
                         arcade.color.BLACK, 50, bold=True, align="center")

    def print_text(self, delta_time):
        self.text = ('Пояс астероидов отчищен.\nПора двигаться дальше')
        if self.text_index < len(self.text):
            self.new_text += self.text[self.text_index]
            self.text_index += 1
        else:
            arcade.unschedule(self.print_text)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background_texture, arcade.rect.XYWH(SCREEN_WIDTH // 2,
                                                                           SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                                           SCREEN_HEIGHT))
        self.player_list.draw()
        self.bullet_list.draw()
        self.meteor_list.draw()
        self.boom_list.draw()
        if not self.flag:
            if self.health > 0:
                self.game_win()
            else:
                self.game_over()
        if self.hero and self.health > 0:
            arcade.draw_text(f"Жизни: {self.health}", 10, SCREEN_HEIGHT - 30,
                             arcade.color.WHITE, 24, bold=True)
        for e in self.emitters:
            e.draw()
        self.manager.draw()

    def on_update(self, delta_time):
        if not self.flag:
            return

        emitters_copy = self.emitters.copy()  # Защищаемся от мутаций списка
        for e in emitters_copy:
            e.update(delta_time)
        for e in emitters_copy:
            if e.can_reap():  # Готов к уборке?
                self.emitters.remove(e)

        if self.game_timer >= self.game_duration and self.health > 0:
            for meteor in self.meteor_list:  # Быстро вниз
                meteor.center_y -= 600 * delta_time
                if meteor.top < 0:
                    meteor.remove_from_sprite_lists()
            for boom in self.boom_list:  # Быстро вниз
                boom.center_y -= 600 * delta_time
                if boom.top < 0:
                    boom.remove_from_sprite_lists()
            for bullet in self.bullet_list:  # Быстро вниз
                bullet.remove_from_sprite_lists()
            self.player_list.update(delta_time)
            if self.game_timer >= self.game_duration and len(self.meteor_list) == 0 and len(self.boom_list) == 0:
                self.flag = False
                arcade.schedule(self.print_text, self.print_interval)
                self.sound.play()
                return
        else:
            self.player_list.update(delta_time)
            self.bullet_list.update(delta_time)
            self.meteor_list.update(delta_time, self.hero.center_x, self.hero.center_y)
            self.boom_list.update(delta_time)

            self.shoot_timer += delta_time
            self.meteor_timer += delta_time
            self.game_timer += delta_time

            if self.shoot_timer >= self.shoot_interval:
                bullet1 = Bullet(self.hero.center_x, self.hero.top, -1)
                bullet2 = Bullet(self.hero.center_x, self.hero.top, 1)
                self.bullet_list.append(bullet1)
                self.bullet_list.append(bullet2)
                self.shoot_timer = 0
            if self.meteor_timer >= self.meteor_interval:
                meteor = Meteor()
                self.meteor_list.append(meteor)
                self.meteor_timer = 0

            # 2. Удаляем все столкнувшиеся метеоры
            for bulet in self.bullet_list:
                for meteor in self.meteor_list:
                    flag = arcade.check_for_collision(bulet, meteor)
                    if flag:
                        boom = Boom(meteor.center_x, meteor.center_y)
                        self.boom_list.append(boom)
                        self.boom_sound.play()
                        meteor.remove_from_sprite_lists()

            if self.hero and self.health > 0:  # Проверяем, что герой жив
                for meteor in self.meteor_list:
                    if arcade.check_for_collision(self.hero, meteor):
                        self.emitters.append(make_explosion(self.hero.center_x, self.hero.center_y))
                        self.emitters.append(make_smoke_puff(self.hero.center_x, self.hero.center_y))
                        damage_taken = meteor.damage
                        self.health -= damage_taken
                        meteor.remove_from_sprite_lists()
                        if self.health <= 0:
                            self.flag = False

    def on_key_press(self, key, modifiers):
        self.hero.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.hero.keys_pressed:
            self.hero.keys_pressed.remove(key)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.flag and self.health > 0: # Если режим победы
            # Проверка клика по кнопке "ВПЕРЕД"
            if 488 < x < 1020 and 477 < y < 525: # Координаты кнопки "Вперед!"
                # Импортируем Level2 здесь, чтобы избежать циклической зависимости на верхнем уровне
                from MINI_LEVEL_1.red_star import IntroView
                next_level_view = IntroView()
                self.window.show_view(next_level_view)
        elif not self.flag and self.health <= 0: # Если режим поражения
            if 475 < x < 723.5 and 160 < y < 241: # Координаты кнопки RESTART
                self.setup() # Перезапускаем уровень 1
            elif 873 < x < 1123.5 and 160 < y < 239: # Координаты кнопки EXIT
                self.window.close() # Закрываем окно
