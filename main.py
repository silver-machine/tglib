import os
import time
import cursor
import msvcrt

ARROW_LEFT = b'K'
ARROW_RIGHT = b'M'
ARROW_UP = b'H'
ARROW_DOWN = b'P'

def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

class Sprite:
    def __init__(self, x, y, char='#', color=37, layer=1):
        self.x = x
        self.y = y

        self.char = char
        self.color = color
        self.layer = layer
    
    def dissolve(self):
        self.char = ' '

class Actor(Sprite):
    def __init__(self, x, y,
                 char='@', color=37, layer=2,
                 behaviour=None):
        super().__init__(x, y, char, color, layer)
        self.behaviour = behaviour
    
    def act(self):
        if self.behaviour:
            self.behaviour(self)

class Object(Sprite):
    def __init__(self, x, y,
                 char='#', color=37, layer=1,
                 moveable=False, pickable=False, collidable=True):
        super().__init__(x, y, char, color, layer)
        self.moveable = moveable
        self.pickable = pickable
        self.collidable = collidable

class Scene:
    def __init__(self, width=os.get_terminal_size()[0],
                 height=os.get_terminal_size()[1],
                 hide_cur=True, title="TGLib", bindings={}, fps=20):
        self.width = width
        self.height = height

        #   0 = background, 1 = objects, 2 = actors
        self.layers = [
            [[' ']*width for _ in range(height)],
            [[' ']*width for _ in range(height)],
            [[' ']*width for _ in range(height)]
        ]

        self.colors = [
            [[37]*width for _ in range(height)],
            [[37]*width for _ in range(height)],
            [[37]*width for _ in range(height)]
        ]

        self.prev_buffer = [[' ']*width for _ in range(height)]
        self.prev_colors = [[37]*width for _ in range(height)]

        if hide_cur:
            cursor.hide()

        os.system("title " + title)
        self.bindings = bindings
        self.fps = fps

    def set_char(self, x, y, char, layer=2, color=37):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][y][x] = char
            self.colors[layer][y][x] = color
    
    def text(self, x, y, string, layer=2, color=37):
        for i, char in enumerate(string):
            self.set_char(x + i, y, char, layer, color)

    def menu(self, x, y, title, options, layer=2, normal_color=37, highlight_color=30, highlight_bg=47, cursor=">"):

        selected = 0
        option_count = len(options)

        def draw():
            self.clear_area(x, y, max(len(title), max(len(opt) for opt in options)) + 2, option_count + 1, layer)

            self.text(x, y, title, layer, normal_color)

            for i, option in enumerate(options):
                if i == selected:
                    color = f"{highlight_bg};{highlight_color}"
                    self.text(x, y + i + 1, f"{cursor} {option}", layer, color)
                else:
                    self.text(x, y + i + 1, f"{' ' * len(cursor)} {option}", layer, normal_color)

            self.display()

        while True:
            draw()
            time.sleep(1 / self.fps)

            key = self.handle_input()
            if not key:
                continue

            if key == 'UP':
                selected = (selected - 1) % option_count
            elif key == 'DOWN':
                selected = (selected + 1) % option_count

            elif key in ('w', 'W'):
                selected = (selected - 1) % option_count
            elif key in ('s', 'S'):
                selected = (selected + 1) % option_count

            elif key == '\r':
                return selected, options[selected]

            elif key == '\x1b':
                return None, None
    
    def get_char(self, x, y):
        for layer in reversed(range(len(self.layers))):
            char = self.layers[layer][y][x]
            if char != ' ':
                return char
        return ' '

    def get_char_and_color(self, x, y):
        for layer in reversed(range(len(self.layers))):
            char = self.layers[layer][y][x]
            color = self.colors[layer][y][x]
            if char != ' ':
                return char, color
        return ' ', 37

    def get_surrounding_chars(self, x, y):
        surroundings = {}
        directions = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0),
            'up_left': (-1, -1),
            'up_right': (1, -1),
            'down_left': (-1, 1),
            'down_right': (1, 1)
        }
        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                surroundings[direction] = self.get_char(nx, ny)
            else:
                surroundings[direction] = None
        return surroundings

    def get_surrounding_chars_and_colors(self, x, y):
        surroundings = {}
        directions = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0),
            'up_left': (-1, -1),
            'up_right': (1, -1),
            'down_left': (-1, 1),
            'down_right': (1, 1)
        }
        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                surroundings[direction] = self.get_char_and_color(nx, ny)
            else:
                surroundings[direction] = (None, None)
        return surroundings
    
    def surrounded_by_x(self, x, y, target_char):
        surroundings = self.get_surrounding_chars(x, y)
        for char in surroundings.values():
            if char != target_char:
                return False
        return True

    def display(self):
        output = []
        for y in range(self.height):
            for x in range(self.width):
                char, color = self.get_char_and_color(x, y)
                if char != self.prev_buffer[y][x] or color != self.prev_colors[y][x]:
                    output.append(f"\033[{color}m\033[{y+1};{x+1}H{char}\033[0m")
        print(''.join(output), end='', flush=True)

        for y in range(self.height):
            for x in range(self.width):
                char, color = self.get_char_and_color(x, y)
                self.prev_buffer[y][x] = char
                self.prev_colors[y][x] = color
    
    def run_actors(self, actors):
        for actor in actors:
            actor.act(self)
            self.set_char(actor.x, actor.y, actor.char, layer=actor.layer, color=actor.color)
    
    def update_size(self, width=os.get_terminal_size()[0], height=os.get_terminal_size()[1],):
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self.layers = [
                [[' ']*width for _ in range(height)],
                [[' ']*width for _ in range(height)],
                [[' ']*width for _ in range(height)]
            ]
            self.colors = [
                [[37]*width for _ in range(height)],
                [[37]*width for _ in range(height)],
                [[37]*width for _ in range(height)]
            ]
            self.prev_buffer = [[' ']*width for _ in range(height)]
            self.prev_colors = [[37]*width for _ in range(height)]
        else:
            return

    def clearscr(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def clear_layer(self, layer):
        self.layers[layer] = [[' ']*self.width for _ in range(self.height)]
        self.colors[layer] = [[37]*self.width for _ in range(self.height)]
    
    def clear_all_layers(self):
        for layer in range(len(self.layers)):
            self.clear_layer(layer)
    
    def clear_char(self, x, y, layer=2):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][y][x] = ' '
            self.colors[layer][y][x] = 37
    
    def clear_area(self, x, y, w, h, layer=2):
        for i in range(h):
            for j in range(w):
                self.clear_char(x + j, y + i, layer)

    def showcursor(self):
        cursor.show()

    def hidecursor(self):
        cursor.hide()
    
    def handle_input(self):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key not in self.bindings:
                if key == b'\xe0':
                    key2 = msvcrt.getch()

                    if key2 in self.bindings:
                        self.bindings[key2]()
                        return None

                    if key2 == b'H':
                        return 'UP'
                    elif key2 == b'P':
                        return 'DOWN'
                    elif key2 == b'K':
                        return 'LEFT'
                    elif key2 == b'M':
                        return 'RIGHT'

                else:
                    return key.decode('utf-8')
            else:
                self.bindings[key]()
    
    def bind_key(self, key, function):
        self.bindings[key] = function

    def run(self, update_function):
        try:
            while True:
                update_function()
                self.display()
                time.sleep(1/self.fps)
        except KeyboardInterrupt:
            self.showcursor()
            self.clearscr()
    
    def stop(self, msg=""):
        self.showcursor()
        self.clearscr()
        print(msg) if msg else None
        quit()