import asyncio
import pygame
import sys, platform, math, random



async def main():

    global road_path
    track_points = [
        (0, 0),  # Start/finish straight
        (150, 50),  # Gentle right
        (300, 150),  # Long sweeping right
        (400, 160),  # Tight left hairpin
        (200, 400),  # Short straight
        (50, 350),  # Sweeping left
        (-100, 200),  # Back straight entry
        (-150, 50),  # Tight right
        (-50, -100),  # Gentle left
        (100, -150),  # Final right back to start
        (150, 50),  # Gentle right
        (-1000, 3000),  # Long sweeping right
        (5000,-2000),
        (400, 160),  # Tight left hairpin
        (200, 400),  # Short straight
        (50, 350),  # Sweeping left
        (-100, 200),  # Back straight entry
        (-150, 50),  # Tight right
        (-50, -100),  # Gentle left
        (100, -150),  # Final right back to start
        (0,0)
    ]
    road_path = generate_road(track_points)
    track_points += track_points[:3]
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


class Tree():
    def __init__(self, distance):
        self.x = distance + random.randint(10, 20) +0.5
        self.y = random.randint(500, 1500)*random.choice([-1,1])
import math
import pygame
from typing import List, Tuple

# =========================
# Spline and road utilities
# =========================

def generate_road(track_points: List[Tuple[float, float]], samples_per_segment=20):
    road_path = []
    for i in range(len(track_points) - 3):
        p0, p1, p2, p3 = track_points[i], track_points[i+1], track_points[i+2], track_points[i+3]
        for j in range(samples_per_segment):
            t = j / samples_per_segment
            road_path.append(catmull_rom(p0, p1, p2, p3, t))
    return road_path

