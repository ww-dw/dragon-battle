import math, random
import pygame
from config import (
    WORLD_W, WORLD_H, SCREEN_W, SCREEN_H,
    INIT_SEGS, PLAYER_SPEED, RESPAWN_PROTECT, MAX_REVIVALS,
    STAR_SPAWN_INTERVAL, MAX_STARS, MAX_FRUITS,
    STAR_DOUBLE_AT, FRUIT_DOUBLE_AT, FRUIT_FROM_STARS,
    MEAT_GROWTH, SEG_RADIUS, HEAD_RADIUS,
    SCORE_STAR, SCORE_FRUIT, SCORE_MEAT, SCORE_KILL,
    AI_SKINS, BG_COLOR, GRID_COLOR, SKINS,
    TURN_SPEED_RAD,
    MAGNET_SPAWN_INTERVAL, MAGNET_DURATION, MAGNET_RANGE, MAGNET_PULL_SPEED,
    GROWTH_SPAWN_INTERVAL, GROWTH_BOOST_SEGS,
    SKIN_FRUIT_SPAWN_INTERVAL, SKIN_FRUIT_DATA,
    EFFECT_SPEED, EFFECT_INVINCIBLE, EFFECT_RAGE, EFFECT_SCORE, EFFECT_FREEZE, EFFECT_PULSE_R,
    BOOST_SPEED_MULT, BOOST_DRAIN_INTERVAL, BOOST_MIN_SEGS,
    SHIELD_SPAWN_INTERVAL, FREEZE_SPAWN_INTERVAL, BOMB_SPAWN_INTERVAL, BOMB_MEAT_COUNT,
)
from dragon import Dragon
from items  import (Star, Fruit, MeatChunk, Magnet, GrowthBoost, SkinFruit,
                    ShieldItem, FreezeItem, BombItem)
from ai     import AIController

RESPAWN_DELAY = 1.8


