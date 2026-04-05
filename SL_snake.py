import pygame
import random
import hashlib
import threading
import sys
import time
from collections import namedtuple
from pygame.locals import K_RIGHT, K_LEFT, K_UP, K_DOWN, QUIT
from tqdm import tqdm


# ===================== 【防修改器+防变速器】修复误报版 =====================
class SafeValue:
    def __init__(self, initial=0):
        self.mask = random.getrandbits(32)
        self.shift = random.randint(3, 8)
        self.offset = random.randint(0x1000, 0x9000)
        self._enc1 = (initial ^ self.mask) + self.offset
        self._enc2 = (initial << self.shift) ^ self.mask
        self._enc3 = (initial ^ 0x9E3779B9) - self.offset

    @property
    def value(self):
        a = (self._enc1 - self.offset) ^ self.mask
        b = (self._enc2 ^ self.mask) >> self.shift
        c = (self._enc3 + self.offset) ^ 0x9E3779B9

        if a == b == c:
            return a
        else:
            print("断开连接（内存篡改）")
            pygame.quit()
            sys.exit()

    @value.setter
    def value(self, v):
        self._enc1 = (v ^ self.mask) + self.offset
        self._enc2 = (v << self.shift) ^ self.mask
        self._enc3 = (v ^ 0x9E3779B9) - self.offset


# 防变速器（修复误报：放宽阈值+首次运行豁免）
class AntiSpeedHack:
    def __init__(self, max_delta=500, exempt_frames=60):
        self.max_delta = max_delta  # 最大允许帧间隔 500ms（原150ms太严）
        self.exempt_frames = exempt_frames  # 前60帧不检测（避免启动波动）
        self.frame_count = 0  # 帧计数器
        self.last_time = time.time() * 1000

    def check(self):
        self.frame_count += 1
        # 前60帧豁免检测
        if self.frame_count < self.exempt_frames:
            self.last_time = time.time() * 1000
            return

        now = time.time() * 1000
        delta = now - self.last_time
        self.last_time = now

        # 只拦截极端变速（正常波动不会触发）
        if delta < 5 or delta > self.max_delta:
            print("断开连接（变速作弊）")
            pygame.quit()
            sys.exit()


# 防注入（修复误报：缩小黑名单范围，只针对作弊工具）
def check_blacklist():
    # 只保留明确的作弊工具关键词，去掉容易误判的 speed
    black = ["cheatengine", "frida", "injector", "dllinject", "memoryhack"]
    for name in list(sys.modules.keys()):
        if any(x in name.lower() for x in black):
            print("断开连接（可疑工具）")
            sys.exit()


check_blacklist()

# ===================== 游戏启动LOGO+进度条 =====================
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

bar = tqdm(total=100, leave=False, file=sys.stdout)
for i in range(100):
    time.sleep(0.01)
    bar.update(1)

# ===================== 游戏基础定义 =====================
Position = namedtuple('Point', 'x y')


class Direction:
    right, left, up, down = 0, 1, 2, 3


# ===================== 蛇类 =====================
class Snake:
    def __init__(self, block_size, w, h):
        self.blocks = [Position(5, 5), Position(4, 5)]
        self.block_size = block_size
        self.current_direction = Direction.right
        self.w, self.h = w, h
        try:
            self.image = pygame.image.load('snake.png').convert_alpha()
        except:
            self.image = pygame.Surface((block_size, block_size))
            self.image.fill((0, 255, 0))
        self.body_src_x = 8 * block_size

    def move(self, grow=False):
        head = self.blocks[0]
        dir_map = {
            Direction.right: Position(head.x + 1, head.y),
            Direction.left: Position(head.x - 1, head.y),
            Direction.up: Position(head.x, head.y - 1),
            Direction.down: Position(head.x, head.y + 1)
        }
        new_head = dir_map[self.current_direction]

        # 穿墙逻辑
        if new_head.x < 0:
            new_head = Position(self.w - 1, new_head.y)
        elif new_head.x >= self.w:
            new_head = Position(0, new_head.y)
        if new_head.y < 0:
            new_head = Position(new_head.x, self.h - 1)
        elif new_head.y >= self.h:
            new_head = Position(new_head.x, 0)

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
        if dx > 3 or dy > 3:
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
            x, y = b.x * self.block_size, b.y * self.block_size
            if i == 0:
                frame = 1 if self.is_near_and_facing_berry(berry_pos) else 0
                src_x = (self.current_direction * 2 + frame) * self.block_size
                surface.blit(self.image, (x, y), (src_x, 0, self.block_size, self.block_size))
            else:
                surface.blit(self.image, (x, y), (self.body_src_x, 0, self.block_size, self.block_size))


# ===================== 果子类 =====================
class Berry:
    def __init__(self, size):
        self.size = size
        try:
            self.img = pygame.image.load('berry.png')
        except:
            self.img = pygame.Surface((size, size))
            self.img.fill((255, 0, 0))
        self.pos = Position(10, 10)

    def draw(self, surf):
        sx, sy = self.pos.x * self.size, self.pos.y * self.size
        surf.blit(self.img, (sx, sy))


