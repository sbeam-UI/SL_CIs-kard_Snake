import pygame
import random
import hashlib
import threading
import time
import sys
from collections import namedtuple
from pygame.locals import K_RIGHT, K_LEFT, K_UP, K_DOWN, QUIT

# ===================== 纯Python防注入（无Windows API） =====================
# 1. 关键变量加密保护
class ProtectedVar:
    def __init__(self, value):
        self.key = 98765
        self.encrypted = value ^ self.key
    @property
    def value(self):
        return self.encrypted ^ self.key
    @value.setter
    def value(self, v):
        self.encrypted = v ^ self.key

# 2. 核心函数哈希校验
def get_func_hash(func):
    return hashlib.md5(func.__code__.co_code).hexdigest()

# 3. 可疑模块检测
def check_suspicious_modules():
    suspicious = ["hook", "inject", "frida", "debug"]
    for name in sys.modules.keys():
        if any(k in name.lower() for k in suspicious):
            sys.exit(0)

# 启动检测
check_suspicious_modules()

# ===================== 游戏代码 =====================
print('\n')
print(' $$$$$$\  $$\   $$\  $$$$$$\  $$\   $$\ $$$$$$$$\ ')
print('$$  __$$\ $$$\  $$ |$$  __$$\ $$ | $$  |$$ ______|')
print('$$ /  \__|$$$$\ $$ |$$ /  $$ |$$ |$$  / $$ |      ')
print('\$$$$$$\  $$ $$|$$ |$$$$$$$$ |$$$$$  /  $$$$$\    ')
print(' \____$$\ $$ \ |$$ |$$  __$$ |$$  $$<   $$  __|   ')
print('$$\   $$ |$$ |\$$$ |$$ |  $$ |$$ |\$$\  $$ |      ')
print(' \$$$$$  /$$ | \$$ |$$ |  $$ |$$ | \$$\ $$$$$$$$\ ')
print('  \_____/ \__|  \__|\__|  \__|\__|  \__|\________|')
print('\n')
print('emergency stress-mitigation software booting up...')

Position = namedtuple('Point', 'x y')

class Direction:
    right, left, up, down = 0, 1, 2, 3

class Snake:
    def __init__(self, block_size, w, h):
        self.blocks = [Position(5,5), Position(4,5)]
        self.block_size = block_size
        self.current_direction = Direction.right
        self.w, self.h = w, h
        try:
            self.image = pygame.image.load('snake.png').convert_alpha()
        except:
            self.image = pygame.Surface((block_size, block_size))
            self.image.fill((0,255,0))
        self.body_src_x = 8 * block_size

    def move(self, grow=False):
        head = self.blocks[0]
        dir_map = {
            Direction.right: Position(head.x+1, head.y),
            Direction.left: Position(head.x-1, head.y),
            Direction.up: Position(head.x, head.y-1),
            Direction.down: Position(head.x, head.y+1)
        }
        new_head = dir_map[self.current_direction]
        self.blocks.insert(0, new_head)
        if not grow:
            self.blocks.pop()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[K_RIGHT] and self.current_direction != Direction.left:
            self.current_direction = Direction.right
        if keys[K_LEFT] and self.current_direction != Direction.right:
            self.current_direction = Direction.left
        if keys[K_UP] and self.current_direction != Direction.down:
            self.current_direction = Direction.up
        if keys[K_DOWN] and self.current_direction != Direction.up:
            self.current_direction = Direction.down

    def is_near_and_facing_berry(self, berry_pos):
        head = self.blocks[0]
        dx, dy = abs(berry_pos.x - head.x), abs(berry_pos.y - head.y)
        if dx >3 or dy>3:
            return False
        dir_check = {
            Direction.right: berry_pos.x > head.x and berry_pos.y == head.y,
            Direction.left: berry_pos.x < head.x and berry_pos.y == head.y,
            Direction.up: berry_pos.y < head.y and berry_pos.x == head.x,
            Direction.down: berry_pos.y > head.y and berry_pos.x == head.x
        }
        return dir_check[self.current_direction]

    def draw(self, surface, berry_pos):
        for i, b in enumerate(self.blocks):
            x, y = b.x*self.block_size, b.y*self.block_size
            if i == 0:
                frame = 1 if self.is_near_and_facing_berry(berry_pos) else 0
                src_x = (self.current_direction*2 + frame)*self.block_size
                surface.blit(self.image, (x,y), (src_x,0,self.block_size,self.block_size))
            else:
                surface.blit(self.image, (x,y), (self.body_src_x,0,self.block_size,self.block_size))

