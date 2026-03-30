import asyncio
import pygame
import sys, platform, math, random
import time
async def main():
    screen_size=[320, 180]
    #screen_size = [800,600]
    screen = pygame.display.set_mode(screen_size, pygame.SCALED)
    clock = pygame.time.Clock()
    clock.tick(); pygame.time.wait(16)

    CAR_OPTIONS = ["assets/RED BULL.png", "assets/ASTON MARTIN.png"]
    selected_car_index = 0

    road_texture = pygame.image.load("assets/road.png").convert()
    mountains_texture = pygame.image.load("assets/mountains.png").convert()
    tree_sprite = pygame.image.load("assets/tree.png").convert()
    dial_sprite = pygame.image.load("assets/tachometer.png").convert_alpha()
    needle_sprite = pygame.image.load("assets/needle.png").convert_alpha()
    tree_sprite.set_colorkey((255, 0, 255))

    game_state = "menu"
 # Menu system to select car sprite
    while game_state == "menu":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game_state = "playing"
                elif event.key == pygame.K_UP:
                    selected_car_index = (selected_car_index - 1) % len(CAR_OPTIONS)
                elif event.key == pygame.K_DOWN:
                    selected_car_index = (selected_car_index + 1) % len(CAR_OPTIONS)

        screen.fill((0, 0, 0))
        draw_menu(screen, CAR_OPTIONS, selected_car_index)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
 # Initialise gear sounds
    pygame.mixer.init()
    gear_sounds = [
        pygame.mixer.Sound("assets/Gear1.ogg"),
        pygame.mixer.Sound("assets/Gear2.ogg"),
        pygame.mixer.Sound("assets/Gear3.ogg"),
        pygame.mixer.Sound("assets/Gear4.ogg"),
        pygame.mixer.Sound("assets/Gear5.ogg"),
    ]
    redline_sound = pygame.mixer.Sound("assets/Redline.wav")
    redline_sound.set_volume(0.6)
    car_sprite = pygame.image.load(CAR_OPTIONS[selected_car_index]).convert_alpha()
 # Initialise cars and trees
    car = Player(gear_sounds, redline_sound)
    cars = [Car(-10), Car(-1), Car(7)]
    trees = [Tree(-67), Tree(-55), Tree(-43), Tree(-33), Tree(-25), Tree(-13), Tree(-3)]
    running = 1
    lap_time = 0
    score = 0
    save = 'save_file.txt'
 # Open save file
    try:
        with open(save, 'r') as file:
            high_score = int(file.read())
    except (FileNotFoundError, ValueError):
        high_score = 0
        # Main gameplay loop
    if game_state == 'playing':

        while running:
            delta = clock.tick() / 1000 + 0.00001
            # Score
            distance_traveled = car.velocity * delta
            score += max(distance_traveled, 0)
            if score > high_score:
                high_score = score
                with open(save, 'w') as file:
                    file.write(str(int(high_score)))
        # Gear changing and quitting the game
            car.controls(delta)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = 0
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        car.gearshift_down()
                    elif event.key == pygame.K_e:
                        car.gearshift_up()
                elif event.type == pygame.USEREVENT + 1:
                    car.engine_channel.play(car.redline_sound, loops=-1)
                    car.redline_playing = True
                    car.rev_playing = False

            screen.blit(mountains_texture, (-65-car.angle*82,0))
            #screen.fill((100, 150, 250))
            #vertical, draw_distance = 180, 1
            vertical, draw_distance = screen_size[1],1
            car.z = calc_z(car.x)
           # z_buffer = [999 for element in range(180)]
            # buffer
            z_buffer = [999 for element in range(screen_size[1])]
           # road drawing
            while draw_distance < 80:
                last_vertical = vertical

                while vertical >= last_vertical and draw_distance < 120:
                    draw_distance += draw_distance/150
                    x = car.x + draw_distance
                    scale = 1/draw_distance
                    z = calc_z(x) - car.z
                    vertical = int(60+160*scale + z*scale)

                if draw_distance < 120:
                    z_buffer[int(vertical)] = draw_distance
                    road_slice = road_texture.subsurface((0, 10*x%360,320, 1))
                    colour = (int(50-draw_distance/3),int(130-draw_distance), int(50-z/20+30*math.sin(x)))
                    pygame.draw.rect(screen, colour, (0, vertical, 320, 1))
                    render_element(screen, road_slice, 500*scale, 1, scale, x, car, car.y, z_buffer)
            # render trees
            for index in reversed(range(len(trees))):
                scale = max(0.0001, 1/(trees[index].x - car.x))
                render_element(screen, tree_sprite, 200 * scale, 300 * scale, scale, trees[index].x, car,trees[index].y + car.y, z_buffer)

            if trees[0].x < car.x+1:
                trees.pop(0)
                trees.append(Tree(trees[-1].x))
            # render cars
            for index in reversed(range(len(cars))):
                scale = max(0.0001, 1 / (cars[index].x - car.x))
                render_element(screen, car_sprite, 100 * scale, 80 * scale, scale,
                               cars[index].x, car, -70 + car.y, z_buffer)
                cars[index].x += cars[index].velocity * delta

            if cars[0].x < car.x + 1:
                cars.pop(0)
                cars.append(Car(car.x, velocity=random.choice([40, 60, 80])))

            lap_time += delta
            render_hud(screen, car, lap_time, score, high_score, dial_sprite, needle_sprite)
            player_rect = car_sprite.get_rect(topleft=(100, 120))
            screen.blit(car_sprite, player_rect.topleft)
            # rectangles for car collision
            for index in reversed(range(len(cars))):
                scale = max(0.0001, 1 / (cars[index].x - car.x))
                rect = render_element(screen, car_sprite, 100 * scale, 80 * scale, scale,
                                      cars[index].x, car, -70 + car.y, z_buffer)
                if rect:
                    hitbox = rect.inflate(-rect.width * 0.3, -rect.height * 0.3)
                    if player_rect.colliderect(hitbox):
                        print("CRASH with another car!")
                        car.velocity = -10

                        car.acceleration = 0
                        cars[index].velocity = 0  # stop the AI car involved
                        score = score / 2
                        if player_rect.centerx < hitbox.centerx:
                            player_rect.right = hitbox.left
                        else:
                            player_rect.left = hitbox.right
            # collision for trees
            for index in reversed(range(len(trees))):
                scale = max(0.0001, 1 / (trees[index].x - car.x))
                rect = render_element(screen, tree_sprite, 200 * scale, 300 * scale, scale, trees[index].x, car,
                                      trees[index].y + car.y, z_buffer)
                if rect and player_rect.colliderect(rect):
                    print("CRASH into a tree!")
                    car.velocity = 0
                    car.acceleration = 0
            if abs(car.y - calc_y(car.x + 2) - 100) > 280 and car.velocity > 5:
                score -= 1 * delta
                car.velocity += -car.velocity * delta
                car.acceleration += -car.acceleration * delta
                pygame.draw.circle(screen, (255, 0, 0), (300, 170), 3)
            pygame.display.update()
            await asyncio.sleep(0)

