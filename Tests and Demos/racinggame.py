import pygame
import sys
import math
import random
import time

pygame.init()

# Screen and clock
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Constants for projection and track
CAM_DEPTH = 200.0  # Distance from camera to projection plane
HORIZON_Y = SCREEN_HEIGHT * 0.4
GROUND_Y = SCREEN_HEIGHT * 0.95
SEGMENT_LENGTH = 50.0
NUM_SEGMENTS = 200
TRACK_LENGTH = NUM_SEGMENTS * SEGMENT_LENGTH
BASE_ROAD_WIDTH = 400.0  # world units for full road width

# Colors
COLOR_SKY = (135, 206, 235)
COLOR_GRASS_LIGHT = (50, 205, 50)
COLOR_GRASS_DARK = (34, 139, 34)
COLOR_ROAD = (105, 105, 105)
COLOR_RUMBLE_LIGHT = (255, 0, 0)
COLOR_RUMBLE_DARK = (255, 255, 255)
COLOR_STRIPE = (255, 255, 255)
COLOR_CAR_PLAYER = (0, 0, 255)
COLOR_CAR_AI = (255, 165, 0)
COLOR_TEXT = (0, 0, 0)
player_car_image = pygame.image.load("explosion-explode.jpg").convert_alpha()
DRAW_DISTANCE = 100  # you can increase to see further (at cost of perf)

font = pygame.font.SysFont("Arial", 18)


def clamp(value, a, b):
    return max(a, min(b, value))


def project_road(x, z, cam_x, cam_z):
    rel_x = x - cam_x
    rel_z = z - cam_z

    if rel_z <= 0.1:
        return None

    scale = CAM_DEPTH / rel_z
    if scale > 1:
        scale = 1

    screen_x = SCREEN_WIDTH / 2 + (rel_x * scale) * (SCREEN_WIDTH / BASE_ROAD_WIDTH)
    screen_y = GROUND_Y - (1 - scale) * (GROUND_Y - HORIZON_Y)
    return screen_x, screen_y, scale


def draw_segment(x1, y1, w1, x2, y2, w2, color):
    """
    x1,y1 : top center of segment on screen
    w1    : half-road width in PIXELS at y1
    x2,y2 : next segment screen coords
    w2    : half-road width in PIXELS at y2
    """
    pts = [
        (x1 - w1, y1),
        (x1 + w1, y1),
        (x2 + w2, y2),
        (x2 - w2, y2),
    ]
    pygame.draw.polygon(screen, color, pts)
    pygame.draw.lines(screen, (0, 0, 0), True, pts, 1)


def draw_rumble_strips(x1, y1, w1, x2, y2, w2, c1, c2):
    left = [
        (x1 - w1, y1),
        (x1 - w1 * 0.85, y1),
        (x2 - w2 * 0.85, y2),
        (x2 - w2, y2),
    ]
    right = [
        (x1 + w1, y1),
        (x1 + w1 * 0.85, y1),
        (x2 + w2 * 0.85, y2),
        (x2 + w2, y2),
    ]
    pygame.draw.polygon(screen, c1, left)
    pygame.draw.polygon(screen, c2, right)
    pygame.draw.lines(screen, (0, 0, 0), True, left, 1)
    pygame.draw.lines(screen, (0, 0, 0), True, right, 1)


def draw_road_stripe(x1, y1, w1, x2, y2, w2):
    s1 = w1 * 0.1
    s2 = w2 * 0.1
    pts = [
        (x1 - s1, y1),
        (x1 + s1, y1),
        (x2 + s2, y2),
        (x2 - s2, y2),
    ]
    pygame.draw.polygon(screen, COLOR_STRIPE, pts)


def draw_car(x, y, scale, color, steer=0.0):
    width = max(8, 60 * scale)
    height = max(6, 30 * scale)
    max_steer_angle = 20
    angle = clamp(steer, -1.0, 1.0) * max_steer_angle
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    body = [
        (-width * 0.5, height * 0.5),
        (-width * 0.4, -height * 0.3),
        (width * 0.4, -height * 0.3),
        (width * 0.5, height * 0.5),
        (0.0, height * 0.9),
    ]
    rotated = []
    for px, py in body:
        rx = px * cos_a - py * sin_a
        ry = px * sin_a + py * cos_a
        rotated.append((x + rx, y + ry))

    pygame.draw.polygon(screen, color, rotated)
    pygame.draw.lines(screen, (0, 0, 0), True, rotated, 1)

    wheel_r = max(2, int(height * 0.15))
    wheel_offsets = [
        (-width * 0.3, height * 0.45),
        (width * 0.3, height * 0.45),
        (-width * 0.3, -height * 0.4),
        (width * 0.3, -height * 0.4),
    ]
    for ox, oy in wheel_offsets:
        rx = ox * cos_a - oy * sin_a
        ry = ox * sin_a + oy * cos_a
        cx = int(x + rx)
        cy = int(y + ry)
        pygame.draw.circle(screen, (20, 20, 20), (cx, cy), wheel_r)
        pygame.draw.circle(screen, (100, 100, 100), (cx, cy), max(1, int(wheel_r * 0.7)))


