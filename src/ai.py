import math, random
from config import (TURN_SPEED_RAD, WORLD_W, WORLD_H, PLAYER_SPEED,
                    INIT_SEGS, SPEED_SCALE_EXP, SPEED_SCALE_MIN, SPEED_SCALE_MAX)


WALL_MARGIN  = 200
DANGER_DIST  = 90


class AIController:
    def __init__(self, dragon, world, difficulty: dict):
        self.dragon     = dragon
        self.world      = world
        self.react      = difficulty['react']
        self.base_speed = dragon.speed
        self.target     = None
        self._timer     = random.uniform(0, 0.4)
        self._interval  = 0.22 + (1 - self.react) * 0.30

    def update(self, dt: float):
        d = self.dragon
        if d.dead or not d.alive:
            return
        if getattr(self.world, 'ai_frozen_timer', 0) > 0:
            return   # frozen by player's freeze item

        # Speed scale by size
        ratio  = INIT_SEGS / max(d.seg_count, INIT_SEGS)
        factor = max(SPEED_SCALE_MIN, min(SPEED_SCALE_MAX, ratio ** SPEED_SCALE_EXP))
        d.speed = self.base_speed * factor

        self._timer += dt
        if self._timer >= self._interval:
            self._timer = 0.0
            self._pick_target()

        desired = self._desired_angle()
        if desired is not None:
            self._steer(desired, dt)

        self._avoid_walls(dt)
        self._avoid_bodies(dt)
        d.move(dt)
        if d.protect_timer > 0:
            d.protect_timer = max(0.0, d.protect_timer - dt)

        # AI collects items
        self._collect_items()

    # ── targeting ─────────────────────────────────────────────────────────────
    def _pick_target(self):
        best, pos = float('inf'), None
        dx, dy    = self.dragon.x, self.dragon.y

        def _try(items, w=1.0):
            nonlocal best, pos
            for it in items:
                if not it.alive:
                    continue
                d = math.hypot(it.x - dx, it.y - dy) * w
                if d < best:
                    best, pos = d, (it.x, it.y)

        _try(self.world.fruits, 0.45)
        _try(self.world.stars,  0.80)
        _try(self.world.meats,  1.00)
        self.target = pos

    def _desired_angle(self):
        if self.target is None:
            return None
        dx = self.target[0] - self.dragon.x
        dy = self.target[1] - self.dragon.y
        if dx*dx + dy*dy < 18*18:
            self.target = None
            return None
        return math.atan2(dy, dx)

    # ── steering ──────────────────────────────────────────────────────────────
    def _steer(self, desired: float, dt: float):
        diff = _adiff(desired, self.dragon.angle)
        cap  = TURN_SPEED_RAD * dt * (0.55 + self.react * 0.65)
        self.dragon.turn(max(-cap, min(cap, diff)))

    def _avoid_walls(self, dt: float):
        x, y  = self.dragon.x, self.dragon.y
        safe  = None
        if x < WALL_MARGIN:                safe = 0.0
        elif x > WORLD_W - WALL_MARGIN:    safe = math.pi
        elif y < WALL_MARGIN:              safe = math.pi / 2
        elif y > WORLD_H - WALL_MARGIN:    safe = -math.pi / 2
        if safe is not None:
            diff = _adiff(safe, self.dragon.angle)
            cap  = TURN_SPEED_RAD * dt * 2.0
            self.dragon.turn(max(-cap, min(cap, diff)))

    def _avoid_bodies(self, dt: float):
        hx, hy = self.dragon.x, self.dragon.y
        for d in self.world.dragons:
            if d is self.dragon or d.dead:
                continue
            for sx, sy in d.body_segments():
                dist = math.hypot(hx - sx, hy - sy)
                if dist < DANGER_DIST:
                    away = math.atan2(hy - sy, hx - sx)
                    self._steer(away, dt)
                    return

    # ── item collection ───────────────────────────────────────────────────────
    def _collect_items(self):
        d  = self.dragon
        hr = 14 + 10   # head + item radius threshold

        for meat in self.world.meats:
            if meat.alive and math.hypot(d.x - meat.x, d.y - meat.y) < hr:
                meat.alive = False
                d.grow(1)

        for star in self.world.stars:
            if star.alive and math.hypot(d.x - star.x, d.y - star.y) < hr:
                star.alive = False
                d.grow(1)

        for fruit in self.world.fruits:
            if fruit.alive and math.hypot(d.x - fruit.x, d.y - fruit.y) < hr:
                fruit.alive = False
                d.grow(2)


def _adiff(target, current):
    d = target - current
    while d >  math.pi: d -= math.tau
    while d < -math.pi: d += math.tau
    return d
