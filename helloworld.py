from main import *

game = Scene(title="Hello World Example", fps=1)
x, y = game.width // 2 - 7, game.height // 2

game.clearscr()

def update():
    global x, y
    game.clear_layer(1)

    game.text(x, y, "Hello, World!", layer=1, color=32)
    game.text(x, y+1, "Use arrow keys to move", layer=1, color=34)

    key = game.handle_input()
    
    match key:
        case 'q':
            game.stop()
        case 'LEFT':
            x = max(0, x - 1)
        case 'RIGHT':
            x = min(game.width - 2, x + 1)
        case 'UP':
            y = max(0, y - 1)
        case 'DOWN':
            y = min(game.height - 2, y + 1)

game.run(update)