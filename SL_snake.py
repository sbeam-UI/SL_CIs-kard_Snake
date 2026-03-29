import pygame
import random
from collections import namedtuple
from pygame.locals import K_RIGHT, K_LEFT, K_UP, K_DOWN, QUIT

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

Position = namedtuple('Point', 'x, y')

class Direction:
    right = 0
    left = 1
    up = 2
    down = 3

class Snake:
    def __init__(self, block_size, width, height):
        self.blocks = []
        self.blocks.append(Position(5, 5))  # 蛇头
        self.blocks.append(Position(4, 5))  # 初始1格蛇身
        self.block_size = block_size
        self.current_direction = Direction.right
        self.width = width
        self.height = height

        try:
            self.image = pygame.image.load('snake.png').convert_alpha()
        except FileNotFoundError:
            self.image = pygame.Surface((block_size, block_size))
            self.image.fill((0, 255, 0))

        self.body_src_x = 8 * self.block_size  # 蛇身用精灵图最后一格

    def move(self, grow=False):
        if self.current_direction == Direction.right:
            movesize = (1, 0)
        elif self.current_direction == Direction.left:
            movesize = (-1, 0)
        elif self.current_direction == Direction.up:
            movesize = (0, -1)
        else:
            movesize = (0, 1)
        head = self.blocks[0]
        new_head = Position(head.x + movesize[0], head.y + movesize[1])
        new_x = new_head.x % self.width
        new_y = new_head.y % self.height
        new_head = Position(new_x, new_y)
        self.blocks.insert(0, new_head)
        if not grow:
            self.blocks.pop()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[K_RIGHT] and self.current_direction != Direction.left:
            self.current_direction = Direction.right
        elif keys[K_LEFT] and self.current_direction != Direction.right:
            self.current_direction = Direction.left
        elif keys[K_UP] and self.current_direction != Direction.down:
            self.current_direction = Direction.up
        elif keys[K_DOWN] and self.current_direction != Direction.up:
            self.current_direction = Direction.down

    def draw(self, surface, frame):
        for index, block in enumerate(self.blocks):
            pos = (block.x * self.block_size, block.y * self.block_size)
            if index == 0:
                src_x = (self.current_direction * 2 + frame) * self.block_size
                src_rect = (src_x, 0, self.block_size, self.block_size)
                surface.blit(self.image, pos, src_rect)
            else:
                src_rect = (self.body_src_x, 0, self.block_size, self.block_size)
                surface.blit(self.image, pos, src_rect)

class Berry:
    def __init__(self, block_size):
        self.block_size = block_size
        try:
            self.image = pygame.image.load('berry.png')
        except FileNotFoundError:
            self.image = pygame.Surface((block_size, block_size))
            self.image.fill((255, 0, 0))
        self.position = Position(1, 1)

    def draw(self, surface):
        rect = self.image.get_rect()
        rect.left = self.position.x * self.block_size
        rect.top = self.position.y * self.block_size
        surface.blit(self.image, rect)

