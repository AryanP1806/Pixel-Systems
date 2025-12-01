import pygame
import sys
import math
import random
from dataclasses import dataclass

# ------------------------- Config & Constants -------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60
TILE = 48
GRAVITY = 0.6
MAX_FALL_SPEED = 16
FRICTION = 0.86
AIR_FRICTION = 0.98

DEBUG_DRAW = False

# Colors
WHITE = (245, 245, 245)
BLACK = (18, 18, 18)
NIGGA = (0,0,0)
DARK_GREY = (50, 50, 50)
SKY = (135, 206, 235)
GREEN = (60, 170, 60)
GOLD = (255, 204, 0)
RED = (220, 60, 60)
ORANGE = (255, 140, 0)
BLUE = (60, 120, 220)
PURPLE = (150, 70, 200)
SILVER = (180, 180, 180)

# ------------------------- Helper Functions & Classes -------------------------

def clamp(value, min_val, max_val):
    """Restricts a value to a given range."""
    return max(min_val, min(max_val, value))

@dataclass
class Camera:
    """A simple 2D camera that follows a target."""
    x: float = 0.0
    y: float = 0.0

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Applies the camera offset to a rect."""
        return rect.move(-int(self.x), -int(self.y))

    def update(self, target_rect: pygame.Rect, level_width: int, level_height: int):
        """Smoothly follows the target rect and stays within level bounds."""
        target_x = target_rect.centerx - WIDTH / 2
        target_y = target_rect.centery - HEIGHT / 2
        
        # Smooth follow using linear interpolation (lerp)
        self.x += (target_x - self.x) * 0.08
        self.y += (target_y - self.y) * 0.06
        
        # Clamp camera to level boundaries
        self.x = clamp(self.x, 0, max(0, level_width - WIDTH))
        self.y = clamp(self.y, 0, max(0, level_height - HEIGHT))

# ------------------------- Game Entities -------------------------

class Particle:
    """Creates a simple particle for effects like smoke, sparkles, etc."""
    def __init__(self, pos, vel, radius, life, color):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.radius = radius
        self.life = life
        self.color = color
        self.age = 0

    def update(self, dt):
        """Updates particle position, velocity, and lifespan."""
        self.age += dt
        self.pos += self.vel * dt
        self.vel.y += GRAVITY * 10 * dt  # Particles have some gravity
        self.radius *= 0.985
        return self.age < self.life and self.radius > 0.5

    def draw(self, surf, cam):
        """Draws the particle on the screen."""
        if self.radius > 0.5:
            screen_pos = (int(self.pos.x - cam.x), int(self.pos.y - cam.y))
            pygame.draw.circle(surf, self.color, screen_pos, int(self.radius))


class Entity(pygame.sprite.Sprite):
    """Base class for all game objects."""
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.Vector2(x, y) # Use a vector for precise float-based position
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False


class Platform(Entity):
    """A static solid platform."""
    def __init__(self, x, y, w=TILE, h=TILE):
        super().__init__(x, y, w, h)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, (70, 70, 70), (0, 0, w, h), border_radius=6)
        pygame.draw.rect(self.image, (100, 100, 100), (4, 4, w-8, h-8), border_radius=6)

class InvisibleBlock(Entity):
    """An invisible solid block that is only visible in debug mode."""
    def __init__(self, x, y, w=TILE, h=TILE):
        super().__init__(x, y, w, h)
        # The block is transparent by default.
        # If debug mode is on, draw a faint outline to make it visible.
        if DEBUG_DRAW:
            pygame.draw.rect(self.image, (100, 100, 255, 150), self.image.get_rect(), 2, border_radius=6)


class JumpPad(Platform):
    """A platform that boosts the player's jump."""
    def __init__(self, x, y):
        super().__init__(x, y, TILE, TILE // 2)
        self.rect.y = y + TILE // 2 # Position it at the bottom of the tile space
        self.pos.y = self.rect.y
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, (50, 140, 50), (0, 0, self.rect.w, self.rect.h), border_radius=6)
        pygame.draw.rect(self.image, (80, 200, 80), (4, 4, self.rect.w-8, self.rect.h-8), border_radius=6)


