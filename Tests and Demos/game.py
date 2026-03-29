import pygame
import random
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0
speed = 200
radius = 40
time_since_last_change = 1
player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
enemy_pos = pygame.Vector2(screen.get_width() / 3, screen.get_height() / 2)
enemy_velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * speed
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill("purple")

    pygame.draw.circle(screen, 'red', player_pos, 40)
    pygame.draw.circle(screen, 'blue', enemy_pos, 40)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos.y -= 300 * dt
    if keys[pygame.K_s]:
        player_pos.y += 300 * dt
    if keys[pygame.K_a]:
        player_pos.x -= 300 * dt
    if keys[pygame.K_d]:
        player_pos.x += 300 * dt
    enemy_pos += enemy_velocity * dt
    time_since_last_change += dt
    print(f"Enemy Pos: {enemy_pos}, Velocity: {enemy_velocity}, Time: {time_since_last_change}")
    if time_since_last_change > 3:
        direction = pygame.Vector2(0, 0)
        while direction.length() < 0.1:
            direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        enemy_velocity = direction.normalize() * speed
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
    if distance <= radius*2:
        screen.fill('red')
    pygame.display.flip()
    dt = clock.tick(60) / 1000

pygame.quit()