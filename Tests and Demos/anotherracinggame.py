import asyncio
import pygame
import sys, platform, math, random

async def main():
    screen_size=[320, 180]
    #screen_size = [1920,1080]
    screen = pygame.display.set_mode(screen_size, pygame.SCALED)
    clock = pygame.time.Clock()
    clock.tick(); pygame.time.wait(16)
    road_texture = pygame.image.load("assets/road.png").convert()
    mountains_texture = pygame.image.load("assets/mountains.png").convert()
    car_sprite = pygame.image.load("assets/car_sprite1.png").convert_alpha()
    tree_sprite = pygame.image.load("assets/tree.png").convert()
    tree_sprite.set_colorkey((255, 0, 255))

    car = Player()
    cars = [Car(-10), Car(-1), Car(7)]
    trees = [Tree(-67), Tree(-55), Tree(-43), Tree(-33), Tree(-25), Tree(-13), Tree(-3)]
    running = 1
    lap_time = 0
    score = 0
    while running:
        delta = clock.tick() / 1000 + 0.00001

        score += 1 * delta * car.velocity
        car.controls(delta)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = 0
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_q:
                    car.gearshift_down()
                if event.key == pygame.K_e:
                    car.gearshift_up()

        screen.blit(mountains_texture, (-65-car.angle*82,0))
        #screen.fill((100, 150, 250))
        #vertical, draw_distance = 180, 1
        vertical, draw_distance = screen_size[1],1
        car.z = calc_z(car.x)
       # z_buffer = [999 for element in range(180)]
        z_buffer = [999 for element in range(screen_size[1])]

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

        for index in reversed(range(len(trees))):
            scale = max(0.0001, 1/(trees[index].x - car.x))
            render_element(screen, tree_sprite, 200 * scale, 300 * scale, scale, trees[index].x, car,trees[index].y + car.y, z_buffer)

        if trees[0].x < car.x+1:
            trees.pop(0)
            trees.append(Tree(trees[-1].x))

        for index in reversed(range(len(cars))):
            scale = max(0.0001, 1/(cars[index].x - car.x))
            render_element(screen, car_sprite, 100*scale, 80*scale, scale, cars[index].x, car, -70+car.y, z_buffer)
            cars[index].x += 50*delta

        if cars[0].x < car.x+1:
            cars.pop(0)
            cars.append(Car(car.x))

        lap_time += delta
        render_hud(screen, car, lap_time, score)
        player_rect = car_sprite.get_rect(topleft=(100, 120))
        screen.blit(car_sprite, player_rect.topleft)
        for index in reversed(range(len(cars))):
            scale = max(0.0001, 1 / (cars[index].x - car.x))
            rect = render_element(screen, car_sprite, 100 * scale, 80 * scale, scale, cars[index].x, car, -70 + car.y,
                                  z_buffer)
            if rect and player_rect.colliderect(rect):
                print("CRASH with another car!")
                car.velocity = 0
                cars.x = 0
                car.acceleration = 0
                score = score / 2
            cars[index].x += 20 * delta

        for index in reversed(range(len(trees))):
            scale = max(0.0001, 1 / (trees[index].x - car.x))
            rect = render_element(screen, tree_sprite, 200 * scale, 300 * scale, scale, trees[index].x, car,
                                  trees[index].y + car.y, z_buffer)
            if rect and player_rect.colliderect(rect):
                print("CRASH into a tree!")
                car.velocity = 0
                car.acceleration = 0
        if abs(car.y - calc_y(car.x + 2) - 100) > 280 and car.velocity > 5:
            car.velocity += -car.velocity * delta
            car.acceleration += -car.acceleration * delta
            pygame.draw.circle(screen, (255, 0, 0), (300, 170), 3)

        pygame.display.update()
        await asyncio.sleep(0)

class Tree():
    def __init__(self, distance):
        self.x = distance + random.randint(10, 20) +0.5
        self.y = random.randint(500, 1500)*random.choice([-1,1])

def calc_y(x):
    #return 200*math.sin(x/113) +170*math.sin(x/117)
    #return 200*math.sin(x/1117) +170*math.sin(x/1113)
    return 200*math.sin(x/13) +170*math.sin(x/17)

def calc_z(x):
    #return 200+80*math.sin(x/300)-120*math.sin(x/200)
    return 200+80*math.sin(x/13)-120*math.sin(x/17)
#def collision_detection():


def render_hud(screen, player, lap_time, score):
    font = pygame.font.SysFont("Arial", 16)

    speed_kmh = abs(player.velocity * 3.6)
    speed_text = font.render(f"speed: {int(speed_kmh)} kmh", True, (255, 255, 255))
    gear_text = font.render(f"Gear: {player.gear} ", True, (255, 255, 255))
    screen.blit(speed_text, (5, 25))
    screen.blit(gear_text, (5, 35))
    score_text = font.render(f"score: {int(score)}", True, (255, 255, 255))
    screen.blit(score_text, (15, 45))
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

class Car():
    def __init__(self, distance):
        self.x = distance + random.randint(90, 110)
        print(f"[SPAWN] New AI car at x={self.x}")

class Player():
    def __init__(self):
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
        self.gear_ratios = [0, 2.0, 1.75, 1.5, 1.2, 0.9, 0.6, 0.4, 0.2,]
        self.reversed_list = list(reversed(self.gear_ratios))
        self.max_speed = 0
        print(f'max_speed list: {self.max_speed}')
        print(f'reversed_list list: {self.reversed_list}')
    def gearshift_up(self):
        if self.gear < self.gear_max:
            self.gear += 1
            print(f'shifted up to {self.gear}th gear')
            print(self.velocity)
    def gearshift_down(self):
        if self.gear > 1:
            self.gear -= 1
    def controls(self,delta):
        pressed_keys = pygame.key.get_pressed()
        self.acceleration += -0.2*self.acceleration*delta
        self.velocity+=-0.02*self.velocity*delta
        self.max_speed = self.reversed_list[self.gear-1]*50
      #  if pressed_keys[pygame.K_q]:
      #      self.gearshift_down()
      #  if pressed_keys[pygame.K_e]:
      #      self.gearshift_up()
        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            if self.velocity >-1:
                self.acceleration += 7*delta * self.gear_ratios[self.gear]
            else:
                self.acceleration = 0
                self.velocity += self.velocity*delta
        elif pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            if  self.velocity < 1:
                self.acceleration -=30* delta
            else:
                self.acceleration=0
                self.velocity += -self.velocity*delta
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            #self.angle -= delta * self.velocity / 10
            self.angle -= delta * self.steer_factor
        elif pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            #self.angle += delta * self.velocity / 10
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