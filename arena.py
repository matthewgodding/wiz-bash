import pygame

ARENA_COLOR = (40, 40, 60)
BORDER_COLOR = (100, 100, 140)
FLOOR_COLOR = (55, 55, 75)


class Arena:
    def __init__(self, screen_w, screen_h, margin=60, left_margin=None, right_margin=None):
        lm = left_margin  if left_margin  is not None else margin
        rm = right_margin if right_margin is not None else margin
        self.rect = pygame.Rect(lm, margin, screen_w - lm - rm, screen_h - margin * 2)

    def draw(self, surface):
        # Floor
        pygame.draw.rect(surface, FLOOR_COLOR, self.rect)
        # Border
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 4)