def catmull_rom(p0, p1, p2, p3, t: float):
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * ((2 * p1[0]) +
               (-p0[0] + p2[0]) * t +
               (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
               (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
    y = 0.5 * ((2 * p1[1]) +
               (-p0[1] + p2[1]) * t +
               (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
               (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
    return (x, y)

def height_at_index(i: int) -> float:
    # Keep your original “fake hills” function, driven by spline index.
    return 200 * math.sin(i / 117.0) + 170 * math.sin(i / 13.0)

def nearest_spline_index(world_x: float, world_y: float, road_path, last_idx_hint: int = 0, window: int = 200) -> int:
    """
    Fast, stable nearest search: scans a window around the last used index.
    Falls back to full scan if path is small.
    """
    n = len(road_path)
    if n == 0:
        return 0
    if n <= window * 2:
        start, end = 0, n
    else:
        start = max(0, last_idx_hint - window)
        end = min(n, last_idx_hint + window)

    closest_i = last_idx_hint
    closest_d2 = float('inf')
    for i in range(start, end):
        px, py = road_path[i]
        d2 = (px - world_x) * (px - world_x) + (py - world_y) * (py - world_y)
        if d2 < closest_d2:
            closest_d2 = d2
            closest_i = i
    return closest_i

# =========================
# Camera and projection
# =========================

class Camera:
    __slots__ = ("x", "y", "z", "angle")
    def __init__(self, x=0.0, y=0.0, z=0.0, angle=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle

def to_camera_space(cam: Camera, world_x: float, world_y: float):
    dx = world_x - cam.x
    dy = world_y - cam.y
    ca = math.cos(-cam.angle)
    sa = math.sin(-cam.angle)
    # Rotate world into camera space
    rel_x = dx * ca - dy * sa
    rel_y = dx * sa + dy * ca  # depth (forward)
    return rel_x, rel_y

def project(rel_x: float, rel_y: float, z_world: float, z_cam: float,
            screen_w: int, screen_h: int, focal_px: float, horizon_px: float):
    """
    Returns: (screen_x, screen_y, scale, visible)
    Uses a simple pinhole camera model. Skips if rel_y <= clip.
    """
    clip = 0.0001
    if rel_y <= clip:
        return 0, 0, 0, False
    scale = focal_px / rel_y
    cx = screen_w // 2
    # Horizontal from rel_x; vertical from horizon plus height parallax
    sx = cx + rel_x * scale
    sy = horizon_px + (z_world - z_cam) * scale
    return sx, sy, scale, True

# =========================
# Z-buffered sprite render
# =========================

def ensure_zbuffer(screen_h: int):
    # Store per-scanline nearest depth (smaller rel_y = closer)
    return [float('inf')] * screen_h

def blit_scaled(screen, sprite, sx: float, sy: float, width_px: float, height_px: float):
    if width_px <= 0 or height_px <= 0:
        return
    scaled = pygame.transform.scale(sprite, (int(width_px), int(height_px)))
    screen.blit(scaled, (int(sx - width_px/2), int(sy - height_px)))

def render_sprite_world(screen, sprite, world_x: float, world_y: float, z_world: float,
                        cam: Camera, zbuf, focal_px: float, horizon_px: float):
    screen_w, screen_h = screen.get_size()
    rel_x, rel_y = to_camera_space(cam, world_x, world_y)
    sx, sy, scale, visible = project(rel_x, rel_y, z_world, cam.z, screen_w, screen_h, focal_px, horizon_px)
    if not visible:
        return
    # Basic z-buffer by scanline
    sy_i = int(sy)
    if sy_i < 1 or sy_i >= screen_h:
        return
    if rel_y >= zbuf[sy_i]:
        return
    zbuf[sy_i] = rel_y
    # Size heuristic (tune to taste)
    width_px = 120 * scale
    height_px = 90 * scale
    blit_scaled(screen, sprite, sx, sy, width_px, height_px)

# =========================
# Road rendering
# =========================

def render_road(screen, road_texture, road_path,
                cam: Camera, focal_px=200.0, horizon_px=60.0,
                max_forward=200.0, step_factor=150.0):
    """
    Draws the road as scanline slices sampled along the camera's forward ray.
    """
    screen_w, screen_h = screen.get_size()
    zbuf = ensure_zbuffer(screen_h)

    draw_distance = 1.0
    vertical = screen_h  # last written vertical to maintain ordering
    last_idx = 0

    while draw_distance < max_forward:
        last_vertical = vertical

        # Advance until we get a new vertical row to draw
        while vertical >= last_vertical and draw_distance < max_forward:
            draw_distance += draw_distance / step_factor

            # March forward in camera space
            world_x = cam.x + math.cos(cam.angle) * draw_distance
            world_y = cam.y + math.sin(cam.angle) * draw_distance

            # Map to spline for height
            last_idx = nearest_spline_index(world_x, world_y, road_path, last_idx)
            z = height_at_index(last_idx)

            # Project the point to find its screen row
            rel_x, rel_y = to_camera_space(cam, world_x, world_y)
            sx, sy, scale, visible = project(rel_x, rel_y, z, cam.z, screen_w, screen_h, focal_px, horizon_px)
            # Compute where to draw the slice (sy is center; make it an int row)
            vertical = int(sy)

        if draw_distance >= max_forward:
            break

        row = max(1, min(screen_h - 1, vertical))
        zbuf[row] = min(zbuf[row], draw_distance)

        # Choose a horizontal texture strip using last_idx
        tex_y = (10 * last_idx) % road_texture.get_height()
        road_slice = road_texture.subsurface((0, tex_y, road_texture.get_width(), 1))

        # Base ground color fallback (optional)
        # pygame.draw.rect(screen, (50, 130, 50), (0, row, screen_w, 1))

        # Parallax-based color tweak (optional aesthetic)
        colour = (
            max(0, min(255, int(50 - draw_distance / 3))),
            max(0, min(255, int(130 - draw_distance))),
            max(0, min(255, int(50 - (z - cam.z) / 20 + 30 * math.sin(last_idx))))
        )
        pygame.draw.rect(screen, colour, (0, row, screen_w, 1))

        # Stretch the 1px slice across screen width with perspective scale
        # Width grows nearer to the camera
        rel_x, rel_y = to_camera_space(cam,
                                       cam.x + math.cos(cam.angle) * draw_distance,
                                       cam.y + math.sin(cam.angle) * draw_distance)
        _, sy, scale, visible = project(rel_x, rel_y, z, cam.z, screen_w, screen_h, focal_px, horizon_px)
        width_px = max(1, int(screen_w * (0.9 + 0.6 * scale)))  # tune the shape of the road
        blit_scaled(screen, road_slice, screen_w / 2, row, width_px, 1)

    return zbuf  # return z-buffer for use by sprites

# =========================
# HUD (with proper FPS)
# =========================

def render_hud(screen, player, lap_time, clock):
    font = pygame.font.SysFont("Arial", 16)
    fps = int(clock.get_fps())
    speed_kmh = int(abs(player.velocity) * 3.6)

    hud_lines = [
        f"FPS: {fps}",
        f"Speed: {speed_kmh} km/h",
        f"Gear: {player.gear}",
    ]
    x, y = 5, 5
    for line in hud_lines:
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 14

# =========================
# Example usage in your loop
# =========================

def render_frame(screen, mountains_texture, road_texture, car, trees, ai_cars, clock, road_path):
    # 1) Camera from player
    cam = Camera(x=car.x, y=car.y, z=car.z, angle=car.angle)

    # 2) Background
    screen.blit(mountains_texture, (-65 - cam.angle * 82, 0))

    # 3) Road
    # horizon and focal can be tuned; they control perspective feeling
    zbuf = render_road(screen, road_texture, road_path, cam, focal_px=200.0, horizon_px=60.0,
                       max_forward=220.0, step_factor=150.0)

    # 4) World sprites (trees, AI cars) – provide world positions
    # Trees
    for t in trees:
        # Trees are on ground plane; give them some height offset if wanted
        world_x = t.x
        world_y = t.y
        z_world = 0.0  # ground
        # You probably want a custom sprite size; you can also override in render_sprite_world
        render_sprite_world(screen, t.sprite, world_x, world_y, z_world, cam, zbuf, focal_px=200.0, horizon_px=60.0)

    # AI cars
    for c in ai_cars:
        world_x = c.x
        world_y = c.y if hasattr(c, "y") else 0.0
        z_world = 0.0
        render_sprite_world(screen, c.sprite, world_x, world_y, z_world, cam, zbuf, focal_px=200.0, horizon_px=60.0)

    # 5) Player car overlay (screen-fixed or world-projected)
    # If you want a cockpit view, blit a centered sprite:
    # screen.blit(car_sprite, (100, 120))  # your old overlay

    # 6) HUD
    render_hud(screen, car, lap_time=0.0, clock=clock)
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
        # Recalculate steer_factor each frame so low speeds turn sharper
        self.steer_factor = self.steer_base * (2.0 - min(self.velocity / 20, 1))
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
       # self.angle = max(-max_steer, min(max_steer, self.angle))

if __name__ == "__main__":

    pygame.init()
    asyncio.run(main())
    pygame.quit()