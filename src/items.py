import pygame, math, random
from config import (SCREEN_W, SCREEN_H,
                    STAR_COLOR, STAR_GLOW, FRUIT_COLORS, MEAT_COLOR, MEAT_LIFETIME,
                    SKINS, SKIN_FRUIT_DATA)


# ── helpers ──────────────────────────────────────────────────────────────────
def _star_poly(cx, cy, r, points=5):
    coords = []
    for i in range(points * 2):
        a = math.pi / points * i - math.pi / 2
        d = r if i % 2 == 0 else r * 0.42
        coords.append((cx + math.cos(a) * d, cy + math.sin(a) * d))
    return coords


def _hex_poly(cx, cy, r):
    return [(cx + math.cos(math.pi/3*i)*r, cy + math.sin(math.pi/3*i)*r) for i in range(6)]


def ws(wx, wy, cam_x, cam_y):
    return wx - cam_x, wy - cam_y


def on_screen(sx, sy, margin=34):
    return -margin < sx < SCREEN_W + margin and -margin < sy < SCREEN_H + margin


# ── Star ─────────────────────────────────────────────────────────────────────
class Star:
    __slots__ = ('x', 'y', 'r', 'phase', 'alive')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 9
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 3.5

    def pull(self, tx, ty, speed, dt):
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            self.x += dx / dist * speed * dt
            self.y += dy / dist * speed * dt

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy):
            return
        r = self.r + math.sin(self.phase) * 2
        gs = pygame.Surface((int(r * 4), int(r * 4)), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*STAR_GLOW, 50), (int(r*2), int(r*2)), int(r*2.5))
        surf.blit(gs, (int(sx - r*2), int(sy - r*2)))
        pygame.draw.polygon(surf, STAR_COLOR, _star_poly(sx, sy, r))

    @property
    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)


