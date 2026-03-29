import pygame
import sys
import math

def main():
    pygame.init()

    screen_size = [800, 600]
    screen = pygame.display.set_mode(screen_size, pygame.SCALED)
    pygame.display.set_caption("Pseudo-3D Road")

    clock = pygame.time.Clock()

    try:
        road_texture = pygame.image.load("roadTexture.png").convert()
    except pygame.error:
        print("Error: Could not load 'roadTexture.png'. Make sure it's in the same folder.")
        pygame.quit()
        sys.exit()

    running = True
    while running:
        delta = clock.tick(60) / 1000.0  # 60 FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((100, 150, 200))  # Sky blue background

        for i in range(180):
            perspective = i / 180
            road_width = int(screen_size[0] * 0.5 * (1 - perspective))
            x = screen_size[0] // 2 - road_width // 2
            y = int(screen_size[1] * (i / 180))
            slice_y = int(road_texture.get_height() * perspective)
            slice_rect = pygame.Rect(0, slice_y, road_texture.get_width(), 1)
            scaled_slice = pygame.transform.scale(road_texture.subsurface(slice_rect), (road_width, 2))
            screen.blit(scaled_slice, (x, y))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()