def draw_text(text, x, y, color=COLOR_TEXT):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


class Track:
    def __init__(self):
        self.segments = []
        for i in range(NUM_SEGMENTS):
            z1 = i * SEGMENT_LENGTH
            z2 = z1 + SEGMENT_LENGTH
            curve = math.sin(i / 20.0) * 0.5  # normalized -0.5..0.5
            self.segments.append({'z1': z1, 'z2': z2, 'curve': curve})

    def get_segment(self, index):
        # accept indices beyond NUM_SEGMENTS and wrap internally
        return self.segments[index % NUM_SEGMENTS]


class Car:
    def __init__(self, x=0.0, speed=0.0, color=COLOR_CAR_PLAYER, z=0.0):
        self.x = x
        self.speed = speed
        self.color = color
        self.z = z
        self.acceleration = 70.0
        self.brake_deceleration = 120.0
        self.coast_deceleration = 20.0
        self.max_speed = 1000.0
        self.lateral_position = x
        self.lateral_speed = 0.0
        self.max_lateral_speed = 4.0
        self.lateral_acceleration = 8.0
        self.lateral_friction = 10.0

    def update(self, keys=None, dt=0.0):
        if keys is not None:
            if keys[pygame.K_UP]:
                self.speed += self.acceleration * dt
            elif keys[pygame.K_DOWN]:
                self.speed -= self.brake_deceleration * dt
            else:
                if self.speed > 0:
                    self.speed -= self.coast_deceleration * dt
                    if self.speed < 0:
                        self.speed = 0.0

            self.speed = clamp(self.speed, 0.0, self.max_speed)

            strength = max(1.0, 5.0 - (self.speed / self.max_speed) * 4.0)
            if keys[pygame.K_LEFT]:
                self.lateral_speed -= self.lateral_acceleration * dt * strength
            elif keys[pygame.K_RIGHT]:
                self.lateral_speed += self.lateral_acceleration * dt * strength
            else:
                if self.lateral_speed > 0:
                    self.lateral_speed -= self.lateral_friction * dt
                    if self.lateral_speed < 0:
                        self.lateral_speed = 0
                elif self.lateral_speed < 0:
                    self.lateral_speed += self.lateral_friction * dt
                    if self.lateral_speed > 0:
                        self.lateral_speed = 0

            self.lateral_speed = clamp(self.lateral_speed, -self.max_lateral_speed, self.max_lateral_speed)
            self.lateral_position += self.lateral_speed * dt
            self.lateral_position = clamp(self.lateral_position, -1.0, 1.0)
            self.x = self.lateral_position
        else:
            # simple coasting for AI
            if self.speed > 0:
                self.speed -= self.coast_deceleration * dt
                if self.speed < 0:
                    self.speed = 0.0
            if self.lateral_speed > 0:
                self.lateral_speed -= self.lateral_friction * dt
                if self.lateral_speed < 0:
                    self.lateral_speed = 0
            elif self.lateral_speed < 0:
                self.lateral_speed += self.lateral_friction * dt
                if self.lateral_speed > 0:
                    self.lateral_speed = 0
            self.lateral_position += self.lateral_speed * dt
            self.lateral_position = clamp(self.lateral_position, -1.0, 1.0)
            self.x = self.lateral_position