class World:
    def __init__(self, player_skin_id: str, difficulty: dict):
        self.difficulty   = difficulty
        self.skin_id      = player_skin_id
        player_skin       = SKINS[player_skin_id]

        # ── player ────────────────────────────────────────────
        px, py = WORLD_W // 2, WORLD_H // 2
        self.player = Dragon(px, py, 0.0, player_skin, INIT_SEGS, PLAYER_SPEED)
        self.revivals_left = MAX_REVIVALS
        self.player_dead   = False
        self.respawn_timer = 0.0

        # ── AI ────────────────────────────────────────────────
        self.ai_controllers: list[AIController] = []
        self.dragons: list[Dragon] = [self.player]
        for i in range(difficulty['ai_count']):
            self._spawn_ai(i)

        # ── basic items ───────────────────────────────────────
        self.stars:  list[Star]      = []
        self.fruits: list[Fruit]     = []
        self.meats:  list[MeatChunk] = []

        # ── special items ─────────────────────────────────────
        self.magnets:       list[Magnet]      = []
        self.growth_boosts: list[GrowthBoost] = []
        self.skin_fruits:   list[SkinFruit]   = []
        self.shields:       list[ShieldItem]  = []
        self.freezes:       list[FreezeItem]  = []
        self.bombs:         list[BombItem]    = []

        # ── item timers ───────────────────────────────────────
        self._star_timer    = 0.0
        self._magnet_timer  = random.uniform(MAGNET_SPAWN_INTERVAL  * 0.5, MAGNET_SPAWN_INTERVAL)
        self._growth_timer  = random.uniform(GROWTH_SPAWN_INTERVAL  * 0.5, GROWTH_SPAWN_INTERVAL)
        self._sfruit_timer  = random.uniform(SKIN_FRUIT_SPAWN_INTERVAL * 0.4, SKIN_FRUIT_SPAWN_INTERVAL)
        self._shield_timer  = random.uniform(SHIELD_SPAWN_INTERVAL  * 0.5, SHIELD_SPAWN_INTERVAL)
        self._freeze_timer  = random.uniform(FREEZE_SPAWN_INTERVAL  * 0.4, FREEZE_SPAWN_INTERVAL)
        self._bomb_timer    = random.uniform(BOMB_SPAWN_INTERVAL    * 0.3, BOMB_SPAWN_INTERVAL)

        # ── player star/fruit counters ────────────────────────
        self._star_count  = 0
        self._fruit_count = 0

        # pulse ring visual: (world_x, world_y, progress 0→1)
        self.pulse_effect: tuple | None = None
        # freeze ring visual
        self.freeze_effect: tuple | None = None
        # AI freeze timer
        self.ai_frozen_timer = 0.0

        # ── player status effects {name: remaining_seconds} ───
        self.effects = {
            'magnet':    0.0,
            'speed':     0.0,
            'invincible':0.0,
            'rage':      0.0,
            'shield':    0.0,   # 1.0 = active (count), 0 = none
            'freeze':    0.0,
            'score':     0.0,
        }
        self._boost_drain_acc = 0.0   # accumulator for speed-boost length drain
        self.boosting = False

        # ── score/stats ───────────────────────────────────────
        self.score     = 0
        self.kills     = 0
        self.game_over = False

        # ── camera ────────────────────────────────────────────
        self.cam_x = float(px - SCREEN_W // 2)
        self.cam_y = float(py - SCREEN_H // 2)

        # seed initial items
        for _ in range(10):
            self._spawn_star()
        for _ in range(3):
            self._spawn_fruit()

    # ══ spawn helpers ══════════════════════════════════════════════════════════
    def _safe_pos(self, margin=250, away_from_player=350):
        for _ in range(50):
            x = random.uniform(margin, WORLD_W - margin)
            y = random.uniform(margin, WORLD_H - margin)
            if math.hypot(x - self.player.x, y - self.player.y) > away_from_player:
                return x, y
        return (random.uniform(margin, WORLD_W - margin),
                random.uniform(margin, WORLD_H - margin))

    def _rand_pos(self, margin=80):
        return (random.uniform(margin, WORLD_W - margin),
                random.uniform(margin, WORLD_H - margin))

    def _spawn_ai(self, index: int):
        x, y  = self._safe_pos(300)
        angle = random.uniform(0, math.tau)
        skin  = AI_SKINS[index % len(AI_SKINS)]
        speed = PLAYER_SPEED * self.difficulty['speed_mult']
        d     = Dragon(x, y, angle, skin, INIT_SEGS, speed)
        ctrl  = AIController(d, self, self.difficulty)
        self.ai_controllers.append(ctrl)
        self.dragons.append(d)
        return d

    def _spawn_star(self):
        if len(self.stars) < MAX_STARS:
            x, y = self._rand_pos()
            self.stars.append(Star(x, y))

    def _spawn_fruit(self):
        if len(self.fruits) < MAX_FRUITS:
            x, y = self._rand_pos()
            self.fruits.append(Fruit(x, y))

    def _explode(self, dragon: Dragon):
        trail = list(dragon._trail)
        step  = max(1, len(trail) // 40)
        for i in range(0, len(trail), step):
            px, py = trail[i]
            self.meats.append(MeatChunk(px, py, dragon.skin['body']))

    # ══ main update ════════════════════════════════════════════════════════════
    def update(self, dt: float,
               turn_left: bool, turn_right: bool,
               mouse_angle: float | None,
               boosting: bool):
        if self.game_over:
            return

        # ── respawn countdown ─────────────────────────────────
        if self.player_dead:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self._respawn_player()
            return

        # ── player effects tick ───────────────────────────────
        for k in list(self.effects):
            if self.effects[k] > 0:
                self.effects[k] = max(0.0, self.effects[k] - dt)

        # ── player speed multiplier from effects ──────────────
        speed_mult = 1.0
        if self.effects['speed'] > 0:
            speed_mult *= 1.5
        if self.effects['rage']  > 0:
            speed_mult *= 2.0

        # ── speed boost (贪吃蛇大作战 mechanic) ──────────────
        self.boosting = False
        if boosting and self.player.seg_count > BOOST_MIN_SEGS:
            speed_mult   *= BOOST_SPEED_MULT
            self.boosting = True
            self._boost_drain_acc += dt
            while self._boost_drain_acc >= BOOST_DRAIN_INTERVAL:
                self._boost_drain_acc -= BOOST_DRAIN_INTERVAL
                self.player.shrink(1)
        else:
            self._boost_drain_acc = 0.0

        self.player.recalc_speed(speed_mult)

        # ── player input + move ───────────────────────────────
        self._handle_player_input(dt, turn_left, turn_right, mouse_angle)
        self.player.move(dt)
        if self.player.protect_timer > 0:
            self.player.protect_timer = max(0.0, self.player.protect_timer - dt)

        # ── AI update ─────────────────────────────────────────
        for ctrl in self.ai_controllers:
            ctrl.update(dt)

        # ── item timers & spawning ────────────────────────────
        self._star_timer += dt
        if self._star_timer >= STAR_SPAWN_INTERVAL:
            self._star_timer -= STAR_SPAWN_INTERVAL
            self._spawn_star()

        self._magnet_timer -= dt
        if self._magnet_timer <= 0 and len(self.magnets) == 0:
            x, y = self._rand_pos(150)
            self.magnets.append(Magnet(x, y))
            self._magnet_timer = MAGNET_SPAWN_INTERVAL + random.uniform(-10, 10)

        self._growth_timer -= dt
        if self._growth_timer <= 0 and len(self.growth_boosts) == 0:
            x, y = self._rand_pos(150)
            self.growth_boosts.append(GrowthBoost(x, y))
            self._growth_timer = GROWTH_SPAWN_INTERVAL + random.uniform(-15, 15)

        self._sfruit_timer -= dt
        if self._sfruit_timer <= 0:
            counts = {}
            for sf in self.skin_fruits:
                counts[sf.skin_id] = counts.get(sf.skin_id, 0) + 1
            for sid in SKIN_FRUIT_DATA:
                if counts.get(sid, 0) < 2:
                    x, y = self._rand_pos(150)
                    self.skin_fruits.append(SkinFruit(x, y, sid))
                    break
            self._sfruit_timer = SKIN_FRUIT_SPAWN_INTERVAL / 5 + random.uniform(-2, 2)

        self._shield_timer -= dt
        if self._shield_timer <= 0 and len(self.shields) == 0:
            x, y = self._rand_pos(150)
            self.shields.append(ShieldItem(x, y))
            self._shield_timer = SHIELD_SPAWN_INTERVAL + random.uniform(-10, 10)

        self._freeze_timer -= dt
        if self._freeze_timer <= 0 and len(self.freezes) == 0:
            x, y = self._rand_pos(150)
            self.freezes.append(FreezeItem(x, y))
            self._freeze_timer = FREEZE_SPAWN_INTERVAL + random.uniform(-10, 10)

        self._bomb_timer -= dt
        if self._bomb_timer <= 0 and len(self.bombs) < 2:
            x, y = self._rand_pos(150)
            self.bombs.append(BombItem(x, y))
            self._bomb_timer = BOMB_SPAWN_INTERVAL + random.uniform(-8, 8)

        # ── AI freeze tick ────────────────────────────────────
        if self.ai_frozen_timer > 0:
            self.ai_frozen_timer = max(0.0, self.ai_frozen_timer - dt)

        # ── update items ──────────────────────────────────────
        all_items = (self.stars + self.fruits + self.meats +
                     self.magnets + self.growth_boosts + self.skin_fruits +
                     self.shields + self.freezes + self.bombs)
        for it in all_items:
            it.update(dt)

        # ── magnet pull ───────────────────────────────────────
        if self.effects['magnet'] > 0:
            px, py = self.player.x, self.player.y
            for it in self.stars + self.fruits + self.meats:
                if it.alive:
                    dist = math.hypot(it.x - px, it.y - py)
                    if dist < MAGNET_RANGE and dist > 1:
                        it.pull(px, py, MAGNET_PULL_SPEED, dt)

        # ── pulse ring animation tick ─────────────────────────
        if self.pulse_effect is not None:
            px2, py2, prog = self.pulse_effect
            prog += dt / 0.55
            self.pulse_effect = (px2, py2, prog) if prog < 1.0 else None

        # ── freeze ring animation tick ────────────────────────
        if self.freeze_effect is not None:
            fx2, fy2, fprog = self.freeze_effect
            fprog += dt / 0.6
            self.freeze_effect = (fx2, fy2, fprog) if fprog < 1.0 else None

        # ── prune dead items ──────────────────────────────────
        self.stars        = [s  for s  in self.stars        if s.alive]
        self.fruits       = [f  for f  in self.fruits       if f.alive]
        self.meats        = [m  for m  in self.meats        if m.alive]
        self.magnets      = [m  for m  in self.magnets      if m.alive]
        self.growth_boosts= [g  for g  in self.growth_boosts if g.alive]
        self.skin_fruits  = [sf for sf in self.skin_fruits  if sf.alive]
        self.shields      = [sh for sh in self.shields      if sh.alive]
        self.freezes      = [fz for fz in self.freezes      if fz.alive]
        self.bombs        = [b  for b  in self.bombs        if b.alive]

        # ── player item collection ────────────────────────────
        self._collect_player_items()

        # ── collision checks ──────────────────────────────────
        self._check_collisions()

        # ── AI re-spawn to maintain count ────────────────────
        active = sum(1 for c in self.ai_controllers if not c.dragon.dead)
        while active < self.difficulty['ai_count'] and random.random() < dt * 0.25:
            idx = len(self.ai_controllers)
            self._spawn_ai(idx)
            active += 1

        # ── camera (smooth follow) ────────────────────────────
        tx = self.player.x - SCREEN_W / 2
        ty = self.player.y - SCREEN_H / 2
        self.cam_x += (tx - self.cam_x) * min(1.0, dt * 9)
        self.cam_y += (ty - self.cam_y) * min(1.0, dt * 9)

    # ══ input ══════════════════════════════════════════════════════════════════
    def _handle_player_input(self, dt, turn_left, turn_right, mouse_angle):
        # Mouse → smooth steer toward cursor
        if mouse_angle is not None:
            diff = mouse_angle - self.player.angle
            while diff >  math.pi: diff -= math.tau
            while diff < -math.pi: diff += math.tau
            cap = TURN_SPEED_RAD * dt
            self.player.turn(max(-cap, min(cap, diff)))
        # Keyboard always additive (1.5× rate, feels more responsive)
        kb = TURN_SPEED_RAD * dt * 1.5
        if turn_left:
            self.player.turn(-kb)
        if turn_right:
            self.player.turn( kb)

    # ══ player item collection ══════════════════════════════════════════════════
    def _collect_player_items(self):
        p  = self.player
        hr = HEAD_RADIUS + 14
        sc = 2 if self.effects['score'] > 0 else 1   # score multiplier

        # Stars
        for star in self.stars:
            if star.alive and math.hypot(p.x - star.x, p.y - star.y) < hr + star.r:
                star.alive = False
                self._star_count += 1
                self.score += SCORE_STAR * sc
                if self._star_count % FRUIT_FROM_STARS == 0:
                    self._spawn_fruit()
                if self._star_count % STAR_DOUBLE_AT == 0:
                    p.grow_flat(12)

        # Regular fruits
        for fruit in self.fruits:
            if fruit.alive and math.hypot(p.x - fruit.x, p.y - fruit.y) < hr + fruit.r:
                fruit.alive = False
                self._fruit_count += 1
                self.score += SCORE_FRUIT * sc
                if self._fruit_count % FRUIT_DOUBLE_AT == 0:
                    p.grow_flat(12)

        # Meat chunks
        for meat in self.meats:
            if meat.alive and math.hypot(p.x - meat.x, p.y - meat.y) < hr + meat.r:
                meat.alive = False
                self.score += SCORE_MEAT * sc
                p.grow(MEAT_GROWTH)

        # Magnet
        for mag in self.magnets:
            if mag.alive and math.hypot(p.x - mag.x, p.y - mag.y) < hr + mag.r:
                mag.alive = False
                self.effects['magnet'] = MAGNET_DURATION

        # Growth boost
        for gb in self.growth_boosts:
            if gb.alive and math.hypot(p.x - gb.x, p.y - gb.y) < hr + gb.r:
                gb.alive = False
                p.grow_flat(GROWTH_BOOST_SEGS)
                self.score += 200 * sc

        # Skin-specific fruits — any player can collect any type; effect from fruit's skin
        for sf in self.skin_fruits:
            if sf.alive and math.hypot(p.x - sf.x, p.y - sf.y) < hr + sf.r:
                sf.alive = False
                self._apply_skin_effect(sf.skin_id)

        # Shield
        for sh in self.shields:
            if sh.alive and math.hypot(p.x - sh.x, p.y - sh.y) < hr + sh.r:
                sh.alive = False
                self.effects['shield'] = 1.0   # 1 = has shield

        # Freeze
        for fz in self.freezes:
            if fz.alive and math.hypot(p.x - fz.x, p.y - fz.y) < hr + fz.r:
                fz.alive = False
                self.ai_frozen_timer = EFFECT_FREEZE
                self.freeze_effect   = (fz.x, fz.y, 0.0)

        # Bomb — explodes into meat chunks at its location
        for b in self.bombs:
            if b.alive and math.hypot(p.x - b.x, p.y - b.y) < hr + b.r:
                b.alive = False
                for _ in range(BOMB_MEAT_COUNT):
                    self.meats.append(MeatChunk(b.x, b.y, (200, 120, 40)))
                self.score += 50 * sc

    def _apply_skin_effect(self, skin_id: str):
        data = SKIN_FRUIT_DATA[skin_id]
        self.player.grow_flat(data['seg'])
        eff = data['effect']
        if eff == 'speed':
            self.effects['speed']      = EFFECT_SPEED
        elif eff == 'invincible':
            self.effects['invincible'] = EFFECT_INVINCIBLE
        elif eff == 'rage':
            # 狂暴：速度×2，持续6s，接触即杀AI
            self.effects['rage'] = EFFECT_RAGE
        elif eff == 'score':
            self.effects['score']      = EFFECT_SCORE
        elif eff == 'pulse':
            # 雷晶：击退+重创范围内所有AI，触发扩散环动画
            px, py = self.player.x, self.player.y
            self.pulse_effect = (px, py, 0.0)   # start ring animation
            for ctrl in self.ai_controllers:
                d = ctrl.dragon
                if not d.dead and math.hypot(d.x - px, d.y - py) < EFFECT_PULSE_R:
                    if d.seg_count <= 20:
                        self._kill_ai(d)          # tiny AI → die outright
                        self.score += SCORE_KILL
                        self.kills += 1
                    else:
                        d.shrink(d.seg_count * 3 // 4)  # shrink 75 %
                        self.score += SCORE_KILL // 2

    # ══ collision ══════════════════════════════════════════════════════════════
    def _check_collisions(self):
        p = self.player

        # Player → wall
        if not (HEAD_RADIUS < p.x < WORLD_W - HEAD_RADIUS and
                HEAD_RADIUS < p.y < WORLD_H - HEAD_RADIUS):
            self._kill_player()
            return

        # Player → other dragon bodies (skip if invincible or rage)
        if self.effects['invincible'] <= 0 and self.effects['rage'] <= 0:
            if p.protect_timer <= 0:
                for d in self.dragons:
                    if d is p or d.dead:
                        continue
                    if p.head_hits_body(d):
                        self._kill_player()
                        return

        # Rage: player head kills AI on contact
        if self.effects['rage'] > 0:
            for ctrl in self.ai_controllers:
                d = ctrl.dragon
                if d.dead:
                    continue
                if math.hypot(p.x - d.x, p.y - d.y) < HEAD_RADIUS * 3.5:
                    self._kill_ai(d)
                    self.score += SCORE_KILL
                    self.kills += 1

        # AI → wall or player body
        for ctrl in self.ai_controllers:
            d = ctrl.dragon
            if d.dead:
                continue
            if not (HEAD_RADIUS < d.x < WORLD_W - HEAD_RADIUS and
                    HEAD_RADIUS < d.y < WORLD_H - HEAD_RADIUS):
                self._kill_ai(d)
                continue
            if d.protect_timer > 0:
                continue
            for other in self.dragons:
                if other is d or other.dead:
                    continue
                if d.head_hits_body(other):
                    if other is p:
                        self.score += SCORE_KILL
                        self.kills += 1
                    self._kill_ai(d)
                    break

    # ══ kill / respawn ═════════════════════════════════════════════════════════
    def _kill_player(self):
        # Shield absorbs one death
        if self.effects.get('shield', 0) > 0:
            self.effects['shield'] = 0.0
            self.player.protect_timer = 2.5   # brief invincibility
            return
        self._explode(self.player)
        self.player_dead   = True
        self.respawn_timer = RESPAWN_DELAY
        if self.revivals_left <= 0:
            self.game_over = True
        else:
            self.revivals_left -= 1

    def _respawn_player(self):
        rx, ry = self._safe_pos(300)
        p = self.player
        p.x, p.y = float(rx), float(ry)
        p.angle   = random.uniform(0, math.tau)
        p.seg_count = INIT_SEGS
        p._trail.clear()
        for i in range(INIT_SEGS + 8):
            sx = rx - math.cos(p.angle) * i * p.speed / 60
            sy = ry - math.sin(p.angle) * i * p.speed / 60
            p._trail.append((sx, sy))
        p.protect_timer = RESPAWN_PROTECT
        # Clear effects on respawn
        for k in self.effects:
            self.effects[k] = 0.0
        self.player_dead = False

    def _kill_ai(self, d: Dragon):
        self._explode(d)
        d.dead = True
        self.ai_controllers = [c for c in self.ai_controllers if c.dragon is not d]

    # ══ leaderboard data ═══════════════════════════════════════════════════════
    def leaderboard(self) -> list[tuple]:
        """Returns list of (rank_name, seg_count, is_player, glow_color)."""
        alive = [d for d in self.dragons if not d.dead]
        ranked = sorted(alive, key=lambda d: d.seg_count, reverse=True)[:6]
        result = []
        for i, d in enumerate(ranked):
            is_p = d is self.player
            name = "你" if is_p else f"AI {i+1}"
            result.append((name, d.seg_count, is_p, d.skin.get('glow', (200,200,200))))
        return result

    # ══ draw ═══════════════════════════════════════════════════════════════════
    def draw(self, surf: pygame.Surface):
        surf.fill(BG_COLOR)
        self._draw_grid(surf)

        cam_x, cam_y = self.cam_x, self.cam_y

        # items (back layer)
        for m in self.meats:
            m.draw(surf, cam_x, cam_y)
        for s in self.stars:
            s.draw(surf, cam_x, cam_y)
        for f in self.fruits:
            f.draw(surf, cam_x, cam_y)
        for sf in self.skin_fruits:
            sf.draw(surf, cam_x, cam_y)
        for gb in self.growth_boosts:
            gb.draw(surf, cam_x, cam_y)
        for mg in self.magnets:
            mg.draw(surf, cam_x, cam_y)
        for sh in self.shields:
            sh.draw(surf, cam_x, cam_y)
        for fz in self.freezes:
            fz.draw(surf, cam_x, cam_y)
        for b in self.bombs:
            b.draw(surf, cam_x, cam_y)

        # dragons (AI first, player on top)
        for d in self.dragons:
            if not d.dead:
                d.draw(surf, cam_x, cam_y)

        # speed-boost particle trail
        if self.boosting and not self.player_dead:
            self._draw_boost_trail(surf, cam_x, cam_y)

        # rage aura (red pulsing ring around player)
        if self.effects.get('rage', 0) > 0 and not self.player_dead:
            p   = self.player
            hsx = int(p.x - cam_x)
            hsy = int(p.y - cam_y)
            pulse = math.sin(pygame.time.get_ticks() / 80) * 5
            ar = int(HEAD_RADIUS * 3.2 + pulse)
            aura = pygame.Surface((ar*2+4, ar*2+4), pygame.SRCALPHA)
            pygame.draw.circle(aura, (255, 60, 20, 70),  (ar+2, ar+2), ar)
            pygame.draw.circle(aura, (255, 90, 30, 180), (ar+2, ar+2), ar, 3)
            surf.blit(aura, (hsx-ar-2, hsy-ar-2))

        # lightning pulse expanding ring (blue)
        if self.pulse_effect is not None:
            px2, py2, prog = self.pulse_effect
            sx2 = int(px2 - cam_x)
            sy2 = int(py2 - cam_y)
            r   = int(EFFECT_PULSE_R * prog)
            alpha = int(220 * (1.0 - prog))
            if r > 0:
                ring = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring, (120, 160, 255, alpha), (r+2, r+2), r, 4)
                pygame.draw.circle(ring, (200, 220, 255, alpha//2), (r+2, r+2), max(1,r-8), 2)
                surf.blit(ring, (sx2-r-2, sy2-r-2))

        # freeze expanding ring (cyan)
        if self.freeze_effect is not None:
            fx2, fy2, fprog = self.freeze_effect
            fsx = int(fx2 - cam_x)
            fsy = int(fy2 - cam_y)
            fr  = int(EFFECT_PULSE_R * fprog)
            fa  = int(200 * (1.0 - fprog))
            if fr > 0:
                fring = pygame.Surface((fr*2+4, fr*2+4), pygame.SRCALPHA)
                pygame.draw.circle(fring, (160, 230, 255, fa), (fr+2, fr+2), fr, 5)
                pygame.draw.circle(fring, (220, 245, 255, fa//2), (fr+2, fr+2), max(1,fr-10), 2)
                surf.blit(fring, (fsx-fr-2, fsy-fr-2))

        # shield aura (cyan) around player when active
        if self.effects.get('shield', 0) > 0 and not self.player_dead:
            p   = self.player
            hsx = int(p.x - cam_x)
            hsy = int(p.y - cam_y)
            sp  = math.sin(pygame.time.get_ticks() / 120) * 4
            sr  = int(HEAD_RADIUS * 2.8 + sp)
            saura = pygame.Surface((sr*2+4, sr*2+4), pygame.SRCALPHA)
            pygame.draw.circle(saura, (60, 220, 255, 55), (sr+2, sr+2), sr)
            pygame.draw.circle(saura, (120, 240, 255, 170), (sr+2, sr+2), sr, 3)
            surf.blit(saura, (hsx-sr-2, hsy-sr-2))

        self._draw_border(surf)

    def _draw_boost_trail(self, surf, cam_x, cam_y):
        p = self.player
        trail = list(p._trail)
        for i in range(min(8, len(trail))):
            tx = trail[i][0] - cam_x
            ty = trail[i][1] - cam_y
            alpha = 180 - i * 20
            r = max(2, 8 - i)
            tmp = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*p.skin['glow'], alpha), (r+1, r+1), r)
            surf.blit(tmp, (int(tx-r-1), int(ty-r-1)))

    def _draw_grid(self, surf: pygame.Surface):
        grid = 160
        ox = int(self.cam_x) % grid
        oy = int(self.cam_y) % grid
        for gx in range(-ox, SCREEN_W + grid, grid):
            pygame.draw.line(surf, GRID_COLOR, (gx, 0), (gx, SCREEN_H))
        for gy in range(-oy, SCREEN_H + grid, grid):
            pygame.draw.line(surf, GRID_COLOR, (0, gy), (SCREEN_W, gy))

    def _draw_border(self, surf: pygame.Surface):
        corners = [
            (0 - self.cam_x,        0 - self.cam_y),
            (WORLD_W - self.cam_x,  0 - self.cam_y),
            (WORLD_W - self.cam_x,  WORLD_H - self.cam_y),
            (0 - self.cam_x,        WORLD_H - self.cam_y),
        ]
        # red warning glow near border
        pygame.draw.lines(surf, (220, 50, 50), True,
                          [(int(x), int(y)) for x, y in corners], 3)
