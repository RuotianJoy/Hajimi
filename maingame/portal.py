import math

import pygame


class Portal:
    def __init__(self, x, y, width, height, target_map, portal_type="level_portal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.target_map = target_map
        self.portal_type = portal_type
        self.rect = pygame.Rect(x, y, width, height)
        self.animation_time = 0

    def update(self, dt):
        self.animation_time += dt

    def draw(self, screen):
        # 绘制传送门动画效果
        # 外圈发光效果
        glow_color = (100 + int(50 * abs(math.sin(self.animation_time * 3))),
                     200 + int(55 * abs(math.sin(self.animation_time * 2))),
                     255)
        pygame.draw.rect(screen, glow_color,
                        (self.x - 5, self.y - 5, self.width + 10, self.height + 10), 3)

        # 内部传送门
        portal_color = (50 + int(30 * abs(math.sin(self.animation_time * 4))),
                       150 + int(50 * abs(math.sin(self.animation_time * 3))),
                       200 + int(55 * abs(math.sin(self.animation_time * 2))))
        pygame.draw.rect(screen, portal_color, self.rect)

        # 中心亮点
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        center_color = (255, 255, 255, int(128 + 127 * abs(math.sin(self.animation_time * 5))))
        pygame.draw.circle(screen, center_color[:3], (center_x, center_y), 8)

        # 传送门标识文字
        font = pygame.font.Font(None, 24)
        text = font.render("NEXT", True, (255, 255, 255))
        text_rect = text.get_rect(center=(center_x, self.y - 20))
        screen.blit(text, text_rect)