class Berry:
    def __init__(self, size):
        self.size = size
        try:
            self.img = pygame.image.load('berry.png')
        except:
            self.img = pygame.Surface((size,size))
            self.img.fill((255,0,0))
        self.pos = Position(10,10)
    def draw(self, surf):
        surf.blit(self.img, (self.pos.x*self.size, self.pos.y*self.size))

class Wall:
    def __init__(self, size, w, h):
        self.size, self.w, self.h = size, w, h
        def load_img(name, color):
            try: return pygame.image.load(name).convert_alpha()
            except:
                s = pygame.Surface((size,size))
                s.fill(color)
                return s
        self.wall_imgs = {
            'top_bottom': load_img('wall2.png', (150,150,150)),
            'top_left': load_img('wall3.png', (200,100,100)),
            'top_right': load_img('wall4.png', (100,200,100)),
            'bottom_right': load_img('wall5.png', (100,100,200)),
            'bottom_left': load_img('wall6.png', (200,200,100)),
            'default': load_img('wall.png', (100,100,100))
        }
    def draw(self, surf):
        for y in range(self.h):
            for x in range(self.w):
                px, py = x*self.size, y*self.size
                if y ==0 or y == self.h-1:
                    img = self.wall_imgs['top_bottom']
                    if y==0 and x==0: img=self.wall_imgs['top_left']
                    elif y==0 and x==self.w-1: img=self.wall_imgs['top_right']
                    elif y==self.h-1 and x==self.w-1: img=self.wall_imgs['bottom_right']
                    elif y==self.h-1 and x==0: img=self.wall_imgs['bottom_left']
                elif x ==0 or x == self.w-1:
                    img = self.wall_imgs['default']
                else:
                    continue
                surf.blit(img, (px,py))

class Game:
    def __init__(self):
        pygame.init()
        self.block_size = 16
        self.map_w, self.map_h = 40, 30
        self.screen = pygame.display.set_mode((self.map_w*self.block_size, self.map_h*self.block_size))
        pygame.display.set_caption("Made with Pygame")
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.score = ProtectedVar(0)  # 加密保护分数
        self.fps = 5
        self.max_fps = 12

        self.wall = Wall(self.block_size, self.map_w, self.map_h)
        self.snake = Snake(self.block_size, self.map_w, self.map_h)
        self.berry = Berry(self.block_size)
        self.font = pygame.font.Font('Minecraft.ttf', 20)
        self.random_berry()

        # 启动核心函数校验线程
        self.core_hash = get_func_hash(self.snake.move)
        threading.Thread(target=self.check_core_integrity, daemon=True).start()

    def random_berry(self):
        while True:
            x = random.randint(1, self.map_w-2)
            y = random.randint(1, self.map_h-2)
            pos = Position(x,y)
            if pos not in self.snake.blocks:
                self.berry.pos = pos
                break

    def check_core_integrity(self):
        """校验蛇移动函数是否被篡改"""
        while True:
            if get_func_hash(self.snake.move) != self.core_hash:
                self.running = False
            time.sleep(2)

    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == QUIT:
                    self.running = False
                if e.type == pygame.MOUSEBUTTONDOWN and e.button ==3:
                    self.paused = not self.paused

            if not self.paused:
                self.snake.handle_input()
                grow = self.snake.blocks[0] == self.berry.pos
                if grow:
                    self.score.value +=1
                    self.fps = min(5 + self.score.value//10, self.max_fps)
                    self.random_berry()
                self.snake.move(grow)

                if self.snake.blocks[0] in self.snake.blocks[1:]:
                    print(f"游戏结束！分数: {self.score.value}")
                    self.running = False

            self.screen.fill((0,120,0))
            self.wall.draw(self.screen)
            self.berry.draw(self.screen)
            self.snake.draw(self.screen, self.berry.pos)
            text = self.font.render(f"Score:{self.score.value} Speed:{self.fps}", True, (255,255,255))
            self.screen.blit(text, (10,10))
            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

if __name__ == "__main__":
    Game().run()