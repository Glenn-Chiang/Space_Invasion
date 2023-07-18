import pygame
from sys import exit
import random
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))
pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 600, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Space Invasion')
clock = pygame.time.Clock()

RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,150,255)
BLACK = (0,0,0)
WHITE = (255,255,255)

# HUD font
hud_font = pygame.font.SysFont('consolas', 20)
hud_font_large = pygame.font.SysFont('consolas', 60)


class Player():
    # Player specs
    width, height = 80, 80 
    # Player.body represents the player's position and dimensions; it is the 'hitbox' of the player used in the game's calculations
    body = pygame.Rect(SCREEN_WIDTH//2 - width//2, SCREEN_HEIGHT - height - 10, width, height)
    image = pygame.image.load(r'assets\images\player_ship.png')
    sprite = pygame.transform.scale(image, (width, height))
    move_speed = 8
    
    max_health = 10
    healthbar_width = 5

    heal_sound = pygame.mixer.Sound(r'assets\sounds\heal_sound.wav')
    death_sound = pygame.mixer.Sound(r'assets\sounds\player_death_sound.wav')
    take_damage_sound = pygame.mixer.Sound(r'assets\sounds\take_damage_sound.mp3')
    
    def __init__(self):
        self.health = self.max_health
        self.healthbar_length = (self.health//self.max_health) * self.width
        self.healthbar = pygame.Rect(self.body.x, self.body.y + self.height + 2, self.healthbar_length, self.healthbar_width)
        self.damage_bar = pygame.Rect(self.body.x, self.body.y + self.height + 2, self.width, self.healthbar_width)

        self.kills = 0
        self.bullets = []
        self.powers = {}

        # Bullet specs
        self.bullet_width, self.bullet_length = 4, 8
        self.bullet_speed = 10    
        self.fire_rate = 5 # Player can only fire max 10 bullets on screen
        self.bullet_damage = 1
        self.bullet_fire_sound = pygame.mixer.Sound(r'assets\sounds\player_gunfire.mp3')
        self.powerup_sound = pygame.mixer.Sound(r'assets\sounds\powerup_sound.wav')

        # Laser specs
        self.laser_width, self.laser_length = 2, SCREEN_HEIGHT
        self.laser = pygame.Rect(self.body.x + self.width//2, self.body.y - SCREEN_HEIGHT, self.laser_width, self.laser_length)
        self.laser_damage = 10
        self.laser_fire_sound = pygame.mixer.Sound(r'assets\sounds\laser_sound.wav')
        self.laser_equipped = False

    # Player movement
    def move(self, key):
        if key[pygame.K_LEFT] and self.body.x - self.move_speed > 0:
            self.body.x -= self.move_speed
            self.healthbar.x -= self.move_speed
            self.damage_bar.x -= self.move_speed
        if key[pygame.K_RIGHT] and self.body.x + self.width + self.move_speed < SCREEN_WIDTH:
            self.body.x += self.move_speed
            self.healthbar.x += self.move_speed
            self.damage_bar.x += self.move_speed
        if key[pygame.K_UP] and self.body.y - self.move_speed > 0:
            self.body.y -= self.move_speed
            self.healthbar.y -= self.move_speed
            self.damage_bar.y -= self.move_speed
        if key[pygame.K_DOWN] and self.body.y + self.height + self.healthbar_width + self.move_speed < SCREEN_HEIGHT:
            self.body.y += self.move_speed
            self.healthbar.y += self.move_speed
            self.damage_bar.y += self.move_speed

    def fire_bullet(self):
        # Create new bullet every time player fires
        bullet = pygame.Rect(self.body.x + self.width//2, self.body.y, self.bullet_width, self.bullet_length)
        if len(self.bullets) < self.fire_rate:
            self.bullets.append(bullet)
            self.bullet_fire_sound.play()

    def handle_bullets(self, enemies):
        for bullet in self.bullets:
            bullet.y -= self.bullet_speed

            # Bullet goes offscreen
            if bullet.y < 0:
                self.bullets.remove(bullet)
                break

            # Bullet hits an enemy
            for enemy in enemies:
                if bullet.colliderect(enemy.body):
                    self.bullets.remove(bullet)
                    enemy.take_damage(self.bullet_damage)
                    break    

    def equip_laser(self):
        self.laser_equipped = True
        self.powers['Laser'] = 10 # Laser has 10 uses before being depleted
        self.powerup_sound.play()

    def fire_laser(self):
        self.laser = pygame.Rect(self.body.x + self.width//2, self.body.y - SCREEN_HEIGHT, self.laser_width, self.laser_length)
        self.laser_fire_sound.play()
        self.powers['Laser'] -= 1 # Use up 1 use of laser
        if self.powers['Laser'] == 0:
            self.laser_equipped = False

    def handle_laser(self, enemies):
        for enemy in enemies:
            if self.laser.colliderect(enemy.body):
                enemy.take_damage(self.laser_damage)

    def take_damage(self, damage):
        if self.health - damage >= 0:
            self.health -= damage
        else:
            self.health = 0
        
        self.healthbar_length = (self.health/self.max_health) * self.width
        self.healthbar = pygame.Rect(self.body.x, self.body.y + self.height + 2, self.healthbar_length, self.healthbar_width)
        self.take_damage_sound.play()

    def heal(self, hp):
        if self.health + hp <= self.max_health:
            self.health += hp
        else:
            self.health = self.max_health
        
        self.heal_sound.play()
        self.healthbar_length = (self.health/self.max_health) * self.width
        self.healthbar = pygame.Rect(self.body.x, self.body.y + self.height + 2, self.healthbar_length, self.healthbar_width)
    
    def damage_up(self):
        self.bullet_damage += 1
        self.laser_damage += 5
        self.powerup_sound.play()
        self.powers['Damage up'] = self.powers.get('Damage up', 0) + 1


class Enemy():

    max_health = 10
    move_speed = 5
    fire_rate = 2 # Fire once every {fire_rate} seconds
    bullet_speed = 6 
    level_up_sound = pygame.mixer.Sound(r'assets\sounds\level_up_sound.wav')

    @classmethod
    def leveL_reset(cls):
        cls.max_health = 10
        cls.move_speed = 5
        cls.fire_rate = 2
        cls.bullet_speed = 6

    @classmethod
    def level_up(cls):
        cls.max_health *= 1.1
        cls.move_speed *= 1.2
        if cls.fire_rate > 0.6:
            cls.fire_rate -= 0.2
        cls.bullet_speed *= 1.1
        cls.level_up_sound.play()

    def __init__(self, type, spawn_point):
        self.type = type
        self.spawn_point = spawn_point
        
        if self.type == 'red':
            self.width, self.height = 60, 60
            self.image = pygame.image.load(r'assets\images\pixel_ship_red_small.png')
            
            self.max_health = 0.4 * self.__class__.max_health
            self.health = self.max_health
            self.move_speed = 0.3 * self.__class__.move_speed
            self.bullets = []
            self.fire_rate = 1.4 * self.__class__.fire_rate
            self.bullet_damage = 1
            self.bullet_width, self.bullet_length = 5, 10

        if self.type == 'green':
            self.width, self.height = 50, 50
            self.image = pygame.image.load(r'assets\images\pixel_ship_green_small.png')
            
            self.max_health = 0.2 * self.__class__.max_health
            self.health = self.max_health
            self.move_speed = 0.5 * self.__class__.move_speed
            self.bullets = []
            self.bullet_speed = 0
            self.bullet_damage = 0
            self.bullet_width, self.bullet_length = 0, 0

        if self.type == 'elite':
            self.width, self.height = 80, 80
            self.image = pygame.image.load(r'assets\images\elite_enemy.png')

            self.max_health = 1 * self.__class__.max_health
            self.health = self.max_health
            self.move_speed = 0.2 * self.__class__.move_speed
            self.bullets = []
            self.fire_rate = 1 * self.__class__.fire_rate
            self.bullet_damage = 2
            self.bullet_width, self.bullet_length = 10, 20

        self.sprite = pygame.transform.scale(self.image, (self.width, self.height))
        self.body = pygame.Rect(self.spawn_point[0], self.spawn_point[1], self.width, self.height)

    def move(self):
        self.body.y += self.move_speed

    def fire(self):
        bullet = pygame.Rect(self.body.x + self.width//2, self.body.y + self.height, self.bullet_width, self.bullet_length)
        self.bullets.append(bullet)
        #self.fire_sound.play()
        
    def handle_bullets(self, player):
        for bullet in self.bullets:
            bullet.y += self.bullet_speed

            # Bullet goes offscreen
            if bullet.y > SCREEN_HEIGHT:
                self.bullets.remove(bullet)
                return

            # Bullet hits player
            if bullet.colliderect(player.body):
                self.bullets.remove(bullet)
                player.take_damage(self.bullet_damage)
                return

    def take_damage(self, damage):
        self.health -= damage

    destroyed_sound = pygame.mixer.Sound(r'assets\sounds\enemy_destroyed.mp3')


class Powerup():
    move_speed = 4
    width, height = 40, 40

    def __init__(self, type, spawn_point):
        self.type = type
        self.spawn_point = spawn_point

        if self.type == 'health':
            self.image = pygame.image.load(r'assets\images\health_pickup.png')
        
        if self.type == 'max_health':
            self.image = pygame.image.load(r'assets\images\max_health_pickup.png')

        if self.type == 'damage':
            self.image = pygame.image.load(r'assets\images\damage_pickup.png')

        if self.type == 'laser':
            self.image = pygame.image.load(r'assets\images\laser_pickup.png')

        self.sprite = pygame.transform.scale(self.image, (self.width, self.height))
        self.body = pygame.Rect(self.spawn_point[0], self.spawn_point[1], self.width, self.height)
    
    def move(self):
        self.body.y += self.move_speed


def display_menu():
    screen.fill(BLACK)

    # Draw title
    title_text = hud_font_large.render('SPACE INVASION', 1, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2,
                             SCREEN_HEIGHT//2 - title_text.get_height()//2))

    # Draw prompt
    prompt_text = hud_font.render('Press [SPACE] to start', 1, WHITE)
    screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2,
                              SCREEN_HEIGHT//2 + title_text.get_height()//2))
    pygame.display.update()


def display_game(player, enemies, powerups, level):
    screen.fill(BLACK)

    # Draw player and healthbar
    # Healthbar moves together with player body
    screen.blit(player.sprite, (player.body.x, player.body.y))
    pygame.draw.rect(screen, RED, player.damage_bar)
    pygame.draw.rect(screen, GREEN, player.healthbar)

    # Draw player bullets
    for bullet in player.bullets:
        pygame.draw.rect(screen, BLUE, bullet)

    # Draw laser (if equipped)
    # Laser only appears when fired
    if player.laser_equipped:
        pygame.draw.rect(screen, BLUE, player.laser)

    # Draw enemies
    for enemy in enemies:
        screen.blit(enemy.sprite, (enemy.body.x, enemy.body.y))

        # Draw enemy bullets
        for bullet in enemy.bullets:
            pygame.draw.rect(screen, RED, bullet)

    # Draw powerups
    for powerup in powerups:
        screen.blit(powerup.sprite, (powerup.body.x, powerup.body.y))

    # Draw HUD
    health_text = hud_font.render(f'HP: {player.health}/{player.max_health}', 1, WHITE)
    kills_text = hud_font.render(f'KILLS: {player.kills}', 1, WHITE)
    powers_text = 'POWERS:\n' + '\n'.join([f'{power}: +{amt}' for power, amt in player.powers.items()])
    powers_text = hud_font.render(powers_text, 1, WHITE)
    leveL_text = hud_font.render(f'LVL: {level}', 1, WHITE)
    
    screen.blit(health_text, (10,SCREEN_HEIGHT-40))
    screen.blit(kills_text, (10,SCREEN_HEIGHT-20))   
    screen.blit(powers_text, (SCREEN_WIDTH - powers_text.get_width() - 20, SCREEN_HEIGHT - powers_text.get_height() - 20 ))
    screen.blit(leveL_text, (SCREEN_WIDTH - leveL_text.get_width() - 20, 10))

    pygame.display.update()


def display_game_over(player):
    game_over_text = hud_font_large.render('GAME OVER', 1, RED)
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 
                                 SCREEN_HEIGHT//2 - game_over_text.get_height()//2))
    kills_text = hud_font.render(f'KILLS: {player.kills}', 1, RED)
    screen.blit(kills_text, (SCREEN_WIDTH//2 - kills_text.get_width()//2, 
                            SCREEN_HEIGHT//2 + game_over_text.get_height()//2 + 20))
    pygame.display.update()
    pygame.time.delay(5000)


def run_game(level_up_timer, enemy_spawn_timer, powerup_spawn_timer):
    
    level_up_interval = 30 * 1000
    pygame.time.set_timer(level_up_timer, level_up_interval)

    enemy_spawn_interval = int(1.25 * 1000)
    powerup_spawn_interval = 10 * 1000
    pygame.time.set_timer(enemy_spawn_timer, enemy_spawn_interval)
    pygame.time.set_timer(powerup_spawn_timer, powerup_spawn_interval)

    enemy_types = ('red', 'green', 'elite')
    enemy_spawnrates = (0.45, 0.45, 0.1)
    powerup_types = ('health', 'max_health', 'damage', 'laser')
    powerup_spawnrates = (0.4,0.15,0.25,0.2)
    spawn_points = ((0,-10), (100,-10), (200,-10), (300,-10), (400,-10), (500,-10))

    enemies = []
    powerups = []
    level = 0
    
    player = Player()

    while True:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # Level up every {level up interval} sec
            # Difficulty increases
            if event.type == level_up_timer:
                level += 1
                # Enemies spawn more often
                enemy_spawn_interval *= 0.9
                # Enemy stats increase
                Enemy.level_up()

            # Player fires by pressing spacebar
            # If laser equipped, fire laser; else fire bullet
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if player.laser_equipped:
                        player.fire_laser()
                        
                    else:
                        player.fire_bullet()        
                    
            # Spawn an enemy every {enemy_spawn_interval} sec       
            if event.type == enemy_spawn_timer:          
                enemy_type = random.choices(enemy_types, enemy_spawnrates)[0]
                spawn_point = random.choice(spawn_points)
                enemy = Enemy(enemy_type, spawn_point)
                enemies.append(enemy)

            # Spawn a powerup every {powerup_spawn_interval} sec
            if event.type == powerup_spawn_timer:
                powerup_type = random.choices(powerup_types, powerup_spawnrates)[0]
                spawn_point = random.choice(spawn_points)
                powerup = Powerup(powerup_type, spawn_point)
                powerups.append(powerup)

        # Player movement
        move_key = pygame.key.get_pressed()
        player.move(move_key)
        # Check if any of the player's bullets hit an enemy
        player.handle_bullets(enemies)
        if player.laser_equipped:
            player.handle_laser(enemies)

        # Enemy movement, damage, death
        for enemy in enemies:
            enemy.move()
            
            # Enemy has moved offscreen -> player takes damage
            if enemy.body.y > SCREEN_HEIGHT:
                enemies.remove(enemy)
                player.take_damage(1)
              
            # Enemy killed
            if enemy.health <= 0:
                enemies.remove(enemy)
                enemy.destroyed_sound.play()
                player.kills += 1

            # Enemy firing
            # Lower fire_rate -> fire more frequently
            if random.randrange(0, int(enemy.fire_rate * 60)) == 1:
                enemy.fire()

            enemy.handle_bullets(player)
        
        # Powerup movement and pickups
        for powerup in powerups:
            powerup.move()

            if powerup.body.y > SCREEN_HEIGHT:
                powerups.remove(powerup)
             
            # Player picks up powerup
            if powerup.body.colliderect(player.body):
                if powerup.type == 'health':
                    player.heal(2)
                if powerup.type == 'max_health':
                    player.heal(10)
                if powerup.type == 'damage':
                    player.damage_up()
                if powerup.type == 'laser':
                    player.equip_laser()

                powerups.remove(powerup)

        display_game(player, enemies, powerups, level)
        
        # Player death ->  Game over   
        if player.health <= 0:
            player.death_sound.play()
            display_game_over(player)
            break

        clock.tick(60)


def main():
    # Level up timer
    level_up_timer = pygame.USEREVENT + 1

    # Enemy spawn timer
    enemy_spawn_timer = pygame.USEREVENT + 2

    # Powerup spawn timer
    powerup_spawn_timer = pygame.USEREVENT + 3
    
    # Represents the current game state: game or menu
    # When program is run, we start in menu
    game_active = False

    while True:
        # Main menu
        if not game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                # Prompt player to press space to start
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        game_active = True

            display_menu()

        # Main game loop
        else:
            run_game(level_up_timer, enemy_spawn_timer, powerup_spawn_timer)
            Enemy.leveL_reset()
            game_active = False


if __name__ == '__main__':
    main()