import pygame, math, random
from collections import deque
from config import (SEG_RADIUS, SEG_SPACING, HEAD_RADIUS, INIT_SEGS,
                    PLAYER_SPEED, TURN_SPEED_RAD, RESPAWN_PROTECT,
                    WORLD_W, WORLD_H, SCREEN_W, SCREEN_H,
                    SPEED_SCALE_EXP, SPEED_SCALE_MIN, SPEED_SCALE_MAX)


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _on_screen(sx, sy, margin=HEAD_RADIUS + 6):
    return -margin < sx < SCREEN_W + margin and -margin < sy < SCREEN_H + margin


class Dragon:
    """
    Continuous-movement dragon.
    Trail stores (x,y) positions at SEG_SPACING intervals of travel.
    """

    def __init__(self, x, y, angle, skin, seg_count=INIT_SEGS, speed=PLAYER_SPEED):
        self.x       = float(x)
        self.y       = float(y)
        self.angle   = float(angle)
        self.base_speed = speed
        self.speed   = speed
        self.skin    = skin
        self.alive   = True
        self.dead    = False
        self.score   = 0

        self._trail:  deque = deque()
        self._travel: float = 0.0
        self.seg_count: int = seg_count

        for i in range(seg_count + 6):
            sx = x - math.cos(angle) * i * SEG_SPACING
            sy = y - math.sin(angle) * i * SEG_SPACING
            self._trail.append((sx, sy))

        self.protect_timer = 0.0

        # prev position for swept-sphere collision
        self.prev_x = float(x)
        self.prev_y = float(y)

    # ── movement ──────────────────────────────────────────────────────────────
    def move(self, dt: float):
        self.prev_x, self.prev_y = self.x, self.y
        dist = self.speed * dt
        self.x += math.cos(self.angle) * dist
        self.y += math.sin(self.angle) * dist
        self._travel += dist
        while self._travel >= SEG_SPACING:
            self._travel -= SEG_SPACING
            self._trail.appendleft((self.x, self.y))
        self._trim()

    def _trim(self):
        cap = self.seg_count + 8
        while len(self._trail) > cap:
            self._trail.pop()

    def turn(self, delta_rad: float):
        self.angle = (self.angle + delta_rad) % math.tau

    # ── size ──────────────────────────────────────────────────────────────────
    def grow(self, n: int):
        self.seg_count = max(5, self.seg_count + n)

    def shrink(self, n: int):
        self.seg_count = max(INIT_SEGS // 2, self.seg_count - n)

    def grow_flat(self, n: int):
        """Add n segments, extending trail if needed."""
        self.seg_count += n
        if self._trail:
            tail = self._trail[-1]
            needed = self.seg_count + 8 - len(self._trail)
            for _ in range(max(0, needed)):
                self._trail.append(tail)

    # ── speed scaling by body size ────────────────────────────────────────────
    def recalc_speed(self, effect_mult: float = 1.0):
        ratio = INIT_SEGS / max(self.seg_count, INIT_SEGS)
        factor = max(SPEED_SCALE_MIN, min(SPEED_SCALE_MAX, ratio ** SPEED_SCALE_EXP))
        self.speed = self.base_speed * factor * effect_mult

    # ── collision ─────────────────────────────────────────────────────────────
    @property
    def head_rect(self):
        r = HEAD_RADIUS
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def body_segments(self):
        trail = list(self._trail)
        skip  = max(8, int(HEAD_RADIUS * 4 // SEG_SPACING) + 1)
        for i in range(skip, min(len(trail), self.seg_count + 2)):
            yield trail[i]

    def head_hits_body(self, other: 'Dragon') -> bool:
        """Swept-sphere check: test current head AND midpoint to last frame."""
        threshold = (HEAD_RADIUS * 0.70 + SEG_RADIUS * 0.70) ** 2  # ~17 px
        hx,  hy  = self.x,      self.y
        mx,  my  = (self.x + self.prev_x) * 0.5, (self.y + self.prev_y) * 0.5
        for sx, sy in other.body_segments():
            if ((hx-sx)**2 + (hy-sy)**2 < threshold or
                    (mx-sx)**2 + (my-sy)**2 < threshold):
                return True
        return False

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        if self.protect_timer > 0 and int(self.protect_timer * 8) % 2 == 0:
            return

        trail = list(self._trail)
        skin  = self.skin
        total = min(self.seg_count, len(trail))

        # ── body segments (back to front) ─────────────────────
        for i in range(total - 1, -1, -1):
            px, py = trail[i]
            sx = px - cam_x
            sy = py - cam_y
            if not _on_screen(sx, sy):
                continue
            t = i / max(total - 1, 1)
            color = _lerp_color(skin['body'], skin['body2'], t)
            r = max(4, int(SEG_RADIUS * (1.0 - t * 0.40)))
            pygame.draw.circle(surf, color, (int(sx), int(sy)), r)

            # scale mark every 4 segments
            if i % 4 == 0 and r > 6:
                sc = _lerp_color(skin['body'], (255, 255, 255), 0.15)
                pygame.draw.circle(surf, sc, (int(sx), int(sy)), r - 3)

            # spine ridge every 3 segments (on the "back" side)
            if i % 3 == 0 and i + 1 < len(trail) and i > 0 and r > 5:
                nx = trail[i-1][0] - trail[i][0]
                ny = trail[i-1][1] - trail[i][1]
                nd = math.hypot(nx, ny)
                if nd > 0.01:
                    nx, ny = nx/nd, ny/nd
                    perp_x = -ny
                    perp_y =  nx
                    rx = int(sx + perp_x * (r + 3))
                    ry = int(sy + perp_y * (r + 3))
                    pygame.draw.circle(surf, skin['glow'], (rx, ry), max(2, r // 3))

        # ── head ──────────────────────────────────────────────
        hsx = int(self.x - cam_x)
        hsy = int(self.y - cam_y)
        if _on_screen(hsx, hsy, HEAD_RADIUS + 12):
            _draw_dragon_head(surf, skin, self.angle, hsx, hsy)


# ── Dragon Head ───────────────────────────────────────────────────────────────
def _draw_dragon_head(surf: pygame.Surface, skin: dict, angle: float, hx: int, hy: int):
    r = HEAD_RADIUS
    f  = (math.cos(angle),            math.sin(angle))
    rt = (math.cos(angle + math.pi/2), math.sin(angle + math.pi/2))

    def pt(fd, rd):
        return (hx + f[0]*fd + rt[0]*rd,
                hy + f[1]*fd + rt[1]*rd)

    def ipt(fd, rd):
        x, y = pt(fd, rd)
        return (int(x), int(y))

    # ── outer glow halo ──────────────────────────────────────
    gs = pygame.Surface((r*6, r*6), pygame.SRCALPHA)
    pygame.draw.circle(gs, (*skin['glow'], 38), (r*3, r*3), int(r*2.4))
    surf.blit(gs, (hx - r*3, hy - r*3))

    # ── main head polygon (dragon-shaped) ────────────────────
    head_pts = [
        ipt( r*1.5,  0),          # snout tip
        ipt( r*0.9,  r*0.85),     # right cheek
        ipt(-r*0.3,  r*0.95),     # right jaw corner
        ipt(-r*0.8,  r*0.55),     # right back
        ipt(-r*0.85, 0),          # back center
        ipt(-r*0.8, -r*0.55),     # left back
        ipt(-r*0.3, -r*0.95),     # left jaw corner
        ipt( r*0.9, -r*0.85),     # left cheek
    ]
    pygame.draw.polygon(surf, skin['head'], head_pts)

    # ── upper cranium ridge (slightly lighter) ────────────────
    cranium = _lerp_color(skin['head'], (255, 255, 255), 0.12)
    cran_pts = [
        ipt( r*0.2,  r*0.5), ipt(-r*0.1,  r*0.7),
        ipt(-r*0.7,  r*0.4), ipt(-r*0.7, -r*0.4),
        ipt(-r*0.1, -r*0.7), ipt( r*0.2, -r*0.5),
    ]
    pygame.draw.polygon(surf, cranium, cran_pts)

    # ── jaw line ─────────────────────────────────────────────
    jaw_c = tuple(max(0, c - 30) for c in skin['head'])
    jaw_pts = [
        ipt(r*1.5,  0),
        ipt(r*0.7,  r*0.5),
        ipt(r*0.1,  r*0.5),
        ipt(r*0.1, -r*0.5),
        ipt(r*0.7, -r*0.5),
    ]
    pygame.draw.lines(surf, jaw_c, False, jaw_pts, 2)

    # ── teeth (small triangles along jaw) ────────────────────
    tooth_c = (230, 230, 200)
    for side, toff in (( 1, r*0.55), (-1, -r*0.55)):
        for tf in (0.9, 0.6, 0.3):
            tx, ty = pt(r*tf, toff)
            tip = (int(tx + rt[0]*side*5 + f[0]*4),
                   int(ty + rt[1]*side*5 + f[1]*4))
            b1  = ipt(r*tf + 4, toff - 4*side)
            b2  = ipt(r*tf - 4, toff - 4*side)
            pygame.draw.polygon(surf, tooth_c, [tip, b1, b2])

    # ── horns ────────────────────────────────────────────────
    for side in (-1, 1):
        hbase = pt(-r*0.15, r*0.65*side)
        hmid  = pt(-r*0.6,  r*1.05*side)
        htip  = pt(-r*1.2,  r*0.8*side)
        horn_poly = [
            ipt(-r*0.05, r*0.50*side),
            ipt(-r*0.25, r*0.80*side),
            (int(htip[0]), int(htip[1])),
            ipt(-r*0.55, r*1.10*side),
            ipt(-r*0.05, r*0.80*side),
        ]
        pygame.draw.polygon(surf, skin['head'], horn_poly)
        pygame.draw.lines(surf, skin['glow'], False,
                          [ipt(-r*0.1, r*0.55*side), (int(hmid[0]),int(hmid[1])),
                           (int(htip[0]),int(htip[1]))], 2)

    # ── eyes ─────────────────────────────────────────────────
    for side in (-1, 1):
        ex, ey = ipt(r*0.55, r*0.52*side)
        # eye whites
        pygame.draw.circle(surf, skin['eye'], (ex, ey), 5)
        # vertical-slit pupil
        slit = [(ex,   ey-3), (ex+2, ey-1),
                (ex+2, ey+1), (ex,   ey+3),
                (ex-2, ey+1), (ex-2, ey-1)]
        pygame.draw.polygon(surf, skin['pupil'], slit)
        # eye glow ring
        pygame.draw.circle(surf, skin['eye'], (ex, ey), 5, 1)

    # ── nostrils ─────────────────────────────────────────────
    for side in (-1, 1):
        nx, ny = ipt(r*1.25, r*0.22*side)
        pygame.draw.circle(surf, tuple(max(0, c-50) for c in skin['head']), (nx, ny), 2)

    # ── head outline ─────────────────────────────────────────
    pygame.draw.polygon(surf, skin['glow'], head_pts, 1)