def main():
    track = Track()
    player = Car()
    ai_cars = [
        Car(x=-0.5, speed=4.5, color=COLOR_CAR_AI, z=100.0),
        Car(x=0.5, speed=5.2, color=COLOR_CAR_AI, z=300.0),
        Car(x=0.0, speed=4.8, color=COLOR_CAR_AI, z=500.0),
    ]

    distance = 0.0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(keys, dt)
        # forward movement multiplier
        distance += player.speed * dt * 20.0
        distance %= TRACK_LENGTH

        # update AIs
        for ai in ai_cars:
            ai.z += ai.speed * dt * 20.0
            ai.z %= TRACK_LENGTH
            ai.speed += random.uniform(-0.05, 0.05)
            ai.speed = clamp(ai.speed, 2.0, 10.0)
            # simple lateral behaviour
            seg = track.get_segment(int(ai.z // SEGMENT_LENGTH))
            target_center = seg['curve']  # -0.5..0.5
            desired = clamp(target_center * 2.0, -1.0, 1.0)
            ai.x += (desired - ai.x) * 0.04
            ai.x += math.sin(time.time() * 3 + ai.z * 0.02) * 0.002
            ai.x = clamp(ai.x, -1.0, 1.0)

        screen.fill(COLOR_SKY)

        base_index = int(distance // SEGMENT_LENGTH)
        cam_x = player.x * (BASE_ROAD_WIDTH / 2.0)
        cam_z = distance

        last_y = SCREEN_HEIGHT

        # Draw segments from nearest to farthest (i = 0 is nearest forward segment)
        # --- Phase 1: Draw grass bands ---
        for i in range(DRAW_DISTANCE):
            seg_index_num = base_index + i
            seg = track.get_segment(seg_index_num)
            next_seg = track.get_segment(seg_index_num + 1)

            seg_z1 = seg_index_num * SEGMENT_LENGTH
            seg_z2 = seg_z1 + SEGMENT_LENGTH

            world_x1 = seg['curve'] * (BASE_ROAD_WIDTH / 2.0)
            world_x2 = next_seg['curve'] * (BASE_ROAD_WIDTH / 2.0)

            proj1 = project_road(world_x1, seg_z1, cam_x, cam_z)
            proj2 = project_road(world_x2, seg_z2, cam_x, cam_z)

            if (proj1 is None) or (proj2 is None):
                continue

            _, y1, _ = proj1
            _, y2, _ = proj2

            y_top = int(min(y1, y2))
            y_bottom = int(max(y1, y2))

            grass_color = COLOR_GRASS_LIGHT if (seg_index_num % 2 == 0) else COLOR_GRASS_DARK
            pygame.draw.rect(screen, grass_color, pygame.Rect(0, y_top, SCREEN_WIDTH, y_bottom - y_top))

        # --- Phase 2: Draw road, rumble strips, stripes ---
        for i in range(DRAW_DISTANCE):
            seg_index_num = base_index + i
            seg = track.get_segment(seg_index_num)
            next_seg = track.get_segment(seg_index_num + 1)

            seg_z1 = seg_index_num * SEGMENT_LENGTH
            seg_z2 = seg_z1 + SEGMENT_LENGTH

            world_x1 = seg['curve'] * (BASE_ROAD_WIDTH / 2.0)
            world_x2 = next_seg['curve'] * (BASE_ROAD_WIDTH / 2.0)

            proj1 = project_road(world_x1, seg_z1, cam_x, cam_z)
            proj2 = project_road(world_x2, seg_z2, cam_x, cam_z)

            if (proj1 is None) or (proj2 is None):
                continue

            x1, y1, scale1 = proj1
            x2, y2, scale2 = proj2

            half_road_px1 = scale1 * (SCREEN_WIDTH / 2.0)
            half_road_px2 = scale2 * (SCREEN_WIDTH / 2.0)

            draw_segment(x1, y1, half_road_px1, x2, y2, half_road_px2, COLOR_ROAD)

            if seg_index_num % 2 == 0:
                draw_rumble_strips(x1, y1, half_road_px1, x2, y2, half_road_px2, COLOR_RUMBLE_LIGHT, COLOR_RUMBLE_DARK)
            else:
                draw_rumble_strips(x1, y1, half_road_px1, x2, y2, half_road_px2, COLOR_RUMBLE_DARK, COLOR_RUMBLE_LIGHT)

            if seg_index_num % 20 < 10:
                draw_road_stripe(x1, y1, half_road_px1, x2, y2, half_road_px2)

        # Draw player car: project a point slightly ahead of camera so car scales correctly
        near_proj = project_road(player.x * (BASE_ROAD_WIDTH / 2.0), cam_z + SEGMENT_LENGTH * 0.5, cam_x, cam_z)
        if near_proj:
            px, py, pscale = near_proj
            # Scale the image based on pscale (adjust multiplier to your liking)
            scale_factor = max(0.5, pscale * 0.5)
            img_w = int(player_car_image.get_width() * scale_factor)
            img_h = int(player_car_image.get_height() * scale_factor)
            scaled_img = pygame.transform.smoothscale(player_car_image, (img_w, img_h))
            # Draw image centered on px, py offset a bit upwards
            screen.blit(scaled_img, (px - img_w // 2, py - img_h))
        else:
            # fallback: just draw image at default position & scale 1.0
            img_w = player_car_image.get_width()
            img_h = player_car_image.get_height()
            screen.blit(player_car_image,
                        (SCREEN_WIDTH // 2 - img_w // 2 + int(player.x * (BASE_ROAD_WIDTH / 2.0)), GROUND_Y - img_h))

        # Draw AI cars with their absolute z positions
        for ai in ai_cars:
            # world lateral is segment center + ai.x * half road width
            ai_seg_idx = int(ai.z // SEGMENT_LENGTH)
            seg = track.get_segment(ai_seg_idx)
            seg_center_world = seg['curve'] * (BASE_ROAD_WIDTH / 2.0)
            ai_world_x = seg_center_world + ai.x * (BASE_ROAD_WIDTH / 2.0)
            proj = project_road(ai_world_x, ai.z, cam_x, cam_z)
            if proj:
                ax, ay, ascale = proj
                draw_car(ax, ay - 20, max(0.35, ascale * 1.05), ai.color)

        # HUD
        draw_text(f"Speed: {player.speed:.1f}", 10, 10)
        draw_text(f"Distance: {distance:.1f}", 10, 30)
        draw_text(f"Position: {player.x:.2f}", 10, 50)
        draw_text(f"FPS: {clock.get_fps():.1f}", 10, 70)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