# ===================== 墙壁类 =====================
class Wall:
    def __init__(self, block_size, map_width, map_height):
        self.block_size = block_size
        self.map_width = map_width
        self.map_height = map_height

        def load_image_or_placeholder(filename, color):
            try:
                return pygame.image.load(filename).convert_alpha()
            except FileNotFoundError:
                surf = pygame.Surface((block_size, block_size))
                surf.fill(color)
                return surf

        self.wall_imgs = {
            'top_bottom': load_image_or_placeholder('wall2.png', (150, 150, 150)),
            'top_left': load_image_or_placeholder('wall3.png', (200, 100, 100)),
            'top_right': load_image_or_placeholder('wall4.png', (100, 200, 100)),
            'bottom_right': load_image_or_placeholder('wall5.png', (100, 100, 200)),
            'bottom_left': load_image_or_placeholder('wall6.png', (200, 200, 100)),
            'default': load_image_or_placeholder('wall.png', (100, 100, 100))
        }

    def draw(self, surface):
        for y in range(self.map_height):
            for x in range(self.map_width):
                if y == 0 or y == self.map_height - 1:
                    img = self.wall_imgs['top_bottom']
                    if y == 0 and x == 0:
                        img = self.wall_imgs['top_left']
                    elif y == 0 and x == self.map_width - 1:
                        img = self.wall_imgs['top_right']
                    elif y == self.map_height - 1 and x == self.map_width - 1:
                        img = self.wall_imgs['bottom_right']
                    elif y == self.map_height - 1 and x == 0:
                        img = self.wall_imgs['bottom_left']
                elif x == 0 or x == self.map_width - 1:
                    img = self.wall_imgs['default']
                else:
                    continue
                pos = (x * self.block_size, y * self.block_size)
                surface.blit(img, pos)


# ===================== 游戏主类 =====================
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.block_size = 16
        self.map_w, self.map_h = 40, 30
        self.screen = pygame.display.set_mode((self.map_w * self.block_size, self.map_h * self.block_size))
        pygame.display.set_caption("Made with Pygame")
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.score = SafeValue(0)  # 防CE分数
        self.fps = 5
        self.max_fps = 12

        # 防变速器启动（修复误报版本）
        self.anti_speed = AntiSpeedHack(max_delta=500, exempt_frames=60)

        # 背景音乐容错
        try:
            self.music = pygame.mixer.Sound('神人音乐.mp3')
            self.music.play(-1)
        except:
            print("背景音乐加载失败，跳过播放")

        # 游戏元素初始化
        self.wall = Wall(self.block_size, self.map_w, self.map_h)
        self.snake = Snake(self.block_size, self.map_w, self.map_h)
        self.berry = Berry(self.block_size)
        # 字体容错
        try:
            self.font = pygame.font.Font('Minecraft.ttf', 20)
        except:
            self.font = pygame.font.Font(None, 20)
        self.random_berry()

        # 可选：核心函数校验（稳定，不会误杀）
        self.core_hash = hashlib.md5(self.snake.move.__code__.co_code).hexdigest()
        threading.Thread(target=self.check_integrity, daemon=True).start()

    def random_berry(self):
        while True:
            x = random.randint(1, self.map_w - 2)
            y = random.randint(1, self.map_h - 2)
            pos = Position(x, y)
            if pos not in self.snake.blocks:
                self.berry.pos = pos
                break

    def check_integrity(self):
        """后台校验核心函数是否被篡改 - 稳定版"""
        while self.running:
            try:
                current_hash = hashlib.md5(self.snake.move.__code__.co_code).hexdigest()
                if current_hash != self.core_hash:
                    print("断开连接（代码篡改）")
                    self.running = False
                    break
            except:
                pass  # 异常不处理，避免闪退
            time.sleep(5)  # 5秒一次，降低资源占用

    def run(self):
        while self.running:
            # 防变速器 每帧检测
            self.anti_speed.check()

            for e in pygame.event.get():
                if e.type == QUIT:
                    self.running = False
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    self.paused = not self.paused

            if not self.paused:
                self.snake.handle_input()
                grow = (self.snake.blocks[0] == self.berry.pos)
                if grow:
                    self.score.value += 1
                    self.fps = min(5 + self.score.value // 10, self.max_fps)
                    self.random_berry()
                self.snake.move(grow)

                # 自撞才结束游戏
                if self.snake.blocks[0] in self.snake.blocks[1:]:
                    print(f"游戏结束！得分：{self.score.value}")
                    self.running = False

            # 绘制画面
            self.screen.fill((0, 128, 0))
            self.wall.draw(self.screen)
            self.berry.draw(self.screen)
            self.snake.draw(self.screen, self.berry.pos)
            text = self.font.render(f"Score:{self.score.value}  Speed:{self.fps}", True, (0, 64, 0))
            self.screen.blit(text, (10, 10))
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()


if __name__ == "__main__":
    Game().run()