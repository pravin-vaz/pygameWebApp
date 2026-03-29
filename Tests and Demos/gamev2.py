import pygame
import random
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0
enemy_speed = 700
player_speed = 400
radius = 40
time_since_last_change = 1
lives = 5
collision_cooldown = 1000  # milliseconds
last_collision_time = 0
explosion = pygame.image.load('explosion-explode.gif')
font = pygame.font.Font('freesansbold.ttf', 32)
text = font.render(f'Lives:{lives}', True, 'green')
textRect = text.get_rect()
textRect.center = (100, 100)
player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
enemy_pos = pygame.Vector2(screen.get_width() / 3, screen.get_height() / 2)
enemy_velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * enemy_speed
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill("purple")
    time_since_last_change += dt
    # INITIALISE PLAYER & ENEMY & TEXT
    pygame.draw.circle(screen, 'red', player_pos, radius)
    pygame.draw.circle(screen, 'blue', enemy_pos, radius)
    screen.blit(text, textRect)
    # PLAYER MOVEMENT
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos.y -= player_speed * dt
    if keys[pygame.K_s]:
        player_pos.y += player_speed * dt
    if keys[pygame.K_a]:
        player_pos.x -= player_speed * dt
    if keys[pygame.K_d]:
        player_pos.x += player_speed * dt
    # ENEMY MOVEMENT
    enemy_pos += enemy_velocity * dt
    if time_since_last_change > random.randint(1,3):
        print('changing direction')
        direction = pygame.Vector2(0,0)
        to_player = pygame.Vector2(player_pos.x - enemy_pos.x, player_pos.y - enemy_pos.y)
        random_offset = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        direction = to_player + random_offset * 200
        #while direction.length() < 0.1:
        #    direction = pygame.Vector2(random.uniform(-1,1), random.uniform(-1, 1))
        enemy_speed += random.randint(-10, 10)
        enemy_velocity = direction.normalize() * enemy_speed
        print(direction, enemy_speed)
        time_since_last_change = 0
    if enemy_pos.x <= radius:
        enemy_velocity.x *= -1
        enemy_pos.x = radius
    elif enemy_pos.x >= screen.get_width() - radius:
        enemy_velocity.x *= -1
        enemy_pos.x = screen.get_width() - radius
    if enemy_pos.y <= radius:
        enemy_velocity.y *= -1
        enemy_pos.y = radius
    elif enemy_pos.y >= screen.get_height() - radius:
        enemy_velocity.y *= -1
        enemy_pos.y = screen.get_height() - radius
    distance = player_pos.distance_to(enemy_pos)
    current_time = pygame.time.get_ticks()
    if distance <= radius * 2 and current_time - last_collision_time > collision_cooldown:
        lives -= 1
        last_collision_time = current_time
        text = font.render(f'Lives:{lives}', True, 'green')
        direction = (enemy_pos - player_pos).normalize()
        enemy_pos += direction * radius * 2
    if lives <= 0:
        screen.fill('red')
        screen.blit(explosion,(enemy_pos.x, enemy_pos.y))
        for i in range(20):
            screen.blit(explosion, (random.randint(1,700), random.randint(1,700)))
        text = font.render(f'Lives:{lives}', True, 'black')
    pygame.display.update()
    dt = clock.tick(60) / 1000
pygame.quit()