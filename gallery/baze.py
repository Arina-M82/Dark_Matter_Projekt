import arcade
import arcade.gui
import sqlite3
import os


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
def get_asset_path(filename):
    return os.path.join(CURRENT_DIR, filename)
class GalleryView(arcade.View):
    # Добавляем аргумент back_view. Это и есть твой сохраненный этап стрельбы.
    def __init__(self, back_view):
        super().__init__()
        self.back_view = back_view  # Теперь галерея "держит в руках" твою игру

        self.current_id = 1
        self.get_info(self.current_id)

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Кнопка закрытия
        self.close_button = arcade.gui.UIFlatButton(text="X", width=40, x=1480, y=690)
        self.close_button.style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(font_color=arcade.color.WHITE, bg=arcade.color.RED_DEVIL),
            "hover": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.DARK_RED),
            "press": arcade.gui.UIFlatButton.UIStyle(bg=arcade.color.BLACK),
        }
        self.close_button.on_click = self.on_click_close
        self.manager.add(self.close_button)

    def on_click_close(self, event):
        # ВАЖНО: Мы не создаем новую игру, а возвращаем старую!
        self.manager.disable()
        self.window.show_view(self.back_view)  # Возвращаемся в точку паузы

    # ... остальной код (get_info, on_draw, on_key_press) оставляешь как есть ...

    # ВАША ФУНКЦИЯ ВНУТРИ КЛАССА
    def get_info(self, id):
        conn = sqlite3.connect(get_asset_path("nee.db"))
        cursor = conn.cursor()
        query = f"SELECT name, line, picture FROM {'facts'} WHERE id = ?"
        cursor.execute(query, (id,))  # здесь я поставила id вместо 1, чтобы можно было листать
        result = cursor.fetchone()

        cursor.execute("SELECT MAX(id) FROM facts")
        self.max_id = cursor.fetchone()[0]
        if self.max_id == None:
            return
        else:
            item_name, item_description, item_picture = result
            self.item_name = item_name
            self.item_description = item_description
            self.texture = arcade.load_texture(get_asset_path(item_picture))
        conn.close()

    def on_draw(self):
        self.clear()
        if self.max_id == None:
            arcade.draw_text('У вас пока нет разблокированных картинок', 800, 375, arcade.color.WHITE, 24, bold=True, anchor_x="center")
            self.manager.draw()
        else:
            arcade.draw_texture_rect(rect=arcade.rect.XYWH(800, 375, 1600, 750), texture=arcade.load_texture(get_asset_path('fon.jpg')))
            arcade.draw_text(self.item_name, 800, 700, arcade.color.WHITE, 24, bold=True, anchor_x="center")
            arcade.draw_text(self.item_description, 775, 650, arcade.color.WHITE, 14, width=1500, multiline=True,
                             anchor_y="top", anchor_x="center")
            arcade.draw_text(f"Запись {self.current_id} из {self.max_id}", 800, 50, arcade.color.WHITE, 12,
                             anchor_x="center")
            arcade.draw_text(f"Переключайте стрелочками", 1100, 50, arcade.color.RED, 12,
                             anchor_x="center")
            arcade.draw_texture_rect(rect=arcade.rect.XYWH(800, 320, 850, 450), texture=self.texture)
            self.manager.draw()

    def on_key_press(self, key, modifiers):
        # Логика зацикливания
        if key == arcade.key.RIGHT:
            self.current_id += 1
            if self.current_id > self.max_id:
                self.current_id = 1
            self.get_info(self.current_id)

        elif key == arcade.key.LEFT:
            self.current_id -= 1
            if self.current_id < 1:
                self.current_id = self.max_id
            self.get_info(self.current_id)

    def on_mouse_press(self, x, y, button, modifiers):
        if x >= 1460 and y >= 670:
            return


def db(item_id):
    # 1. Подключаемся к исходной базе и забираем данные
    conn_source = sqlite3.connect(get_asset_path("need.db"))
    cursor_source = conn_source.cursor()

    cursor_source.execute("SELECT name, line, picture FROM facts WHERE id = ?", (item_id,))
    result = cursor_source.fetchone()
    conn_source.close()

    if result:
        item_name, item_line, item_picture = result

        # 2. Подключаемся к целевой базе и записываем данные
        conn_dest = sqlite3.connect(get_asset_path("nee.db"))
        cursor_dest = conn_dest.cursor()

        query = "INSERT OR REPLACE INTO facts (id, name, line, picture) VALUES (?, ?, ?, ?)"
        cursor_dest.execute(query, (item_id, item_name, item_line, item_picture))

        conn_dest.commit()
        conn_dest.close()
def delete():
    conn = sqlite3.connect(get_asset_path("nee.db"))
    cursor = conn.cursor()

    # Удаляет все строки
    cursor.execute("DELETE FROM facts")

    conn.commit()
    conn.close()

def maxi():
    conn = sqlite3.connect(get_asset_path("nee.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM facts")
    max_id = cursor.fetchone()[0]
    return max_id