class Coin(Entity):
    """A collectible coin."""
    def __init__(self, x, y):
        super().__init__(x, y, TILE//2, TILE//2)
        self.base_y = y
        self.anim_timer = random.random() * math.pi * 2
        self.draw_coin()

    def draw_coin(self):
        self.image.fill((0,0,0,0))
        r = self.image.get_rect()
        pygame.draw.ellipse(self.image, GOLD, r)
        pygame.draw.ellipse(self.image, (255, 230, 100), r.inflate(-8, -8))
        pygame.draw.line(self.image, (255, 220, 60), (r.w*0.5, 6), (r.w*0.5, r.h-6), 4)

    def update(self, dt):
        """Makes the coin bob up and down."""
        self.anim_timer += dt * 5
        self.pos.y = self.base_y + math.sin(self.anim_timer) * 4
        self.rect.y = int(self.pos.y)


class PowerUp(Entity):
    """A collectible power-up (speed, jump, or star)."""
    TYPES = ("speed", "jump", "star")
    COLORS = {"speed": ORANGE, "jump": BLUE, "star": PURPLE}

    def __init__(self, x, y, kind=None):
        super().__init__(x, y, TILE//2, TILE//2)
        self.kind = kind or random.choice(self.TYPES)
        self.anim_timer = random.random() * math.pi * 2
        self.base_y = y
        self.draw()

    def draw(self):
        self.image.fill((0,0,0,0))
        r = self.image.get_rect()
        col = self.COLORS[self.kind]
        pygame.draw.rect(self.image, col, r, border_radius=10)
        pygame.draw.rect(self.image, WHITE, r.inflate(-6, -6), 2, border_radius=8)

        if self.kind == "star":
            points = []
            cx, cy, R_outer, R_inner = r.centerx, r.centery, r.w * 0.35, r.w * 0.15
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                radius = R_outer if i % 2 == 0 else R_inner
                points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
            pygame.draw.polygon(self.image, SILVER, points)
        elif self.kind == "speed":
            pygame.draw.polygon(self.image, WHITE, [(r.w*0.3, r.h*0.8), (r.w*0.7, r.h*0.5), (r.w*0.3, r.h*0.2)])
        elif self.kind == "jump":
            pygame.draw.arc(self.image, WHITE, r.inflate(-12, -12), math.pi, 2*math.pi, 3)

    def update(self, dt):
        """Makes the power-up bob up and down."""
        self.anim_timer += dt * 4
        self.pos.y = self.base_y + math.sin(self.anim_timer) * 3
        self.rect.y = int(self.pos.y)


class Enemy(Entity):
    """A simple walking enemy."""
    def __init__(self, x, y):
        super().__init__(x, y, TILE-8, TILE-8)
        self.speed = 25.0
        self.direction = 1
        self.alive = True
        self.draw_enemy()

    def draw_enemy(self):
        self.image.fill((0,0,0,0))
        r = self.image.get_rect()
        pygame.draw.rect(self.image, RED, r, border_radius=10)
        pygame.draw.rect(self.image, (255, 160, 160), r.inflate(-8,-8), border_radius=8)
        pygame.draw.circle(self.image, BLACK, (int(r.w*0.35), int(r.h*0.35)), 5)
        pygame.draw.circle(self.image, BLACK, (int(r.w*0.65), int(r.h*0.35)), 5)

    def update(self, dt, platforms):
        if not self.alive:
            self.vel.y += GRAVITY * 60 * dt
            self.pos.y += self.vel.y * dt
            self.rect.y = int(self.pos.y)
            if self.rect.top > HEIGHT + 500:
                self.kill()
            return
        
        self.vel.x = self.speed * self.direction * dt
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)

        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel.x > 0: self.rect.right = p.rect.left
                else: self.rect.left = p.rect.right
                self.pos.x = self.rect.x
                self.direction *= -1
                break
        
        ground_probe_rect = pygame.Rect(self.rect.centerx + (self.direction * self.rect.width / 2), self.rect.bottom, 4, 10)
        on_edge = not any(p.rect.colliderect(ground_probe_rect) for p in platforms)
        if on_edge:
            self.direction *= -1

        self.vel.y += GRAVITY
        self.vel.y = clamp(self.vel.y, -MAX_FALL_SPEED, MAX_FALL_SPEED)
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False

        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel.y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0
                self.pos.y = self.rect.y
                break


class Player(Entity):
    """The player character."""
    def __init__(self, x, y):
        super().__init__(x, y, TILE - 10, TILE - 8)
        self.spawn_pos = pygame.Vector2(x, y)
        self.speed = 200.0
        self.run_multiplier = 1.6
        self.jump_power = 14.0
        self.lives = 3
        self.coins = 0
        self.facing_right = True
        
        self.skin_color = (60, 120, 250)
        self.trail_effect_color = WHITE
        
        self.can_double_jump = True
        
        self.invincible = False
        self.invincible_timer = 0.0
        self.hurt_flash_timer = 0.0

        self.power_timers = {"speed": 0.0, "jump": 0.0, "star": 0.0}
        self.trail_cooldown = 0.0
        self.draw_player()

    def draw_player(self):
        w, h = self.rect.size
        self.image.fill((0,0,0,0))
        
        light_color = (min(255, self.skin_color[0] + 100), min(255, self.skin_color[1] + 80), min(255, self.skin_color[2] + 5))
        pygame.draw.rect(self.image, self.skin_color, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(self.image, light_color, (4, 4, w-8, h-8), border_radius=6)
        
        eye_x = int(w * 0.65) if self.facing_right else int(w * 0.35)
        pygame.draw.circle(self.image, BLACK, (eye_x, int(h * 0.35)), 4)

    def update(self, dt, keys, platforms, particles):
        self._handle_input(dt, keys)
        self._apply_movement(dt, platforms)
        self._update_timers(dt)
        self._update_effects(dt, particles)

    def _handle_input(self, dt, keys):
        move_intent = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_intent -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_intent += 1
        
        if move_intent != 0:
            if (move_intent > 0) != self.facing_right:
                self.facing_right = move_intent > 0
                self.draw_player()

        is_running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        speed_mod = self.run_multiplier if is_running else 1.0
        if self.power_timers["speed"] > 0: speed_mod *= 1.5
        
        target_vel_x = self.speed * speed_mod * move_intent
        
        self.vel.x += (target_vel_x - self.vel.x) * 15 * dt

        friction = FRICTION if self.on_ground else AIR_FRICTION
        if abs(self.vel.x) < 0.1: self.vel.x = 0
        if move_intent == 0:
            self.vel.x *= (1 - friction) ** (dt * 60)

    def process_jump(self, keys, particles):
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        if jump_pressed:
            jump_mod = 1.35 if self.power_timers["jump"] > 0 else 1.0
            if self.on_ground:
                self.vel.y = -self.jump_power * jump_mod
                self.on_ground = False
                self._spawn_jump_particles(particles, self.trail_effect_color)
            elif self.can_double_jump:
                self.vel.y = -self.jump_power * 0.8 * jump_mod
                self.can_double_jump = False
                self._spawn_jump_particles(particles, self.trail_effect_color)
    
    def handle_jump_release(self, keys):
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        if not jump_pressed and self.vel.y < -3:
            self.vel.y = -3
            
    def _apply_movement(self, dt, platforms):
        self.vel.y += GRAVITY
        self.vel.y = clamp(self.vel.y, -MAX_FALL_SPEED * 2, MAX_FALL_SPEED)

        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel.x > 0: self.rect.right = p.rect.left
                else: self.rect.left = p.rect.right
                self.pos.x = self.rect.x
                self.vel.x = 0

        self.pos.y += self.vel.y
        self.rect.y = round(self.pos.y)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel.y > 0:
                    self.rect.bottom = p.rect.top
                    self.on_ground = True
                    self.can_double_jump = True
                    self.vel.y = 0
                elif self.vel.y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0
                self.pos.y = self.rect.y

    def _update_timers(self, dt):
        if self.invincible:
            self.invincible_timer -= dt
            self.hurt_flash_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False

        for k in self.power_timers:
            if self.power_timers[k] > 0:
                self.power_timers[k] -= dt
        
        if self.power_timers["star"] > 0:
            self.invincible = True
            self.invincible_timer = max(self.invincible_timer, self.power_timers["star"])

    def _update_effects(self, dt, particles):
        self.trail_cooldown -= dt
        is_star_power = self.power_timers["star"] > 0
        if is_star_power and self.trail_cooldown <= 0:
            vel = (random.uniform(-10, 10), random.uniform(-10, 0))
            particles.append(Particle(self.rect.center, vel, random.randint(3, 5), 0.3, SILVER))
            self.trail_cooldown = 0.03
        elif not is_star_power and abs(self.vel.x) > 100 and self.on_ground and self.trail_cooldown <= 0:
            vel = (random.uniform(-10, 10), random.uniform(-20, -10))
            particles.append(Particle(self.rect.midbottom, vel, random.randint(2, 4), 0.2, self.trail_effect_color))
            self.trail_cooldown = 0.05

    def hurt(self):
        if self.invincible: return False
        
        self.lives -= 1
        self.invincible = True
        self.invincible_timer = 1.5
        self.hurt_flash_timer = 1.5
        self.vel.y = -8
        
        self.vel.x = -150 if self.facing_right else 150
        
        return True
    
    def apply_powerup(self, kind):
        durations = {"speed": 8.0, "jump": 8.0, "star": 6.0}
        self.power_timers[kind] = durations.get(kind, 0)

    def respawn(self):
        self.pos = self.spawn_pos.copy()
        self.rect.topleft = self.pos
        self.vel.xy = (0, 0)
        self.lives -=1
        
        self.invincible = True
        self.invincible_timer = 2.0
        self.hurt_flash_timer = 2.0

    def _spawn_jump_particles(self, particles, color):
        for _ in range(8):
            vel = (random.uniform(-80, 80), random.uniform(-160, -60))
            particles.append(Particle(self.rect.midbottom, vel, random.randint(2,4), 0.4, color))
            
    def is_visible(self):
        """Determines if the player should be drawn, for flashing effect."""
        return self.hurt_flash_timer <= 0 or int(self.hurt_flash_timer * 10) % 2 == 0

class Flag(Entity):
    """The level-end flag."""
    def __init__(self, x, y):
        super().__init__(x, y - TILE, TILE, TILE * 2)
        self.image.fill((0,0,0,0))
        pole_rect = pygame.Rect(self.rect.w//2 - 3, 0, 6, self.rect.h)
        pygame.draw.rect(self.image, (200, 200, 200), pole_rect)
        flag_points = [(pole_rect.centerx, 10), (self.rect.w - 5, 25), (pole_rect.centerx, 40)]
        pygame.draw.polygon(self.image, RED, flag_points)

# --- NEW FEATURE: WarpFlag Class ---
class WarpFlag(Entity):
    """A flag that warps the player to a specific level."""
    def __init__(self, x, y, destination_level):
        super().__init__(x, y - TILE, TILE, TILE * 2)
        self.destination_level = destination_level
        self.image.fill((0, 0, 0, 0))
        pole_rect = pygame.Rect(self.rect.w // 2 - 3, 0, 6, self.rect.h)
        pygame.draw.rect(self.image, (200, 200, 200), pole_rect)
        # Use a different color to distinguish it from the regular flag
        flag_points = [(pole_rect.centerx, 10), (self.rect.w - 5, 25), (pole_rect.centerx, 40)]
        pygame.draw.polygon(self.image, BLUE, flag_points)

# ------------------------- Level Data & Loading -------------------------
LEVELS = [
    
    [ # Level 0 - Added a secret warp flag '6'
        "I.......................................................................................",
        "I.......................................................................................",
        "I.......................................................................................",
        "I..IIIIIIIIIIIIIIIXIIIIIIIIII...........................................................",
        "I.I...............X.....................................................................",
        "I.................X.....................................................................",
        "II................X.....................................................................",
        "I.I...............X.....................................................................",
        "I..I...S.......2..X...........CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC..F....",
        "XXXXXXXXXXXXXXXXXXX..........XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    ],
    [ # Level 1 (Secret/Bonus Level)
        "I.......................................................................................",
        "........................................................................................",
        "...IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII........",
        "........................................................................................",
        "........................................................................................",
        "I.......................................................................................",
        "I.....................................................................................",
        "I.......................................................................................",
        "I....S........C....C...CC.........................................................4....",
        "XXXXXXXXXX....X....X...XX..XX....X..XXX....XX..XX....XX....XXX....XXX....XX....XXXXXXX",
    ],
    [ # Level 2
        "........................................................................................",
        "........................................................................................",
        "........................................................................................",
        "..............................C.......C......................C..........................",
        "...............C...................................E....................................",
        "..............XXX...............XXXX........................XXXXX.......................",
        "...........X................C......................................X........C...........",
        "..........X..E.................XXXXXX.............C....................E.................",
        ".......S............C..............................................XXXXXXX..........F...",
        "XXXXXXXXXXXXXXXXXXXXXXXXX..XXXXXXX..XXXXXXXXX..XXXXXXXXXXX..XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    ],
    [ # Level 3
        "........................................................................................",
        "........................................................................................",
        "........................................................................................",
        ".........................C...............C...................C..........................",
        "...............C......................X............E....................................",
        "..............XXXXXXX...X.......XXXX........................XXXXX.......................",
        ".......................X....C...............................................C...........",
        ".............E........X........XXXXXX.............C....................E.................",
        ".......S............C..............................................XXXXXXX..........F...",
        "XXXXXXXXXXXXXXXXXXXXXXXXX...XXXXXX..XXXXXXXXX..XXXXXXXXXXX..XXXXXXXXXXXX..XXXXXXXXXXXXXX",
    ],
    [ # Level 4
        "........................................................................................",
        "........................................................................................",
        "........................................................................................",
        "................C...........E......................C.E..............E..................",
        "...............XXX..................................XXX..................................",
        "............X..........................................X.....C..........................",
        ".............E..C........................C..............E...........E....................",
        "..............XXXX.........XXXX........................XXXX..............................",
        ".......S....................C.............E.............E........................E....F.",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...XXXXXXXXXXXXX...XXXXXXXXXXXXXX...XXXXXXXXXXXX..XXXXXXXX",
    ],
    [ # Level 5
        "........................................................................................",
        "........................................................................................",
        "........................................................................................",
        ".......................................................................................",
        "........................................................................................",
        "........................................................................................",
        "...........C.E...........................C...............................................",
        "...........X..........C................X...........E............CE.......................",
        ".......S....................C.......C.....E.............E............C....ECE.E.E....F.",
        "XXXXXXXXXXXXXXXX...XXXXXXXX...XXXXXXXXXX..X..XXXXXXXXXXXXX..X..XXX...X...XXXXXXXXXXXXXXXX",
    ],
    [ # Level 6
        "........................................................................................",
        "........................................................................................",
        "...........................................................................C............",
        "...........................................................................X..C........",
        ".........................................................................C.....C........",
        ".........................................................................X......C.......",
        "...........C.E...........................C.............................C.........C.......",
        "......................C............................E............CE.....X..........C......",
        ".......S....................C.......C.....E.............E............C.............C.F.",
        "XXXXXXXXXXXXXXXX....X....XX...XXXXXXXX....X....XXXXXXXXXXX..X..XXX...X.............XXXXXX",
    ],
    
]


class Level:
    """Manages all the objects in a level."""
    def __init__(self, level_data):
        self.platforms = pygame.sprite.Group()
        self.jumppads = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.flag = None
        self.warp_flags = pygame.sprite.Group() # --- NEW: Group for warp flags
        self.player_spawn = pygame.Vector2(100, 100)
        
        self.width = len(level_data[0]) * TILE
        self.height = len(level_data) * TILE
        
        self._generate(level_data)
        
    def _generate(self, level_data):
        for y, row in enumerate(level_data):
            for x, char in enumerate(row):
                wx, wy = x * TILE, y * TILE
                if char == 'X':
                    is_top_platform = y > 0 and x < len(level_data[y-1]) and level_data[y-1][x] == '.'
                    if is_top_platform and random.random() < 0.06:
                        pad = JumpPad(wx, wy)
                        self.jumppads.add(pad)
                        self.platforms.add(pad)
                    else:
                        self.platforms.add(Platform(wx, wy))
                elif char == 'I':
                    self.platforms.add(InvisibleBlock(wx, wy))
                elif char == 'E':
                    self.enemies.add(Enemy(wx + 4, wy + 4))
                elif char == 'C':
                    self.coins.add(Coin(wx + TILE//4, wy + TILE//4))
                elif char == 'S':
                    self.player_spawn = pygame.Vector2(wx, wy)
                elif char == 'F':
                    self.flag = Flag(wx, wy)
                # --- NEW: Check for warp flag characters (digits) ---
                elif char.isdigit():
                    destination = int(char)
                    if 0 <= destination < len(LEVELS):
                        self.warp_flags.add(WarpFlag(wx, wy, destination))

        for coin in list(self.coins):
            if random.random() < 0.14:
                self.powerups.add(PowerUp(coin.rect.x, coin.rect.y))
                coin.kill()

# ------------------------- Shop Class -------------------------

class Shop:
    """Manages the in-game shop and items. Can change purchase prizes"""
    def __init__(self):
        self.active = False
        self.selection_index = 0
        self.items = [
            {"name": "Extra Life", "cost": 15, "type": "life"},
            {"name": "Red Skin", "cost": 0, "type": "skin", "color": RED},
            {"name": "White Skin", "cost": 0, "type": "skin", "color": WHITE},
            {"name": "Nigga Premium", "cost": 10, "type": "skin", "color": NIGGA},
            {"name": "Green Skin", "cost": 0, "type": "skin", "color": GREEN},
            {"name": "Purple Skin", "cost": 0, "type": "skin", "color": PURPLE},
            {"name": "Gold Skin", "cost": 5, "type": "skin", "color": GOLD},
            {"name": "Green Trail", "cost": 0, "type": "trail", "color": GREEN},
            {"name": "Orange Trail", "cost": 1, "type": "trail", "color": ORANGE},
            {"name": "Gold Trail", "cost": 1, "type": "trail", "color": GOLD},
        ]
        self.message = ""
        self.message_timer = 0.0

    def buy_item(self, player):
        """Attempts to buy the currently selected item."""
        if not self.items: return
        
        item = self.items[self.selection_index]
        cost = item["cost"]

        if player.coins >= cost:
            player.coins -= cost
            self._apply_item(player, item)
            self.show_message(f"Purchased {item['name']}!", 1.5)
        else:
            self.show_message("Not enough coins!", 1.5)

    def _apply_item(self, player, item):
        """Applies the purchased item's effect to the player."""
        item_type = item["type"]
        if item_type == "life":
            player.lives += 1
        elif item_type == "skin":
            player.skin_color = item["color"]
            player.draw_player()
        elif item_type == "trail":
            player.trail_effect_color = item["color"]
    
    def show_message(self, text, duration):
        self.message = text
        self.message_timer = duration
    
    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt

# ------------------------- Main Game Class -------------------------

class Game:
    """The main game controller."""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Platformer Adventure")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.font = pygame.font.SysFont("consolas", 22)
        self.big_font = pygame.font.SysFont("consolas", 48, bold=True)
        
        self.state = "menu"
        self.level_index = 0
        self.menu_selection = 0
        self.name_buffer = ""
        self.victory_time = 0.0
        
        self.shop = Shop()
        self.reset_game_state()

    def reset_game_state(self):
        """Initializes or resets all game-related variables."""
        self.level_data = Level(LEVELS[self.level_index])
        
        if hasattr(self, 'player'):
            p_lives = self.player.lives
            p_coins = self.player.coins
            p_skin = self.player.skin_color
            p_trail = self.player.trail_effect_color
        else:
            p_lives = 3
            p_coins = 0
            p_skin = BLUE
            p_trail = WHITE

        self.player = Player(self.level_data.player_spawn.x, self.level_data.player_spawn.y)
        self.player.lives = p_lives
        self.player.coins = p_coins
        self.player.skin_color = p_skin
        self.player.trail_effect_color = p_trail
        self.player.draw_player()
        
        self.camera = Camera()
        self.particles = []
        self.elapsed_time = 0.0
        self.paused = False

    def run(self):
        """The main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Processes all input events for the current game state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.state == "shop":
                self._handle_shop_events(event)
            elif self.state == "menu":
                self._handle_menu_events(event)
            elif self.state == "game":
                self._handle_game_events(event)
            elif self.state == "game_over" or self.state == "victory":
                self._handle_end_screen_events(event)
            elif self.state == "times":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def update(self, dt):
        """Updates game logic based on the current state."""
        if self.state == "shop":
            self.shop.update(dt)
        elif self.state == "game" and not self.paused:
            self._update_game(dt)
            
    def draw(self):
        """Draws everything to the screen based on the current state."""
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "game" or self.state == "shop":
            self._draw_game()
            if self.state == "shop":
                self._draw_shop_overlay()
        elif self.state == "game_over":
            self._draw_game()
            self._draw_game_over_overlay()
        elif self.state == "victory":
            self._draw_game()
            self._draw_victory_screen()
        elif self.state == "times":
            self._draw_times_screen()
            
    # --- State-Specific Handlers ---

    def _handle_shop_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                self.state = "game"
                self.paused = False # Unpause when leaving shop
            elif event.key == pygame.K_UP:
                self.shop.selection_index = (self.shop.selection_index - 1) % len(self.shop.items)
            elif event.key == pygame.K_DOWN:
                self.shop.selection_index = (self.shop.selection_index + 1) % len(self.shop.items)
            elif event.key == pygame.K_RETURN:
                self.shop.buy_item(self.player)

    def _handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selection = (self.menu_selection - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.menu_selection = (self.menu_selection + 1) % 3
            elif event.key == pygame.K_RETURN:
                if self.menu_selection == 0:
                    self.level_index = 0
                    if hasattr(self, 'player'):
                        self.player.lives = 3
                        self.player.coins = 0
                        self.player.skin_color = BLUE
                        self.player.trail_effect_color = WHITE
                    self.reset_game_state()
                    self.state = "game"
                elif self.menu_selection == 1:
                    self.state = "times"
                elif self.menu_selection == 2:
                    self.running = False

    def _handle_game_events(self, event):
        keys = pygame.key.get_pressed()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            elif event.key == pygame.K_p:
                self.state = "shop"
                self.paused = True
            else:
                self.player.process_jump(keys, self.particles)
        elif event.type == pygame.KEYUP:
            self.player.handle_jump_release(keys)

    def _handle_end_screen_events(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == "game_over":
                if event.key == pygame.K_r:
                    self.level_index = 0
                    if hasattr(self, 'player'):
                        self.player.lives = 3
                        self.player.coins = 0
                        self.player.skin_color = BLUE
                        self.player.trail_effect_color = WHITE
                    self.reset_game_state()
                    self.state = "game"
                elif event.key == pygame.K_q:
                    self.state = "menu"
            elif self.state == "victory":
                if event.key == pygame.K_RETURN and self.name_buffer:
                    with open("times.txt", "a") as f:
                        f.write(f"{self.name_buffer},{self.victory_time:.2f}\n")
                    self.state = "menu"
                    self.name_buffer = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.name_buffer = self.name_buffer[:-1]
                elif event.unicode.isprintable() and len(self.name_buffer) < 12:
                    self.name_buffer += event.unicode
                    
    def _update_game(self, dt):
        self.elapsed_time += dt
        
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.level_data.platforms, self.particles)
        
        self.level_data.enemies.update(dt, self.level_data.platforms)
        self.level_data.coins.update(dt)
        self.level_data.powerups.update(dt)
        
        self.particles[:] = [p for p in self.particles if p.update(dt)]
        
        self._check_collisions()
        
        if self.player.rect.top > self.level_data.height + 200:
            if self.player.lives > 1:
                self.player.respawn()
                self._spawn_particles(self.player.rect.center, ORANGE, 20)
            else:
                self.player.lives = 0
                self.state = "game_over"

        if self.level_data.flag and self.player.rect.colliderect(self.level_data.flag.rect):
            self._next_level()
        
        self.camera.update(self.player.rect, self.level_data.width, self.level_data.height)
        
    def _check_collisions(self):
        for enemy in pygame.sprite.spritecollide(self.player, self.level_data.enemies, False):
            if enemy.alive:
                is_stomp = self.player.vel.y > 1 and self.player.rect.bottom - enemy.rect.top < 20
                if is_stomp or self.player.power_timers["star"] > 0:
                    enemy.alive = False
                    enemy.vel.y = -8
                    self.player.vel.y = -8
                    self._spawn_particles(enemy.rect.center, RED, 15)
                else:
                    if self.player.hurt():
                        self._spawn_particles(self.player.rect.center, ORANGE, 20)
                        if self.player.lives <= 0:
                            self.state = "game_over"
        
        for pad in self.level_data.jumppads:
            if self.player.rect.colliderect(pad.rect) and self.player.vel.y > 0 and self.player.rect.bottom - pad.rect.top < 20:
                self.player.vel.y = -self.player.jump_power * 1.5
                self._spawn_particles(pad.rect.midtop, GREEN, 15)

        for coin in pygame.sprite.spritecollide(self.player, self.level_data.coins, True):
            self.player.coins += 1
            self._spawn_particles(coin.rect.center, GOLD, 12)
            
        for powerup in pygame.sprite.spritecollide(self.player, self.level_data.powerups, True):
            self.player.apply_powerup(powerup.kind)
            self._spawn_particles(powerup.rect.center, powerup.COLORS[powerup.kind], 15)

        # --- NEW: Check for warp flag collisions ---
        for flag in self.level_data.warp_flags:
            if self.player.rect.colliderect(flag.rect):
                self._spawn_particles(flag.rect.center, PURPLE, 30) # Warp particles
                self._warp_to_level(flag.destination_level)
                break # Essential to stop checks after warping
    
    def _next_level(self):
        self.level_index += 1
        if self.level_index < len(LEVELS):
            current_time = self.elapsed_time
            self.reset_game_state()
            self.elapsed_time = current_time
            self.state = "game"
        else:
            self.victory_time = self.elapsed_time
            self.state = "victory"

    # --- NEW: Method to handle warping to a specific level ---
    def _warp_to_level(self, level_idx):
        if 0 <= level_idx < len(LEVELS):
            self.level_index = level_idx
            current_time = self.elapsed_time
            self.reset_game_state() # This uses the new level_index to load the correct level
            self.elapsed_time = current_time
            self.state = "game"
        else:
            # Fallback in case of an invalid level index in the map
            print(f"Warning: Invalid warp destination '{level_idx}'.")
            self._next_level()


    def _draw_game(self):
        self._draw_parallax_background()
        
        for entity in self.level_data.platforms:
            self.screen.blit(entity.image, self.camera.apply(entity.rect))
        
        if self.level_data.flag:
            self.screen.blit(self.level_data.flag.image, self.camera.apply(self.level_data.flag.rect))
        
        # --- NEW: Draw the warp flags ---
        for warp_flag in self.level_data.warp_flags:
            self.screen.blit(warp_flag.image, self.camera.apply(warp_flag.rect))
        
        all_sprites = pygame.sprite.Group(self.level_data.coins, self.level_data.powerups, self.level_data.enemies)
        for entity in all_sprites:
            self.screen.blit(entity.image, self.camera.apply(entity.rect))

        if self.player.is_visible():
            self.screen.blit(self.player.image, self.camera.apply(self.player.rect))

        for p in self.particles:
            p.draw(self.screen, self.camera)
            
        if DEBUG_DRAW:
            pygame.draw.rect(self.screen, RED, self.camera.apply(self.player.rect), 1)
        
        self._draw_hud()
        
        if self.paused and self.state != "shop":
            self._draw_pause_overlay()

    def _draw_parallax_background(self):
        self.screen.fill(SKY)
        horizon = HEIGHT * 0.6
        for i in range(5):
            color = (SKY[0]-i*6, SKY[1]-i*8, SKY[2]-i*10)
            pygame.draw.rect(self.screen, color, (0, horizon + i*30, WIDTH, 30))
        
        for i in range(4):
            offset = (-self.camera.x * (0.1 + i * 0.05)) % (WIDTH + 400) - 200
            pygame.draw.ellipse(self.screen, (70+i*10, 180-i*10, 120), (offset, HEIGHT-220, 400, 180))

    def _draw_hud(self):
        pygame.draw.rect(self.screen, (0,0,0,100), (0,0,WIDTH,40))
        
        time_txt = self.font.render(f"TIME {self.elapsed_time:06.2f}", True, WHITE)
        coin_txt = self.font.render(f"COINS {self.player.coins:03d}", True, GOLD)
        life_txt = self.font.render(f"LIVES {self.player.lives}", True, WHITE)
        
        self.screen.blit(time_txt, (16, 8))
        self.screen.blit(coin_txt, (WIDTH//2 - coin_txt.get_width()//2, 8))
        self.screen.blit(life_txt, (WIDTH - life_txt.get_width() - 16, 8))

    def _draw_menu(self):
        self.screen.fill(BLACK)
        title = self.big_font.render("Platformer Adventure", True, GOLD)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        options = ["Start Game", "High Scores", "Quit"]
        for i, option in enumerate(options):
            color = GOLD if i == self.menu_selection else WHITE
            text = self.font.render(option, True, color)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + i * 40))

    def _draw_game_over_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.big_font.render("GAME OVER", True, RED)
        subtext = self.font.render("Press [R] to Restart or [Q] for Menu", True, WHITE)
        
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 40))
        self.screen.blit(subtext, (WIDTH//2 - subtext.get_width()//2, HEIGHT//2 + 20))
    

    def _draw_shop_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.big_font.render("SHOP", True, GOLD)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
        
        instr = self.font.render("Use UP/DOWN to select, ENTER to buy. Press P to close.", True, SILVER)
        self.screen.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT - 50))
        
        start_y = 120
        row_height = 40
        left_column_x = WIDTH // 2 - 300
        right_column_x = WIDTH // 2 + 40

        for i, item in enumerate(self.shop.items):
            is_selected = (i == self.shop.selection_index)
            can_afford = self.player.coins >= item['cost']

            color = GOLD if is_selected else WHITE
            if not can_afford:
                color = (120, 120, 120)
            
            row = i // 2
            column = i % 2

            current_y = start_y + row * row_height
            if column == 0:
                name_pos = (left_column_x, current_y)
                cost_pos = (left_column_x + 200, current_y)
            else:
                name_pos = (right_column_x, current_y)
                cost_pos = (right_column_x + 200, current_y)

            name_txt = self.font.render(item['name'], True, color)
            cost_txt = self.font.render(f"{item['cost']}", True, color)
            coin_icon_txt = self.font.render("c", True, GOLD if can_afford else (120, 120, 120))
            
            self.screen.blit(name_txt, name_pos)
            self.screen.blit(cost_txt, cost_pos)
            self.screen.blit(coin_icon_txt, (cost_pos[0] + cost_txt.get_width() + 5, cost_pos[1]))

        if self.shop.message_timer > 0:
            msg_txt = self.font.render(self.shop.message, True, WHITE)
            self.screen.blit(msg_txt, (WIDTH//2 - msg_txt.get_width()//2, HEIGHT - 90))

    def _draw_victory_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.big_font.render("VICTORY!", True, GOLD)
        time_txt = self.font.render(f"Final Time: {self.victory_time:.2f}s", True, WHITE)
        name_prompt = self.font.render(f"Enter Name: {self.name_buffer}_", True, WHITE)
        
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 60))
        self.screen.blit(time_txt, (WIDTH//2 - time_txt.get_width()//2, HEIGHT//2))
        self.screen.blit(name_prompt, (WIDTH//2 - name_prompt.get_width()//2, HEIGHT//2 + 40))

    def _draw_times_screen(self):
        self.screen.fill(BLACK)
        title = self.big_font.render("High Scores", True, GOLD)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        try:
            with open("times.txt", "r") as f:
                scores = [line.strip().split(',') for line in f if ',' in line]
                scores.sort(key=lambda x: float(x[1]))
            for i, (name, time) in enumerate(scores[:10]):
                entry = self.font.render(f"{i+1:2}. {name:<12} - {time}s", True, WHITE)
                self.screen.blit(entry, (WIDTH//2 - entry.get_width()//2, 150 + i*30))
        except (FileNotFoundError, IndexError):
            msg = self.font.render("No scores recorded yet.", True, WHITE)
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
            
        back_msg = self.font.render("Press [ESC] to return to menu", True, SILVER)
        self.screen.blit(back_msg, (WIDTH // 2 - back_msg.get_width() // 2, HEIGHT - 50))
    
    def _draw_pause_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        text = self.big_font.render("PAUSED", True, WHITE)
        self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
        
    def _spawn_particles(self, pos, color, count):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 200)
            vel = (math.cos(angle) * speed, math.sin(angle) * speed)
            self.particles.append(Particle(pos, vel, random.randint(2, 5), 0.6, color))


if __name__ == '__main__':
    game = Game()
    game.run()