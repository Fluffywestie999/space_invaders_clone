import pygame
import random
import numpy as np  # For pixel array operations if needed later

# Initialize Pygame and the mixer
pygame.init()
pygame.mixer.init()

# Load sounds
shoot_sound = pygame.mixer.Sound("assets/shoot.wav")
explosion_sound = pygame.mixer.Sound("assets/explosion.wav")
player_death_sound = pygame.mixer.Sound("assets/playerdeath.wav")
ufo_sound = pygame.mixer.Sound("assets/ufo.wav")  # New UFO sound

# Screen dimensions and setup
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders Clone")

# Load and scale the background image
background = pygame.image.load("assets/invaders.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Define some colors
WHITE = (255, 255, 255)
RED   = (255, 0, 0)

# Enemy formation parameters
enemy_rows = 3
enemy_cols = 10
enemy_spacing_x = 60
enemy_spacing_y = 60
enemy_offset_x = 50
enemy_offset_y = 50

# Preload the alien death image and process transparency.
alien_death_image = pygame.image.load("assets/aliendeath.png").convert()
alien_death_image.set_colorkey((0, 0, 0))
alien_death_image = pygame.transform.scale(alien_death_image, (40, 40)).convert_alpha()

# ------------------------
# Define UFO spawn event.
# ------------------------
UFO_SPAWN_EVENT = pygame.USEREVENT + 2
# Set the UFO spawn timer to fire every 15000 ms (15 seconds)
pygame.time.set_timer(UFO_SPAWN_EVENT, 15000)

# Global variables for waves and win condition.
wave = 1
win = False

# ------------------------
# Define the Shield class.
# ------------------------
class Shield(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        raw_image = pygame.image.load("assets/shield.png").convert()
        raw_image.set_colorkey((0, 0, 0))
        # Scale the shield to 80x40; adjust as needed.
        self.image = pygame.transform.scale(raw_image, (80, 40)).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))

# (For now, shield collision/degradation code is removed.)

# ------------------------
# Define the Player class.
# ------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        raw_image = pygame.image.load("assets/player.png").convert()
        raw_image.set_colorkey((0, 0, 0))
        # Scale to 64x32 (reducing height by 50%)
        self.image = pygame.transform.scale(raw_image, (64, 32)).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10)
        self.speed = 5

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

# ------------------------
# Define the Enemy class.
# ------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=1.125):  # Starting speed reduced by 25%
        super().__init__()
        frame1 = pygame.image.load("assets/alien1.png").convert()
        frame1.set_colorkey((0, 0, 0))
        frame1 = pygame.transform.scale(frame1, (40, 40)).convert_alpha()
        frame2 = pygame.image.load("assets/alien2.png").convert()
        frame2.set_colorkey((0, 0, 0))
        frame2 = pygame.transform.scale(frame2, (40, 40)).convert_alpha()
        self.frames = [frame1, frame2]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.last_update = pygame.time.get_ticks()
        self.dying = False
        self.death_time = 0

    def update(self):
        if self.dying:
            if pygame.time.get_ticks() - self.death_time >= 500:
                self.kill()
            return
        self.rect.x += self.speed
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= 1000:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.last_update = current_time

# ------------------------
# Define the UFO class.
# ------------------------
class UFO(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            raw_image = pygame.image.load("assets/ufo.png").convert()
        except Exception as e:
            print("Error loading UFO sprite:", e)
            raw_image = pygame.Surface((60, 30))
            raw_image.fill(WHITE)
        raw_image.set_colorkey((0, 0, 0))
        self.image = pygame.transform.scale(raw_image, (60, 30)).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = 40
        self.x = float(self.rect.x)
        total_distance = SCREEN_WIDTH + self.rect.width
        self.speed = -total_distance / 600  # UFO crosses screen in ~10 seconds.
        self.dying = False
        self.death_time = 0
        # Get a free channel and play the UFO sound on loop.
        self.ufo_channel = pygame.mixer.find_channel()
        if self.ufo_channel:
            self.ufo_channel.play(ufo_sound, loops=-1)

    def update(self):
        if self.dying:
            if pygame.time.get_ticks() - self.death_time >= 500:
                if self.ufo_channel:
                    self.ufo_channel.stop()
                self.kill()
            return
        self.x += self.speed
        self.rect.x = int(self.x)
        if self.rect.right < 0:
            if self.ufo_channel:
                self.ufo_channel.stop()
            self.kill()

# ------------------------
# Define the Player Bullet class.
# ------------------------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = -10  # Moves upward.

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

# ------------------------
# Define the Enemy Bullet class.
# ------------------------
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 5  # Moves downward.

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# ------------------------
# Set up sprite groups.
# ------------------------
all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy_bullet_group = pygame.sprite.Group()
ufo_group = pygame.sprite.Group()   # Group for UFO
shield_group = pygame.sprite.Group()  # Group for shields

# Create the player and add to groups.
player = Player()
all_sprites.add(player)
player_group.add(player)

# Function to create the enemy formation.
def create_enemy_formation():
    for row in range(enemy_rows):
        for col in range(enemy_cols):
            x = enemy_offset_x + col * enemy_spacing_x
            y = enemy_offset_y + row * enemy_spacing_y
            enemy = Enemy(x, y)
            all_sprites.add(enemy)
            enemy_group.add(enemy)

create_enemy_formation()

# Spawn 3 shields evenly distributed above the player.
shield_y = SCREEN_HEIGHT - 100  # Adjust vertical position as needed.
shield_positions = [SCREEN_WIDTH * 0.25, SCREEN_WIDTH * 0.5, SCREEN_WIDTH * 0.75]
for x in shield_positions:
    shield = Shield(x, shield_y)
    shield_group.add(shield)
    all_sprites.add(shield)

score = 0
font = pygame.font.Font(None, 36)

# Timer event for enemy shooting.
ENEMY_SHOOT_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_SHOOT_EVENT, 3000)  # Every 3 seconds

