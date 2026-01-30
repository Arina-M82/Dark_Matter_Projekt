from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import shuffle
from ursina import Vec4
import subprocess
import sys
import os

app = Ursina()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
window.size = (1900, 950)
window.position = 10, 50
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)

class Horror(Entity):
    def __init__(self):
        super().__init__()

        try:
            self.level = Entity(model='level.glb')
        except:
            # Если не находит, тогда полный путь
            self.level = Entity(model=get_asset_path('level.glb'))
        self.doors = []
        self.notes = []
        self.lockers = []

        # Флаг активации квантового монстра (начинает ходить после door 1)
        self.monster_kvant_active = False

        self.a = [i for i in range(10)]
        shuffle(self.a)
        self.note_texts = {
            'wrote 1': 'Лабораторный журнал №402: Объект-01 подчиняется Квантовому эффекту наблюдателя. Пока за ним ведется мониторинг,'
                       'его частицы зафиксированы в одной точке. Но как только взгляд прекращается, волновая функция расширяется.'
                       'Он существует везде и нигде одновременно. Если вы его видите — не моргайте. Ваше внимание — это единственные цепи, '
                       f'которые его удерживают\n{self.a[0]}',
            'wrote 2': 'Медицинский отчет: «Лучевая болезнь прогрессирует у всех выживших. Пульсар — это космический маяк, '
                       'вращающаяся нейтронная звезда. Его ритм смертелен и точен. Гамма-лучи разрушают ДНК за долю секунды. '
                       'Свинецовые шкафы — единственный барьер, который эти лучи не могут преодолеть. '
                       f'Не игнорируйте cистему безопасности. Тень Пульсара не выбирает жертв, она просто выжигает всё живое на своем пути».\n{self.a[1]}',
            'wrote 3': 'Технический регламент: «При аварийном отключении реактора все системы переходят на резервные аккумуляторы. '
                       'Чтобы восстановить полное питание и разблокировать магнитные замки дверей, необходимо вручную '
                       'активировать термоядерный запал. Терминал управления находится в центральной рубке. Ищите ГОЛУБУЮ КНОПКУ. '
                       f'Вы должны нажать её\n{self.a[2]}',
            'wrote 4': 'Мы думали, что наука защитит нас. Но на расстоянии в 40 световых лет законы физики становятся нашими '
                       'врагами. Станция '"Прометей"' — это памятник человеческой гордыне. Мы построили её в месте, где '
                       'пространство и время ведут себя иначе. Мы здесь не исследователи. Мы — жертвы, принесенные в угоду '
                       f'великой пустоте. Прощайте\n{self.a[3]}'
        }

        configs = {'door': 'z', 'door 1': 'x', 'door 2': 'z', 'door 3': 'z', 'door 4': 'x'}
        for name, axis in configs.items():
            node = self.level.model.find(f'**/{name}')
            if node:
                d = Entity(model=node, collider='box', name=name)
                d.axis = axis
                d.is_open = False
                if name == 'door':
                    d.z += 4
                    d.is_open = True
                self.doors.append(d)

        for name in self.note_texts.keys():
            node = self.level.model.find(f'**/{name}')
            if node:
                n = Entity(model=node, collider='box', name=name)
                self.notes.append(n)

        for i in range(1, 6):
            name = f'locker {i}'
            node = self.level.model.find(f'**/{name}')
            if node:
                lock = Entity(model=node, collider='box', name=name)
                self.lockers.append(lock)

        model_button = self.level.model.find('**/button')
        self.button = Entity(model=model_button, collider='box', name='button')

        self.monster_path = [
            Vec3(3, -0.8, 8.5), Vec3(-0.35, -0.8, 8.65), Vec3(-0.05, -0.8, 0.59),
            Vec3(13.1, -0.8, 0.09), Vec3(30.86, 5.51, -0.33), Vec3(39.33, 5.61, -0.85),
            Vec3(38.85, 5.55, -11.61), Vec3(3, -0.8, 8.5)
        ]
        self.player = FirstPersonController(position=(2, 1, 8), scale=1.2)

        self.setup()

        invoke(self.close_first_door, delay=5)

    def close_first_door(self):
        Audio('monster_ level.mp3')
        for d in self.doors:
            if d.name == 'door' and d.is_open:
                self.move_door(d)

    def setup(self):
        self.flag_lose = True
        self.patrol_timer = 0
        self.is_patrolling = False
        self.monster_sound_played = False

        self.hint = Text(text="Нажмите 'E'", origin=(0, 0), y=-0.1, scale=1.5, color=color.black, enabled=False)
        self.hint.shadow = True
        self.hint.outline = 0.02

        # Начальные координаты (0, -1, 0)
        self.monster_kvant = Entity(model='scp.glb', position=(0, -1, 0), scale=0.3, collider='box')
        self.monster = Entity(position=(3, -0.8, 8.5), collider='box', enabled=False)
        self.monster_model = Entity(parent=self.monster, model='monsterr.glb', rotation_y=90)
        self.monster_kvant.shader = 'lit_with_shadows_shader'

        # Игрок
        self.player.gravity = 1
        self.player.cursor.visible = False

        # UI
        self.coord_debug = Text(text='', position=window.top_left, scale=1.5, color=color.yellow)
        self.hide_overlay = Entity(parent=camera.ui, model='quad', texture='lock.png', scale=(window.aspect_ratio, 1),
                                   enabled=False, z=-1)
        self.is_hiding = False
        self.is_door_locked = True
        self.note_panel = Entity(parent=camera.ui, model='quad', scale=(1.2, 0.8), color=color.rgba(255, 255, 255, 0.8),
                                 enabled=False, z=-0.1)
        self.note_display = Text(parent=self.note_panel, text='', origin=(0, 0), scale=1.8, color=color.black, z=-0.1)
        self.code_input = InputField(enabled=False, placeholder='Код...', y=0)

        self.level.collider = 'mesh'

    def update(self):
        if not self.flag_lose:
            return

        if self.monster_kvant_active:
            self.move_monster_kvant()

        self.patrol_timer += time.dt
        if not self.is_patrolling and self.patrol_timer >= 40 and not self.monster_sound_played:
            self.monster_sound_played = True
            Audio('monster.mp3')
        if not self.is_patrolling and self.patrol_timer >= 45:
            self.start_monster_patrol()

        # СМЕРТЬ ОТ ПАТРУЛЬНОГО: только если не в шкафу
        if self.monster.enabled and not self.is_hiding:
            if distance(self.monster, self.player) < 10.0:
                self.lose_game()

        if self.monster.enabled and distance(self.monster, self.player) < 2.0:
            self.lose_game()

        self.coord_debug.text = f"X:{round(self.player.x, 1)} Y:{round(self.player.y, 1)} Z:{round(self.player.z, 1)}"

        if self.code_input.enabled or self.note_panel.enabled or self.is_hiding:
            self.hint.enabled = False
            return

        hit_info = raycast(self.player.camera_pivot.world_position, self.player.camera_pivot.forward, distance=5,
                           ignore=(self.player,))
        interactables = self.doors + self.notes + self.lockers + [self.button]
        if hit_info.hit and hit_info.entity in interactables:
            self.hint.enabled = True
        else:
            self.hint.enabled = False

    def move_monster_kvant(self):
        if not self.monster_kvant.enabled or self.is_hiding or self.note_panel.enabled or self.code_input.enabled:
            return

        to_monster = (self.monster_kvant.world_position - self.player.camera_pivot.world_position).normalized()
        dot = self.player.camera_pivot.forward.dot(to_monster)
        dist = distance(self.monster_kvant.world_position, self.player.world_position)

        if dist < 2.5:
            self.lose_game()
            return

        # Если игрок не смотрит на монстра (монстр в "мертвой зоне" зрения)
        if dot < 0.8:
            if dist > 1.5:
                # Сохраняем текущую высоту
                old_y = self.monster_kvant.y

                # Поворачиваем монстра к игроку
                self.monster_kvant.look_at(self.player)

                # Обнуляем наклон по X и Z (Roll), чтобы он стоял строго вертикально
                # Именно rotation_z отвечает за наклон "влево-вправо"
                self.monster_kvant.rotation_x = 0
                self.monster_kvant.rotation_z = 0

                # Движение вперед
                self.monster_kvant.position += self.monster_kvant.forward * time.dt * 6

                # Проверка пола
                ground_check = raycast(self.monster_kvant.world_position + Vec3(0, 5, 0), direction=(0, -1, 0),
                                       distance=15, ignore=(self.monster_kvant, self.player))
                if ground_check.hit:
                    self.monster_kvant.y = ground_check.point.y - 4.95
                else:
                    self.monster_kvant.y = old_y

    def input(self, key):
        if self.is_hiding and key in ('e', 'escape'):
            self.move_hike()
            return
        if self.note_panel.enabled and key in ('e', 'escape'):
            self.note_panel.enabled = False
            self.player.enabled = True
            mouse.locked = True
            return
        if self.code_input.enabled:
            if key == 'enter':
                self.check_code()
            elif key == 'escape':
                self.close_numpad()
            return

        if key == 'e':
            hit_info = raycast(self.player.camera_pivot.world_position, self.player.camera_pivot.forward, distance=5,
                               ignore=(self.player,))
            if hit_info.entity == self.button:
                self.is_door_locked = False
                print("Питание включено")
            elif hit_info.entity in self.doors:
                door = hit_info.entity
                if door.name == 'door' and self.is_door_locked:
                    pass
                if door.name == 'door 4' and not door.is_open:
                    self.open_numpad(door)
                else:
                    self.move_door(door)
                    if door.name == 'door' and True:#door.is_open
                        invoke(self.win_game, delay=1.5)
            elif hit_info.entity in self.notes:
                self.display_note(hit_info.entity.name)
            elif hit_info.entity in self.lockers:
                self.move_hike()

    def move_door(self, door):
        dist = 4 if not door.is_open else -4
        if door.axis == 'x':
            door.animate_x(door.x + dist, duration=1.2)
        else:
            door.animate_z(door.z + dist, duration=1.2)
        door.is_open = not door.is_open

        if door.name == 'door 1' and door.is_open:
            self.monster_kvant_active = True

    def lose_game(self):
        if not self.flag_lose:
            return
        self.flag_lose = False
        self.player.enabled = False
        self.monster_kvant.enabled = False
        mouse.locked = False
        self.lose_overlay = Entity(parent=camera.ui, model='quad', scale=(2, 1), color=color.black, z=-10)
        self.lose_msg = Text(text='ВЫ СТАЛИ ЧАСТЬЮ\nТЕНИ ПРОМЕТЕЯ', parent=camera.ui, origin=(0, 0), y=0.25, scale=3,
                             color=color.white, z=-11)
        self.restart_btn = Button(text='Рестарт', color=color.green, scale=(0.8, 0.08), y=-0.05, parent=camera.ui,
                                  z=-11)
        self.restart_btn.on_click = self.restart_logic
        self.exit_btn = Button(text='Выход', color=color.red, scale=(0.8, 0.08), y=-0.15, parent=camera.ui, z=-11)
        self.exit_btn.on_click = application.quit

    def win_game(self):
        if not self.flag_lose:
            return
        self.flag_lose = False
        self.player.enabled = False
        self.monster_kvant.enabled = False
        mouse.locked = False
        self.lose_overlay = Entity(parent=camera.ui, model='quad', scale=(2, 1), color=color.black, z=-10)
        self.lose_msg = Text(text='ПОБЕГ СОВЕРШЕН!', parent=camera.ui, origin=(0, 0), y=0.25, scale=3,
                             color=color.white, z=-11)
        self.restart_btn = Button(text='Рестарт', color=color.green, scale=(0.8, 0.08), y=-0.05, parent=camera.ui,
                                  z=-11)
        self.restart_btn.on_click = self.restart_logic
        self.exit_btn = Button(text='ВПЕРЕД', color=color.green, scale=(0.8, 0.08), y=-0.15, parent=camera.ui, z=-11)
        self.exit_btn.on_click = self.end

    def end(self):
        arcade_script = os.path.join(CURRENT_DIR, 'outro.py')
        subprocess.Popen([sys.executable, arcade_script])
        application.quit()

    def restart_logic(self):
        destroy(self.lose_overlay)
        if hasattr(self, 'lose_overlay'):
            destroy(self.lose_overlay)
            destroy(self.lose_msg)
        if hasattr(self, 'win_overlay'):
            destroy(self.win_overlay)
            destroy(self.win_msg)
        destroy(self.lose_msg)
        destroy(self.restart_btn)
        destroy(self.exit_btn)
        self.player.position = (2, 1, 8)
        self.player.enabled = True
        self.monster_kvant.position = (0, -1, 0)
        self.monster_kvant.enabled = True
        self.monster_kvant_active = False
        self.monster.enabled = False
        self.patrol_timer = 0
        self.is_patrolling = False
        self.flag_lose = True
        self.is_door_locked = True
        mouse.locked = True

        """Перемешивает список и ПЕРЕЗАПИСЫВАЕТ тексты в словаре"""
        shuffle(self.a)
        # Здесь мы заново создаем строки, чтобы они подхватили НОВЫЕ значения из self.a
        self.note_texts = {
            'wrote 1': 'Лабораторный журнал №402: Объект-01 подчиняется Квантовому эффекту наблюдателя. Пока за ним ведется мониторинг,'
                       'его частицы зафиксированы в одной точке. Но как только взгляд прекращается, волновая функция расширяется.'
                       'Он существует везде и нигде одновременно. Если вы его видите — не моргайте. Ваше внимание — это единственные цепи, '
                       f'которые его удерживают\n{self.a[0]}',
            'wrote 2': 'Медицинский отчет: «Лучевая болезнь прогрессирует у всех выживших. Пульсар — это космический маяк, '
                       'вращающаяся нейтронная звезда. Его ритм смертелен и точен. Гамма-лучи разрушают ДНК за долю секунды. '
                       'Свинецовые шкафы — единственный барьер, который эти лучи не могут преодолеть. '
                       f'Не игнорируйте cистему безопасности. Тень Пульсара не выбирает жертв, она просто выжигает всё живое на своем пути».\n{self.a[1]}',
            'wrote 3': 'Технический регламент: «При аварийном отключении реактора все системы переходят на резервные аккумуляторы. '
                       'Чтобы восстановить полное питание и разблокировать магнитные замки дверей, необходимо вручную '
                       'активировать термоядерный запал. Терминал управления находится в центральной рубке. Ищите ГОЛУБУЮ КНОПКУ. '
                       f'Вы должны нажать её\n{self.a[2]}',
            'wrote 4': 'Мы думали, что наука защитит нас. Но на расстоянии в 40 световых лет законы физики становятся нашими '
                       'врагами. Станция '"Прометей"' — это памятник человеческой гордыне. Мы построили её в месте, где '
                       'пространство и время ведут себя иначе. Мы здесь не исследователи. Мы — жертвы, принесенные в угоду '
                       f'великой пустоте. Прощайте\n{self.a[3]}'
        }
        for d in self.doors:
            if d.is_open:
                self.move_door(d)

        Audio('monster_ level.mp3')

    def start_monster_patrol(self):
        self.monster.enabled = True
        self.is_patrolling = True
        self.patrol_timer = 0
        patrol = Sequence()
        for point in self.monster_path:
            patrol.append(Func(self.monster.look_at, point))
            patrol.append(Func(self.monster.animate_position, point, duration=1.5))
            patrol.append(Wait(1.5))
        patrol.append(Func(self.finish_patrol))
        patrol.start()

    def finish_patrol(self):
        self.is_patrolling = False
        self.monster.enabled = False
        self.monster_sound_played = False

    def display_note(self, note_name):
        self.note_display.text = self.note_texts[note_name]
        self.note_display.wordwrap = 27
        self.note_panel.enabled = True
        self.player.enabled = False
        mouse.locked = False

    def open_numpad(self, door):
        self.current_door = door
        self.code_input.enabled = True
        self.code_input.active = True
        self.code_input.text = ''
        mouse.locked = False
        self.player.enabled = False

    def check_code(self):
        if self.code_input.text == ''.join(list(map(str, self.a[:4]))):
            self.move_door(self.current_door)
        self.close_numpad()

    def close_numpad(self):
        self.code_input.enabled = False
        mouse.locked = True
        self.player.enabled = True

    def move_hike(self):
        self.is_hiding = not self.is_hiding
        self.hide_overlay.enabled = self.is_hiding
        self.player.enabled = not self.is_hiding
        if not self.is_hiding:
            mouse.locked = True


view = Horror()
app.run()