class Tree():
    def __init__(self, distance):
        self.x = distance + random.randint(10, 20) +0.5
        self.y = random.randint(500, 1500)*random.choice([-1,1])
# Menu initialisation
def draw_menu(screen, car_options, selected_index):
    font = pygame.font.SysFont("Arial", 24, bold=True)
    title_text = font.render("Select your car:", True, (255, 255, 255))
    screen.blit(title_text, (screen.get_width()//2 - title_text.get_width()//2, 30))

    for i, car in enumerate(car_options):
        color = (255, 0, 0) if i == selected_index else (255, 255, 255)
        text = font.render(car.split('/')[-1].replace('.png', ''), True, color)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 70 + i*30))

    prompt_text = font.render("Press ENTER to Begin!", True, (255, 255, 0))
    screen.blit(prompt_text, (screen.get_width()//2 - prompt_text.get_width()//2, 140))

# Sine wave for road (left and right)
def calc_y(x):
    #return 200*math.sin(x/113) +170*math.sin(x/117)
    #return 200*math.sin(x/1117) +170*math.sin(x/1113)
    return 200*math.sin(x/13) +170*math.sin(x/17)
# sin wave for road elevation (up and down)
def calc_z(x):
    #return 200+80*math.sin(x/300)-120*math.sin(x/200)
    return 200+80*math.sin(x/13)-120*math.sin(x/17)
#def collision_detection():

# Render HUD elements (gear, score, speed, tachometer etc)
def render_hud(screen, player, lap_time, score, high_score, dial_sprite, needle_sprite):
    scale = 0.5

    scaled_dial = pygame.transform.smoothscale(
        dial_sprite,
        (int(dial_sprite.get_width() * scale), int(dial_sprite.get_height() * scale))
    )

    scaled_needle = pygame.transform.smoothscale(
        needle_sprite,
        (int(needle_sprite.get_width() * scale), int(needle_sprite.get_height() * scale))
    )
    dial_rect = scaled_dial.get_rect(bottomright=(screen.get_width() - 8, screen.get_height() - 8))
    screen.blit(scaled_dial, dial_rect.topleft)

    MAX_RPM = 12000
    NEEDLE_OFFSET = -30
    MIN_ANGLE = 0
    MAX_ANGLE = 230

    rpm = min(player.velocity * player.gear_ratios[player.gear] * 150, MAX_RPM)  # tweak multiplier

    needle_angle = MIN_ANGLE + (rpm / MAX_RPM) * MAX_ANGLE + NEEDLE_OFFSET

    rotated_needle = pygame.transform.rotate(scaled_needle, -needle_angle)
    rotated_rect = rotated_needle.get_rect(center=dial_rect.center)
    screen.blit(rotated_needle, rotated_rect.topleft)

    font = pygame.font.SysFont("Arial", 16)
    speed_kmh = abs(player.velocity * 3.6)
    speed_text = font.render(f"speed: {int(speed_kmh)} kmh", True, (255, 255, 255))
    gear_text = font.render(f"Gear: {player.gear} ", True, (255, 255, 255))
    screen.blit(speed_text, (5, 15))
    screen.blit(gear_text, (5, 25))
    score_text = font.render(f"score: {int(score)}", True, (255, 255, 255))
    screen.blit(score_text, (5, 35))
    high_score_text = font.render(f"High Score: {int(high_score)} ", True, (255, 255, 255))
    screen.blit(high_score_text, (5, 45))
# render elements
def render_element(screen, sprite, width, height, scale, x, car, y, z_buffer):
    y = calc_y(x) - y
    z = calc_z(x) - car.z

    vertical = int(60+160*scale + z*scale)
    if vertical >= 1 and vertical < 180 and z_buffer[vertical-1] > 1/scale -10:
        horizontal = 160-(160-y)*scale + car.angle*(vertical-150)

        scaled_sprite = pygame.transform.scale(sprite, (int(width), int(height)))
        rect = scaled_sprite.get_rect()
        rect.topleft = (horizontal, vertical - height + 1)

        screen.blit(scaled_sprite, rect.topleft)
        return rect
    return None
# enemy car class
class Car():
    def __init__(self, distance, velocity=50):
        self.x = distance + random.randint(10, 50)
        self.velocity = velocity
        print(f"[SPAWN] New AI car at x={self.x}")

class Player():
    def __init__(self, gear_sounds, redline_sound):
        self.x = 0
        self.y = 300
        self.z = 0
        self.angle = 0
        self.velocity = 0
        self.acceleration = 0
        self.steer_base = 0.5
        self.steer_speed_factor = self.velocity / 50
        self.steer_factor = self.steer_base / (1 + self.velocity * 0.2)
        self.gear = 1
        self.gear_max = 8
        self.gear_ratios = [0, 2.2, 1.8, 1.5, 1.35, 1.2, 1.05, 0.75, 0.45]
        #self.gear_ratios = [0, 4, 3.5, 3, 2.5, 2, 1.5, 1.0, 0.55]

        #self.acceleration_multiplier = 0.025  # slows down overall acceleration to ~34 sec to top speed
        self.reversed_list = list(reversed(self.gear_ratios))
        self.max_speed = 0
        self.gear_sounds = gear_sounds
        self.redline_sound = redline_sound
        self.engine_channel = pygame.mixer.Channel(0)  # use one channel for looping redline
        self.rev_playing = False  # Is the engine rev sound currently playing
        self.redline_playing = False

        print(f'max_speed list: {self.max_speed}')
        print(f'reversed_list list: {self.reversed_list}')
        self.shift_start_time = None
        self.shift_debug_enabled = True  # Toggle this for debug prints

    def gearshift_up(self):
        if self.gear < self.gear_max:

            self.gear += 1
            self.redline_playing = False
            self.rev_playing = False  # ready to play new rev sound
            self.shift_start_time = time.time()

            print(f"Shifted up to {self.gear}th gear")

            self.engine_channel.stop()

            gear_index = min(self.gear - 1, 5) - 1
            if gear_index >= 0:
                self.gear_sounds[gear_index].play()

            gear_length = self.gear_sounds[gear_index].get_length() if gear_index >= 0 else 0
            pygame.time.set_timer(pygame.USEREVENT + 1, int(gear_length * 1000))

    def gearshift_down(self):
        if self.gear > 1:

            self.gear -= 1
            print(f"Shifted down to {self.gear}th gear")
            self.engine_channel.stop()

    def controls(self, delta):
        pressed_keys = pygame.key.get_pressed()

        self.acceleration += -0.2 * self.acceleration * delta
        self.velocity += -0.02 * self.velocity * delta
        self.max_speed = self.reversed_list[self.gear - 1] * 50

        # if pressed_keys[pygame.K_q]:
        #     self.gearshift_down()
        # if pressed_keys[pygame.K_e]:
        #     self.gearshift_up()
        # controls for player car, up down left right and gear shifts
        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            self.acceleration += 2 * delta * self.gear_ratios[self.gear]

            if not self.rev_playing and not self.redline_playing:
                # Pick correct gear sound
                gear_index = min(self.gear - 1, len(self.gear_sounds) - 1)
                self.engine_channel.play(self.gear_sounds[gear_index])
                self.rev_playing = True

                pygame.time.set_timer(
                    pygame.USEREVENT + 1,
                    int(self.gear_sounds[gear_index].get_length() * 1000),
                    True
                )

        elif pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            if self.velocity < 1:
                self.acceleration -= 30 * delta
            else:
                self.acceleration = 0
            self.velocity += -self.velocity * delta

        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            # self.angle -= delta * self.velocity / 10
            self.angle -= delta * self.steer_factor

        elif pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            # self.angle += delta * self.velocity / 10
            self.angle += delta * self.steer_factor

        if self.velocity < self.max_speed:
            self.velocity += self.acceleration * delta

        self.velocity = max(0, min(self.velocity, self.max_speed))
        self.x += self.velocity * delta * math.cos(self.angle)
        self.y += self.velocity * math.sin(self.angle) * delta * 100

        max_steer = 0.8 if self.velocity <= 60 else 0.4

        #self.angle = max(-max_steer, min(max_steer, self.angle))



if __name__ == "__main__":
    pygame.init()
    asyncio.run(main())
    pygame.quit()