# ------------------------
# Helper function to handle player death.
# ------------------------
def handle_player_death():
    global running
    print("Game Over!")
    raw_death = pygame.image.load("assets/playerdeath.png").convert()
    raw_death.set_colorkey((0, 0, 0))
    death_sprite = pygame.transform.scale(raw_death, (64, 64)).convert_alpha()
    player.image = death_sprite
    screen.blit(background, (0, 0))
    all_sprites.draw(screen)
    score_text = font.render("Score: " + str(score), True, WHITE)
    screen.blit(score_text, (10, 10))
    wave_text = font.render("Wave: " + str(wave), True, WHITE)
    screen.blit(wave_text, (SCREEN_WIDTH - wave_text.get_width() - 10, 10))
    pygame.display.flip()
    player_death_sound.play()
    pygame.time.wait(1000)
    player.kill()
    running = False

# ------------------------
# Main Game Loop.
# ------------------------
running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)  # Limit to 60 FPS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Player fires a bullet.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if len(bullet_group) < 1:
                    bullet = Bullet(player.rect.centerx, player.rect.top)
                    all_sprites.add(bullet)
                    bullet_group.add(bullet)
                    shoot_sound.play()

        # Enemy shooting event.
        if event.type == ENEMY_SHOOT_EVENT:
            max_enemy_bullets = min(wave, 5)
            while len(enemy_bullet_group) < max_enemy_bullets and len(enemy_group) > 0:
                enemy = random.choice(enemy_group.sprites())
                enemy_bullet = EnemyBullet(enemy.rect.centerx, enemy.rect.bottom)
                all_sprites.add(enemy_bullet)
                enemy_bullet_group.add(enemy_bullet)

        # UFO spawn event.
        if event.type == UFO_SPAWN_EVENT:
            if len(ufo_group) == 0:
                ufo = UFO()
                all_sprites.add(ufo)
                ufo_group.add(ufo)

    keys = pygame.key.get_pressed()
    player.update(keys)
    bullet_group.update()
    enemy_bullet_group.update()
    enemy_group.update()
    ufo_group.update()

    # Process enemy movement.
    edge_reached = any(enemy.rect.left <= 0 or enemy.rect.right >= SCREEN_WIDTH for enemy in enemy_group)
    if edge_reached:
        for enemy in enemy_group:
            enemy.speed = -enemy.speed * 1.1
            enemy.rect.y += 20

    pygame.sprite.groupcollide(enemy_bullet_group, bullet_group, True, True)
    enemy_hits = pygame.sprite.groupcollide(bullet_group, enemy_group, True, False)
    if enemy_hits:
        for bullet, enemies in enemy_hits.items():
            for enemy in enemies:
                if not enemy.dying:
                    enemy.dying = True
                    enemy.death_time = pygame.time.get_ticks()
                    enemy.image = alien_death_image
                    score += 1
        explosion_sound.play()

    ufo_hits = pygame.sprite.groupcollide(bullet_group, ufo_group, True, False)
    if ufo_hits:
        for bullet, ufos in ufo_hits.items():
            for ufo in ufos:
                if not ufo.dying:
                    ufo.dying = True
                    ufo.death_time = pygame.time.get_ticks()
                    ufo.image = alien_death_image
                    score += 10
        explosion_sound.play()

    if pygame.sprite.spritecollideany(player, enemy_bullet_group):
        handle_player_death()

    for enemy in enemy_group:
        if enemy.rect.bottom >= SCREEN_HEIGHT:
            handle_player_death()
            break

    if pygame.sprite.spritecollideany(player, enemy_group):
        handle_player_death()

    if len(enemy_group) == 0:
        wave += 1
        if wave > 99:
            win = True
            running = False
        else:
            create_enemy_formation()

    screen.blit(background, (0, 0))
    all_sprites.draw(screen)
    score_text = font.render("Score: " + str(score), True, WHITE)
    screen.blit(score_text, (10, 10))
    wave_text = font.render("Wave: " + str(wave), True, WHITE)
    screen.blit(wave_text, (SCREEN_WIDTH - wave_text.get_width() - 10, 10))
    pygame.display.flip()

if win:
    screen.fill((0, 0, 0))
    win_text = font.render("You have won!", True, WHITE)
    screen.blit(win_text, ((SCREEN_WIDTH - win_text.get_width()) // 2,
                           (SCREEN_HEIGHT - win_text.get_height()) // 2))
    pygame.display.flip()
    pygame.time.wait(3000)

pygame.quit()