# ── Fruit ────────────────────────────────────────────────────────────────────
class Fruit:
    __slots__ = ('x', 'y', 'r', 'color', 'phase', 'alive', 'kind')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 13
        self.kind  = random.randint(0, len(FRUIT_COLORS) - 1)
        self.color = FRUIT_COLORS[self.kind]
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 2.2

    def pull(self, tx, ty, speed, dt):
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            self.x += dx / dist * speed * dt
            self.y += dy / dist * speed * dt

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy):
            return
        r = int(self.r + math.sin(self.phase) * 2.5)
        gs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.color, 55), (r*2, r*2), r*3)
        surf.blit(gs, (int(sx-r*2), int(sy-r*2)))
        pygame.draw.circle(surf, self.color, (int(sx), int(sy)), r)
        pygame.draw.circle(surf, (255,255,255), (int(sx)-r//3, int(sy)-r//3), max(2, r//4))

    @property
    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)


# ── MeatChunk ────────────────────────────────────────────────────────────────
class MeatChunk:
    __slots__ = ('x', 'y', 'r', 'color', 'value', 'lifetime', 'alive', 'vx', 'vy')

    def __init__(self, x, y, color, value=1):
        self.x = float(x) + random.uniform(-20, 20)
        self.y = float(y) + random.uniform(-20, 20)
        self.r        = 6
        self.color    = color
        self.value    = value
        self.lifetime = MEAT_LIFETIME
        self.alive    = True
        ang = random.uniform(0, math.tau)
        spd = random.uniform(0, 40)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        # slow drift
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.92
        self.vy *= 0.92

    def pull(self, tx, ty, speed, dt):
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            self.x += dx/dist * speed * dt
            self.y += dy/dist * speed * dt

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy, 20):
            return
        alpha = min(255, int(self.lifetime / MEAT_LIFETIME * 255))
        tmp = pygame.Surface((self.r*2+2, self.r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (*self.color, alpha), (self.r+1, self.r+1), self.r)
        surf.blit(tmp, (int(sx-self.r-1), int(sy-self.r-1)))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── Magnet ───────────────────────────────────────────────────────────────────
class Magnet:
    __slots__ = ('x', 'y', 'r', 'phase', 'alive')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 16
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 2

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy):
            return
        r   = int(self.r + math.sin(self.phase) * 2)
        # glow
        gs = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (50, 160, 255, 50), (r*2+r//2, r*2+r//2), r*2)
        surf.blit(gs, (int(sx-r*2-r//2), int(sy-r*2-r//2)))
        # horseshoe arc
        rect = pygame.Rect(int(sx-r), int(sy-r), r*2, r*2)
        pygame.draw.arc(surf, (60, 160, 255), rect, 0, math.pi, 5)
        # poles
        pygame.draw.rect(surf, (255, 60, 60),   (int(sx-r-3), int(sy-4), 7, r//2+4))
        pygame.draw.rect(surf, (60,  60, 255),  (int(sx+r-4), int(sy-4), 7, r//2+4))
        # labels
        _draw_small_text(surf, "N", (255,60,60),  int(sx-r+1), int(sy+r//2-3))
        _draw_small_text(surf, "S", (60,60,255),  int(sx+r-3), int(sy+r//2-3))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── GrowthBoost ──────────────────────────────────────────────────────────────
class GrowthBoost:
    __slots__ = ('x', 'y', 'r', 'phase', 'alive')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 18
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 1.8

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy):
            return
        r   = int(self.r + math.sin(self.phase) * 3)
        # outer glow
        gs = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (80, 255, 80, 45), (r*2+r//2, r*2+r//2), r*2)
        surf.blit(gs, (int(sx-r*2-r//2), int(sy-r*2-r//2)))
        # body circle
        pygame.draw.circle(surf, (20, 160, 20), (int(sx), int(sy)), r)
        pygame.draw.circle(surf, (80, 255, 80),  (int(sx), int(sy)), r, 2)
        # up-arrow symbol
        aw = r // 2
        arrow = [(int(sx), int(sy-aw-4)), (int(sx+aw), int(sy+2)),
                 (int(sx+aw//2), int(sy+2)), (int(sx+aw//2), int(sy+aw)),
                 (int(sx-aw//2), int(sy+aw)), (int(sx-aw//2), int(sy+2)), (int(sx-aw), int(sy+2))]
        pygame.draw.polygon(surf, (160, 255, 160), arrow)
        _draw_small_text(surf, "500", (220,255,220), int(sx-10), int(sy+r-10))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── SkinFruit ────────────────────────────────────────────────────────────────
class SkinFruit:
    __slots__ = ('x', 'y', 'r', 'skin_id', 'color', 'glow', 'label', 'phase', 'alive')

    def __init__(self, x, y, skin_id: str):
        self.x, self.y = float(x), float(y)
        self.r       = 15
        self.skin_id = skin_id
        data         = SKIN_FRUIT_DATA[skin_id]
        skin         = SKINS[skin_id]
        self.color   = skin['body']
        self.glow    = data['glow']
        self.label   = data['label']
        self.phase   = random.uniform(0, math.tau)
        self.alive   = True

    def update(self, dt):
        self.phase += dt * 2.5

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy):
            return
        r = int(self.r + math.sin(self.phase) * 3)
        # glow
        gs = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.glow, 55), (r*2+r//2, r*2+r//2), r*2)
        surf.blit(gs, (int(sx-r*2-r//2), int(sy-r*2-r//2)))
        # hexagon body
        hex_pts = [(int(sx+math.cos(math.pi/3*i)*r), int(sy+math.sin(math.pi/3*i)*r)) for i in range(6)]
        pygame.draw.polygon(surf, self.color, hex_pts)
        pygame.draw.polygon(surf, self.glow,  hex_pts, 2)
        # shine
        pygame.draw.circle(surf, (255,255,255), (int(sx)-r//4, int(sy)-r//4), max(2, r//5))
        _draw_small_text(surf, self.label, self.glow, int(sx-18), int(sy+r+1))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── ShieldItem ───────────────────────────────────────────────────────────────
class ShieldItem:
    __slots__ = ('x', 'y', 'r', 'phase', 'alive')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 16
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 1.6

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy): return
        r = int(self.r + math.sin(self.phase) * 2.5)
        # cyan glow
        gs = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (60, 220, 255, 50), (r*2+r//2, r*2+r//2), r*2)
        surf.blit(gs, (int(sx-r*2-r//2), int(sy-r*2-r//2)))
        # shield shape (pentagon-ish)
        pts = [(int(sx + math.cos(math.pi*2/5*i - math.pi/2)*r),
                int(sy + math.sin(math.pi*2/5*i - math.pi/2)*r)) for i in range(5)]
        pygame.draw.polygon(surf, (20, 100, 160), pts)
        pygame.draw.polygon(surf, (80, 220, 255), pts, 3)
        # inner shine
        pygame.draw.circle(surf, (200, 240, 255), (int(sx)-r//4, int(sy)-r//4), max(2, r//4))
        _draw_small_text(surf, "护盾", (180, 240, 255), int(sx-12), int(sy+r+1))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── FreezeItem ───────────────────────────────────────────────────────────────
class FreezeItem:
    __slots__ = ('x', 'y', 'r', 'phase', 'alive')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 15
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 2.8

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy): return
        r = int(self.r + math.sin(self.phase) * 2)
        # icy blue glow
        gs = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (160, 220, 255, 55), (r*2+r//2, r*2+r//2), r*2)
        surf.blit(gs, (int(sx-r*2-r//2), int(sy-r*2-r//2)))
        # snowflake: 6 spokes
        for i in range(6):
            a = math.pi / 3 * i
            ex = int(sx + math.cos(a) * r)
            ey = int(sy + math.sin(a) * r)
            pygame.draw.line(surf, (180, 240, 255), (int(sx), int(sy)), (ex, ey), 2)
            # small crossbars
            for t in (0.4, 0.7):
                mx2 = int(sx + math.cos(a) * r * t)
                my2 = int(sy + math.sin(a) * r * t)
                pygame.draw.line(surf, (140, 210, 255),
                                 (int(mx2 + math.cos(a+math.pi/2)*4),
                                  int(my2 + math.sin(a+math.pi/2)*4)),
                                 (int(mx2 + math.cos(a-math.pi/2)*4),
                                  int(my2 + math.sin(a-math.pi/2)*4)), 1)
        pygame.draw.circle(surf, (200, 245, 255), (int(sx), int(sy)), r//3)
        _draw_small_text(surf, "冰冻", (180, 240, 255), int(sx-12), int(sy+r+1))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── BombItem ─────────────────────────────────────────────────────────────────
class BombItem:
    __slots__ = ('x', 'y', 'r', 'phase', 'alive')

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r     = 16
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt):
        self.phase += dt * 2.2

    def draw(self, surf, cam_x, cam_y):
        sx, sy = ws(self.x, self.y, cam_x, cam_y)
        if not on_screen(sx, sy): return
        r = int(self.r + math.sin(self.phase) * 2)
        # orange glow
        gs = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255, 120, 20, 55), (r*2+r//2, r*2+r//2), r*2)
        surf.blit(gs, (int(sx-r*2-r//2), int(sy-r*2-r//2)))
        # bomb body
        pygame.draw.circle(surf, (60, 40, 40),   (int(sx), int(sy)), r)
        pygame.draw.circle(surf, (220, 80, 20),  (int(sx), int(sy)), r, 3)
        # explosion rays
        for i in range(8):
            a   = math.pi / 4 * i + self.phase * 0.3
            rx  = int(sx + math.cos(a) * (r + 6))
            ry  = int(sy + math.sin(a) * (r + 6))
            pygame.draw.line(surf, (255, 160, 40), (int(sx), int(sy)), (rx, ry), 2)
        # fuse
        pygame.draw.line(surf, (200, 180, 100),
                         (int(sx), int(sy-r)), (int(sx+6), int(sy-r-8)), 2)
        pygame.draw.circle(surf, (255, 220, 80), (int(sx+6), int(sy-r-8)), 3)
        _draw_small_text(surf, "爆炸", (255, 160, 60), int(sx-12), int(sy+r+1))

    @property
    def rect(self):
        return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


# ── utility ──────────────────────────────────────────────────────────────────
_small_font = None

def _draw_small_text(surf, text, color, x, y):
    global _small_font
    if _small_font is None:
        try:
            _small_font = pygame.font.SysFont('Microsoft YaHei', 12)
        except Exception:
            _small_font = pygame.font.Font(None, 14)
    img = _small_font.render(text, True, color)
    surf.blit(img, (x, y))