class Wall:
    def __init__(self, block_size, map_width, map_height):
        self.block_size = block_size
        self.map_width = map_width
        self.map_height = map_height

        # 加载不同位置的墙壁图片，缺失时用对应颜色兜底
        self.wall_imgs = {
            'top_bottom': self.load_image_or_placeholder('wall2.png', (150, 150, 150)),
            'top_left': self.load_image_or_placeholder('wall3.png', (200, 100, 100)),
            'top_right': self.load_image_or_placeholder('wall4.png', (100, 200, 100)),
            'bottom_right': self.load_image_or_placeholder('wall5.png', (100, 100, 200)),
            'bottom_left': self.load_image_or_placeholder('wall6.png', (200, 200, 100)),
            'default': self.load_image_or_placeholder('wall.png', (100, 100, 100))
        }

    def load_image_or_placeholder(self, filename, color):
        try:
            return pygame.image.load(filename).convert_alpha()
        except FileNotFoundError:
            surf = pygame.Surface((self.block_size, self.block_size))
            surf.fill(color)
            return surf

    def draw(self, surface):
        for y in range(self.map_height):
            for x in range(self.map_width):
                # 判断墙壁位置
                if y == 0 or y == self.map_height - 1:
                    # 上下墙壁用wall2.png
                    img = self.wall_imgs['top_bottom']
                    # 四个角落替换成对应图片
                    if y == 0 and x == 0:
                        img = self.wall_imgs['top_left']
                    elif y == 0 and x == self.map_width - 1:
                        img = self.wall_imgs['top_right']
                    elif y == self.map_height - 1 and x == self.map_width - 1:
                        img = self.wall_imgs['bottom_right']
                    elif y == self.map_height - 1 and x == 0:
                        img = self.wall_imgs['bottom_left']
                elif x == 0 or x == self.map_width - 1:
                    # 左右墙壁用默认wall.png
                    img = self.wall_imgs['default']
                else:
                    continue  # 非墙壁位置跳过

                pos = (x * self.block_size, y * self.block_size)
                surface.blit(img, pos)

class Game:
    WHITE = (255, 255, 255)
    BLACK = (0, 128, 0)

    def __init__(self, Width=640, Height=480):
        pygame.init()
        self.block_size = 16
        self.Win_width = Width
        self.Win_height = Height
        self.surface = pygame.display.set_mode((self.Win_width, self.Win_height))
        pygame.display.set_caption('贪吃蛇游戏 - Made with Pygame')
        self.score = 0
        self.frame = 0
        self.running = True
        self.Clock = pygame.time.Clock()

        # 速度规则：初始5，每10分+1，最大12
        self.initial_fps = 5
        self.max_fps = 12
        self.fps = self.initial_fps

        self.font = pygame.font.Font(None, 32)

        # 生成地图尺寸
        self.map_width = 40
        self.map_height = 30
        # 初始化墙壁（传入地图尺寸）
        self.wall = Wall(self.block_size, self.map_width, self.map_height)

        self.snake = Snake(self.block_size, self.map_width, self.map_height)
        self.berry = Berry(self.block_size)
        self.position_berry()

    def update_speed(self):
        self.fps = self.initial_fps + (self.score // 10)
        if self.fps > self.max_fps:
            self.fps = self.max_fps

    def position_berry(self):
        while True:
            bx = random.randint(0, self.map_width - 1)
            by = random.randint(0, self.map_height - 1)
            pos = Position(bx, by)
            # 判断是否在墙壁上
            is_wall = (bx == 0 or bx == self.map_width-1 or by ==0 or by == self.map_height-1)
            if pos not in self.snake.blocks and not is_wall:
                self.berry.position = pos
                break

    def berry_collision(self):
        head = self.snake.blocks[0]
        if head == self.berry.position:
            self.score += 1
            self.update_speed()
            self.position_berry()
            return True
        return False

    def head_hit_body(self):
        head = self.snake.blocks[0]
        return head in self.snake.blocks[1:]

    def head_hit_wall(self):
        return False

    def draw_data(self):
        text = f'Score: {self.score}  Speed: {self.fps}  Length: {len(self.snake.blocks)}'
        text_img = self.font.render(text, True, self.WHITE)
        self.surface.blit(text_img, (10, 10))

    def draw(self):
        self.surface.fill(self.BLACK)
        self.wall.draw(self.surface)
        self.berry.draw(self.surface)
        self.snake.draw(self.surface, self.frame)
        self.draw_data()
        pygame.display.update()

    def play(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False

            self.frame = (self.frame + 1) % 2
            self.snake.handle_input()
            grow = self.berry_collision()
            self.snake.move(grow=grow)

            if self.head_hit_body():
                print(f'游戏结束！最终分数: {self.score} 蛇身长度: {len(self.snake.blocks)}')
                self.running = False

            self.draw()
            self.Clock.tick(self.fps)

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.play()