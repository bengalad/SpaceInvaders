import os
import time
import random
import pygame
from pygame import mixer
#initialize font and mixer modules for text and sound respectively
pygame.font.init()
pygame.mixer.init()

#setting background size and adding title of window
WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

#load images
RED_SPACESHIP = pygame.image.load(os.path.join("images", "pixel_ship_red_small.png"))
GREEN_SPACESHIP = pygame.image.load(os.path.join("images", "pixel_ship_green_small.png"))
BLUE_SPACESHIP = pygame.image.load(os.path.join("images", "pixel_ship_blue_small.png"))
HEALTH_PACK = pygame.transform.scale(pygame.image.load(os.path.join("images", 'health_pack.png')), (65,60))

#player ship
YELLOW_SPACESHIP = pygame.image.load(os.path.join("images", "pixel_ship_yellow.png"))

#load lasers
RED_LASER = pygame.image.load(os.path.join("images", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("images", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("images", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("images", "pixel_laser_yellow.png"))

# load background
BG = pygame.transform.scale(pygame.image.load(os.path.join("images", "background-black.png")), (WIDTH, HEIGHT))

#load sounds
mixer.music.load(os.path.join("sounds", 'background.wav'))
EXPOLSION_SOUND = mixer.Sound(os.path.join("sounds", "explosion.wav"))
LASER_SOUND = mixer.Sound(os.path.join("sounds", "laser.wav"))
ENEMY_LASER_SOUND = mixer.Sound(os.path.join("sounds", "laser_enemy.wav"))
HEAL_SOUND = mixer.Sound(os.path.join("sounds", 'healing.wav'))

#play background music, -1 makes it a loop
mixer.music.play(-1)

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(obj, self)


class Ship:
    COOLDOWN = 25

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            LASER_SOUND.play()
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACESHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health   

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        EXPOLSION_SOUND.play()
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))


class Enemy(Ship):
    COLOR_MAP = {
                "red": (RED_SPACESHIP, RED_LASER),
                "green": (GREEN_SPACESHIP, GREEN_LASER),
                "blue": (BLUE_SPACESHIP, BLUE_LASER)
                }

    def __init__(self, x, y, colour, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[colour]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            ENEMY_LASER_SOUND.play()
            laser = Laser(self.x - 15, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

class Healthpack:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.healthpack_img = HEALTH_PACK
        self.mask = pygame.mask.from_surface(self.healthpack_img)

    def draw(self, window):
        window.blit(self.healthpack_img, (self.x, self.y))

    def move(self, vel):
        self.y += vel
     
    def get_width(self):
        return self.healthpack_img.get_width()

    def get_height(self):
        return self.healthpack_img.get_height()

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (int(offset_x), int(offset_y))) != None


def main():
    run = True
    FPS = 60
    level = 0
    lives = 5

    main_font = pygame.font.SysFont("comicsans", 50)
    lost_font = pygame.font.SysFont("comicsans", 65)
    levelup_font = pygame.font.SysFont("comicsans", 55)

    enemies = []
    healthpacks = []
    wavelength = 5
    enemy_vel = 1
    health_pack_vel = 0.5

    #speed of player ship and lasers
    player_vel = 5
    laser_vel = 6

    player = Player(300, 630)
    #healthpack = Healthpack(0,0)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window():
        WIN.blit(BG, (0,0))
        #setting text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))
        level_label = main_font.render(f"Level: {level}", 1, (255,255,255))
        lost_label = lost_font.render("YOU LOSE!!", 1, (255,255,255))
        levelup_label = levelup_font.render("Next wave get ready...", 1, (255,255,255))
        #
        leveluplabel_copy = levelup_label.copy()
        alpha = 255
        timer = 10


        WIN.blit(lives_label, (10,10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

        for healthpack in healthpacks:
            healthpack.draw(WIN)

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
             WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))
        if len(enemies) == 0 and level > 0 and lost == False:
            if timer > 0:
                timer -= 1
            else:
                if alpha > 0:
                    alpha = max(0, alpha-4)
                    leveluplabel_copy = levelup_label.copy()
                    leveluplabel_copy.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGB_MULT)
            WIN.blit(leveluplabel_copy, (WIDTH/2 - leveluplabel_copy.get_width()/2, 350))
            pygame.display.flip()
            clock.tick(1)

        pygame.display.update() 

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 3:
                run = False 
            else:  
                continue    

        if len(enemies) == 0:        
            level += 1
            wavelength += 5
            for i in range(wavelength):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1000, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)
    
        if len(healthpacks) == 0:
            for j in range(3):
                healthpack = Healthpack(random.randrange(50, WIDTH-100), random.randrange(-1000, -100))
                healthpacks.append(healthpack)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x - player_vel > 0: #moving to left
            player.x -= player_vel
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() < WIDTH: #moving to right
            player.x += player_vel
        if keys[pygame.K_UP] and player.y - player_vel > 0: #moving upwards
            player.y -= player_vel    
        if keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() + 15 < HEIGHT: #moving downwards
           player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()
        
        for enemy in enemies:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 4*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                EXPOLSION_SOUND.play()
                player.health -= 15
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        for healthpack in healthpacks:
            healthpack.move(health_pack_vel)

            if collide(healthpack, player) and player.health < 100:
                HEAL_SOUND.play()
                player.health += 15
                healthpacks.remove(healthpack)
            elif collide(healthpack, player) and player.health >= 100:
                healthpacks.remove(healthpack)
            elif healthpack.y + healthpack.get_height() > HEIGHT:
                healthpacks.remove(healthpack)

        player.move_lasers(-laser_vel, enemies)
        
def main_menu():
    title_font = pygame.font.SysFont("comicsans", 70)
    run = True
    while run:
        WIN.blit(BG, (0,0))
        title_label = title_font.render("Click the mouse to begin...", 1, (255,255,255))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 350))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONUP:
                main()
    pygame.quit()

              
main_menu()