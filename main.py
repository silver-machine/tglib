import os
import time
import cursor
import msvcrt

ARROW_LEFT = b'K'
ARROW_RIGHT = b'M'
ARROW_UP = b'H'
ARROW_DOWN = b'P'

class Scene:
    def __init__(self, width=os.get_terminal_size()[0], height=os.get_terminal_size()[1], hide_cur=True, title="TGLib", bindings={}):
        self.width = width
        self.height = height

        # layers:
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

    def set_char(self, x, y, char, layer=2, color=37):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][y][x] = char
            self.colors[layer][y][x] = color
    
    def text(self, x, y, string, layer=2, color=37):
        for i, char in enumerate(string):
            self.set_char(x + i, y, char, layer, color)
    
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
    
    def surrounded_by(self, x, y, target_char):
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

        # update buffers
        for y in range(self.height):
            for x in range(self.width):
                char, color = self.get_char_and_color(x, y)
                self.prev_buffer[y][x] = char
                self.prev_colors[y][x] = color
    
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
                    if key2 in [b'K', b'M', b'H', b'P']:
                        self.bindings[key2]()
                    else:
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

    def run(self, update_function, fps=20):
        try:
            while True:
                update_function()
                self.display()
                time.sleep(1/fps)
        except KeyboardInterrupt:
            self.showcursor()
            self.clearscr()
    
    def stop(self, msg=""):
        self.showcursor()
        self.clearscr()
        print(msg) if msg else None
        quit()