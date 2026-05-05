"""All game screens."""
import pygame, math, sys, random, os
import config
from config import (SCREEN_W, SCREEN_H, SKINS, SKIN_ORDER, DIFFICULTIES,
                    BG_COLOR, STAR_COLOR, WORLD_W, WORLD_H, IS_ANDROID, AUTHOR)
import save_data as SD

# ── font ─────────────────────────────────────────────────────────────────────
_fcache: dict = {}

# Android system CJK font paths (common on Chinese Android devices)
_ANDROID_FONTS = [
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/system/fonts/NotoSansSC-Regular.otf',
    '/system/fonts/DroidSansFallback.ttf',
    '/system/fonts/DroidSansFallbackFull.ttf',
    '/system/fonts/SourceHanSansSC-Regular.otf',
    '/sdcard/fonts/NotoSansSC-Regular.otf',    # user-placed fallback
]

def get_font(size: int) -> pygame.font.Font:
    if size in _fcache:
        return _fcache[size]
    # Android: try system CJK font paths
    if IS_ANDROID:
        for path in _ANDROID_FONTS:
            if os.path.exists(path):
                try:
                    f = pygame.font.Font(path, size)
                    _fcache[size] = f
                    return f
                except Exception:
                    pass
        # Fallback (no CJK, shows boxes but won't crash)
        f = pygame.font.Font(None, size)
        _fcache[size] = f
        return f
    # Desktop: prefer CJK system fonts
    for name in ('Microsoft YaHei', 'SimHei', 'NSimSun', 'PingFang SC', ''):
        try:
            f = pygame.font.SysFont(name, size)
            _fcache[size] = f
            return f
        except Exception:
            pass
    f = pygame.font.Font(None, size)
    _fcache[size] = f
    return f

# ── colors ────────────────────────────────────────────────────────────────────
C_WHITE  = (240, 240, 240)
C_GRAY   = (150, 150, 150)
C_GREEN  = ( 80, 220,  80)
C_GOLD   = (255, 210,  50)
C_RED    = (220,  60,  60)
C_CYAN   = ( 80, 220, 220)
C_LOCKED = ( 70,  70,  70)

# ── helpers ───────────────────────────────────────────────────────────────────
def draw_text(surf, text, size, color, cx, cy, anchor='center'):
    img = get_font(size).render(text, True, color)
    r   = img.get_rect()
    if anchor == 'center':  r.center  = (cx, cy)
    elif anchor == 'left':  r.midleft = (cx, cy)
    elif anchor == 'right': r.midright= (cx, cy)
    surf.blit(img, r)
    return r

def draw_button(surf, text, size, rect, bg=(35,55,35), fg=C_WHITE,
                border=(70,180,70), hover=False):
    c = tuple(min(255, v+25) for v in bg) if hover else bg
    pygame.draw.rect(surf, c, rect, border_radius=8)
    pygame.draw.rect(surf, border, rect, 2, border_radius=8)
    draw_text(surf, text, size, fg, rect.centerx, rect.centery)

def is_hover(rect): return rect.collidepoint(pygame.mouse.get_pos())


# ── animated star background ──────────────────────────────────────────────────
class StarBG:
    def __init__(self, n=70):
        self.pts = [(random.uniform(0,SCREEN_W), random.uniform(0,SCREEN_H),
                     random.uniform(0.8,2.5), random.uniform(0,math.tau)) for _ in range(n)]
        self.t = 0.0
    def update(self, dt): self.t += dt
    def draw(self, surf):
        for x,y,r,ph in self.pts:
            br = max(1, r + math.sin(self.t*2+ph)*r*0.6)
            s  = pygame.Surface((int(br*4)+2, int(br*4)+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*STAR_COLOR, 110), (int(br*2)+1, int(br*2)+1), int(br))
            surf.blit(s, (int(x-br*2), int(y-br*2)))


# ══════════════════════════════════════════════════════════════════════════════
# Main Menu
# ══════════════════════════════════════════════════════════════════════════════
class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.bg     = StarBG()
        self.clock  = pygame.time.Clock()
        self.t      = 0.0

    def run(self) -> str:
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.bg.update(dt); self.t += dt
            cx = SCREEN_W // 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_start.collidepoint(event.pos): return 'skin'
                    if btn_quit.collidepoint(event.pos): pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: return 'skin'

            s = self.screen
            s.fill(BG_COLOR); self.bg.draw(s)

            # animated title
            title = "贪  吃  龙  大  作  战"
            font  = get_font(68)
            for i, ch in enumerate(title):
                off = math.sin(self.t * 2.5 + i * 0.45) * 9
                img = font.render(ch, True, C_GOLD)
                bx  = cx - len(title) * 20 + i * 40
                s.blit(img, img.get_rect(midbottom=(bx + 20, SCREEN_H//2 - 90 + off)))

            draw_text(s, "DRAGON  FEAST", 24, C_GRAY, cx, SCREEN_H//2 - 40)

            btn_start = pygame.Rect(cx-130, SCREEN_H//2+10,  260, 56)
            btn_quit  = pygame.Rect(cx-130, SCREEN_H//2+82,  260, 56)
            draw_button(s, "开 始 游 戏", 36, btn_start, hover=is_hover(btn_start))
            draw_button(s, "退      出",  36, btn_quit,
                        bg=(55,25,25), border=(200,55,55), hover=is_hover(btn_quit))

            data = SD.load()
            draw_text(s, f"最高分: {data['high_score']}   累计分: {data['total_score']}",
                      22, C_GRAY, cx, SCREEN_H - 52)
            ctrl_tip = ("触屏滑动转向 · 右侧滑动加速" if IS_ANDROID
                        else "SPACE/右键 加速  ·  方向键/WASD/鼠标 转向")
            draw_text(s, ctrl_tip, 18, (100,150,100), cx, SCREEN_H - 30)
            draw_text(s, f"© {AUTHOR}  |  贪吃龙大作战", 16, (70,100,70), cx, SCREEN_H - 10)
            pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
# Skin Select
# ══════════════════════════════════════════════════════════════════════════════
class SkinSelect:
    def __init__(self, screen):
        self.screen   = screen
        self.bg       = StarBG()
        self.clock    = pygame.time.Clock()
        self.selected = SD.load().get('last_skin', 'green')

    def run(self):
        data     = SD.load()
        unlocked = data['unlocked_skins']
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.bg.update(dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return ('menu', self.selected)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for sid, rect in skin_rects.items():
                        if rect.collidepoint(event.pos) and sid in unlocked:
                            self.selected = sid
                    if btn_ok.collidepoint(event.pos):   return ('difficulty', self.selected)
                    if btn_back.collidepoint(event.pos): return ('menu', self.selected)

            s = self.screen
            s.fill(BG_COLOR); self.bg.draw(s)
            draw_text(s, "选 择 皮 肤", 48, C_GOLD, SCREEN_W//2, 52)

            skin_rects = {}
            cw, ch = 190, 230
            total_w = len(SKIN_ORDER) * (cw+18) - 18
            sx0 = (SCREEN_W - total_w) // 2

            for i, sid in enumerate(SKIN_ORDER):
                sk     = SKINS[sid]
                locked = sid not in unlocked
                cx     = sx0 + i*(cw+18) + cw//2
                cy     = SCREEN_H//2 - 20
                rect   = pygame.Rect(cx-cw//2, cy-ch//2, cw, ch)
                skin_rects[sid] = rect

                bdr = sk['glow'] if sid == self.selected else (50,70,50)
                bw  = 3        if sid == self.selected else 1
                pygame.draw.rect(s, (22,32,22) if not locked else (20,20,20), rect, border_radius=10)
                pygame.draw.rect(s, bdr, rect, bw, border_radius=10)

                col = sk['body'] if not locked else C_LOCKED
                pygame.draw.circle(s, col,         (cx, cy-38), 36)
                pygame.draw.circle(s, sk['head'] if not locked else (45,45,45), (cx, cy-38), 36, 3)
                if not locked:
                    for side in (-1, 1):
                        pygame.draw.circle(s, sk['eye'],   (cx+side*11, cy-43), 5)
                        pygame.draw.circle(s, sk['pupil'], (cx+side*11, cy-43), 2)
                    # horns
                    for side in (-1, 1):
                        pygame.draw.line(s, sk['glow'],
                                         (cx+side*8, cy-58), (cx+side*18, cy-72), 3)

                draw_text(s, sk['name'], 26, C_WHITE if not locked else C_LOCKED, cx, cy+10)
                if locked:
                    draw_text(s, f"累计 {sk['unlock']} 分解锁", 16, C_GRAY,  cx, cy+38)
                    draw_text(s, "🔒", 24, C_LOCKED, cx, cy+62)
                else:
                    draw_text(s, "✓ 已解锁", 16, C_GREEN, cx, cy+38)
                if sid == self.selected:
                    draw_text(s, "▲ 当前选择", 16, C_GOLD, cx, cy+ch//2-14)

            btn_ok   = pygame.Rect(SCREEN_W//2-215, SCREEN_H-85, 200, 50)
            btn_back = pygame.Rect(SCREEN_W//2+15,  SCREEN_H-85, 200, 50)
            draw_button(s, "确认选择", 30, btn_ok,  hover=is_hover(btn_ok))
            draw_button(s, "← 返回",  30, btn_back,
                        bg=(40,28,28), border=(160,55,55), hover=is_hover(btn_back))
            draw_text(s, f"累计分: {data['total_score']}", 20, C_GRAY, SCREEN_W//2, SCREEN_H-16)
            pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
# Difficulty Select
# ══════════════════════════════════════════════════════════════════════════════
class DifficultySelect:
    def __init__(self, screen):
        self.screen = screen
        self.bg     = StarBG()
        self.clock  = pygame.time.Clock()

    def run(self):
        descs = {
            'easy':   ('3 条 AI · 移速 ×0.8', C_GREEN),
            'medium': ('5 条 AI · 标准移速',   C_GOLD),
            'hard':   ('8 条 AI · 移速 ×1.2',  C_RED),
        }
        keys = list(DIFFICULTIES.keys())
        btn_rects = {}
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.bg.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for k, r in btn_rects.items():
                        if r.collidepoint(event.pos): return k
                    if btn_back.collidepoint(event.pos): return None

            s = self.screen
            s.fill(BG_COLOR); self.bg.draw(s)
            draw_text(s, "选 择 难 度", 48, C_GOLD, SCREEN_W//2, 80)
            for i, key in enumerate(keys):
                diff      = DIFFICULTIES[key]
                desc, col = descs[key]
                rect = pygame.Rect(SCREEN_W//2-220, 200+i*130, 440, 100)
                btn_rects[key] = rect
                draw_button(s, diff['label'], 40, rect,
                            bg=(28,46,28), border=col, fg=col, hover=is_hover(rect))
                draw_text(s, desc, 22, C_GRAY, SCREEN_W//2, rect.bottom-28)
            btn_back = pygame.Rect(SCREEN_W//2-100, SCREEN_H-78, 200, 48)
            draw_button(s, "← 返回", 28, btn_back,
                        bg=(40,28,28), border=(160,55,55), hover=is_hover(btn_back))
            pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
# HUD
# ══════════════════════════════════════════════════════════════════════════════
EFFECT_ICONS = {
    'magnet':     ('磁铁', (80,  180, 255)),
    'speed':      ('加速', (255, 230,  50)),
    'invincible': ('无敌', (180,  80, 255)),
    'rage':       ('狂暴', (255,  80,  30)),
    'score':      ('x2分', (255, 210,  50)),
    'shield':     ('护盾', (80,  220, 255)),
    'freeze':     ('冰冻', (160, 240, 255)),
}

def draw_hud(surf: pygame.Surface, world, paused: bool):
    p = world.player

    # ── top bar ──────────────────────────────────────────────
    bar_h = 46
    bar   = pygame.Surface((SCREEN_W, bar_h), pygame.SRCALPHA)
    bar.fill((8, 15, 8, 210))
    surf.blit(bar, (0, 0))
    pygame.draw.line(surf, (40, 90, 40), (0, bar_h), (SCREEN_W, bar_h), 1)

    draw_text(surf, f"得分: {world.score}", 26, C_GOLD,   12, 23, 'left')
    draw_text(surf, f"长度: {p.seg_count}", 24, C_WHITE, 200, 23, 'left')
    draw_text(surf, f"击杀: {world.kills}", 24, C_WHITE, 360, 23, 'left')

    # revival dots
    for i in range(world.revivals_left):
        pygame.draw.circle(surf, C_GREEN, (SCREEN_W//2 - 24 + i*26, 23), 9)
        pygame.draw.circle(surf, (0,0,0), (SCREEN_W//2 - 24 + i*26, 23), 9, 2)
    draw_text(surf, "命", 18, C_GRAY, SCREEN_W//2 - 44, 23, 'left')

    # boost hint
    if IS_ANDROID:
        hint = "右侧滑动 = 加速" if not world.boosting else "⚡ 加速中"
    else:
        hint = "SPACE/右键 = 加速(消耗体长)" if not world.boosting else "⚡ 加速中"
    col  = (120, 255, 120) if world.boosting else (80, 120, 80)
    tip  = get_font(18).render(hint, True, col)
    surf.blit(tip, tip.get_rect(midright=(SCREEN_W - 8, 23)))

    # ── active effects bar ────────────────────────────────────
    ex = 8
    for eff_name, (icon, col) in EFFECT_ICONS.items():
        t = world.effects.get(eff_name, 0.0)
        if t > 0:
            label = f"{icon} ✓" if eff_name == 'shield' else f"{icon} {t:.1f}s"
            draw_text(surf, label, 20, col, ex, bar_h + 14, 'left')
            ex += 100
    # freeze AI indicator
    if world.ai_frozen_timer > 0:
        draw_text(surf, f"冰冻AI {world.ai_frozen_timer:.1f}s", 20,
                  (160, 240, 255), ex, bar_h + 14, 'left')

    # ── leaderboard (top-right) ───────────────────────────────
    lb_x, lb_y = SCREEN_W - 175, bar_h + 4
    draw_text(surf, "排行榜", 20, C_GOLD, lb_x + 80, lb_y + 10)
    for i, (name, segs, is_p, glow) in enumerate(world.leaderboard()):
        y  = lb_y + 30 + i * 22
        col = C_GOLD if is_p else glow
        pygame.draw.circle(surf, col, (lb_x + 12, y), 5)
        draw_text(surf, f"{i+1}. {name}  {segs}", 18, col, lb_x + 22, y, 'left')

    # ── minimap (bottom-right) ────────────────────────────────
    _draw_minimap(surf, world)

    # ── pause overlay ─────────────────────────────────────────
    if paused:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 145))
        surf.blit(ov, (0, 0))
        draw_text(surf, "游  戏  暂  停", 60, C_GOLD, SCREEN_W//2, SCREEN_H//2 - 40)
        resume_hint = "点击屏幕继续" if IS_ANDROID else "按 ESC 继续"
        draw_text(surf, resume_hint, 30, C_WHITE, SCREEN_W//2, SCREEN_H//2 + 35)

    # ── death overlay ─────────────────────────────────────────
    if world.player_dead and not world.game_over:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((80, 0, 0, 100))
        surf.blit(ov, (0, 0))
        draw_text(surf, "阵亡中...", 54, C_RED,   SCREEN_W//2, SCREEN_H//2)
        draw_text(surf, f"剩余复活: {world.revivals_left}", 30, C_WHITE,
                  SCREEN_W//2, SCREEN_H//2 + 60)


def _draw_minimap(surf: pygame.Surface, world):
    MW, MH = 160, 110
    MX, MY = SCREEN_W - MW - 6, SCREEN_H - MH - 6
    # background
    bg = pygame.Surface((MW, MH), pygame.SRCALPHA)
    bg.fill((8, 16, 8, 185))
    surf.blit(bg, (MX, MY))
    pygame.draw.rect(surf, (40, 90, 40), (MX, MY, MW, MH), 1)

    sx = MW / WORLD_W
    sy = MH / WORLD_H

    # items dots
    for star in world.stars:
        x = int(MX + star.x * sx)
        y = int(MY + star.y * sy)
        pygame.draw.circle(surf, (200, 180, 40), (x, y), 1)

    for fruit in world.fruits:
        x = int(MX + fruit.x * sx)
        y = int(MY + fruit.y * sy)
        pygame.draw.circle(surf, fruit.color, (x, y), 2)

    # dragons
    for d in world.dragons:
        if d.dead:
            continue
        dmx = int(MX + d.x * sx)
        dmy = int(MY + d.y * sy)
        is_p = d is world.player
        r    = 4 if is_p else 2
        col  = d.skin.get('glow', (200, 200, 200))
        pygame.draw.circle(surf, col, (dmx, dmy), r)

    # viewport rect
    vx = int(MX + world.cam_x * sx)
    vy = int(MY + world.cam_y * sy)
    vw = max(4, int(SCREEN_W * sx))
    vh = max(4, int(SCREEN_H * sy))
    pygame.draw.rect(surf, (80, 200, 80), (vx, vy, vw, vh), 1)


# ══════════════════════════════════════════════════════════════════════════════
# Game Screen
# ══════════════════════════════════════════════════════════════════════════════
class GameScreen:
    def __init__(self, screen, skin_id: str, diff_key: str):
        from world import World
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        self.world   = World(skin_id, DIFFICULTIES[diff_key])
        self.paused  = False
        self.skin_id = skin_id
        # Multi-touch state: {finger_id: {'start': (x,y), 'cur': (x,y)}}
        self._touches: dict = {}
        self._boost_zone_x = int(SCREEN_W * 0.78)
        self._pause_btn    = pygame.Rect(SCREEN_W - 52, 5, 42, 36)

    def _handle_touch_events(self, events):
        """Joystick-style swipe steering + right-zone boost."""
        DEAD_ZONE = 30
        for event in events:
            if event.type == pygame.FINGERDOWN:
                fx = int(event.x * SCREEN_W)
                fy = int(event.y * SCREEN_H)
                if not self._pause_btn.collidepoint(fx, fy):
                    self._touches[event.finger_id] = {'start': (fx, fy), 'cur': (fx, fy)}
            elif event.type == pygame.FINGERMOTION:
                if event.finger_id in self._touches:
                    fx = int(event.x * SCREEN_W)
                    fy = int(event.y * SCREEN_H)
                    self._touches[event.finger_id]['cur'] = (fx, fy)
            elif event.type == pygame.FINGERUP:
                self._touches.pop(event.finger_id, None)

        mouse_angle = None
        boost = False
        for touch in self._touches.values():
            sx, sy = touch['start']
            cx, cy = touch['cur']
            if sx >= self._boost_zone_x:
                boost = True
            else:
                dx, dy = cx - sx, cy - sy
                if math.hypot(dx, dy) > DEAD_ZONE:
                    mouse_angle = math.atan2(dy, dx)
        return mouse_angle, boost

    def _draw_touch_joystick(self, surf: pygame.Surface):
        """Draw virtual joystick ring + knob while finger is dragging."""
        DEAD_ZONE = 30
        MAX_RADIUS = 55
        for touch in self._touches.values():
            sx, sy = touch['start']
            cx, cy = touch['cur']
            if sx >= self._boost_zone_x:
                continue
            ring = pygame.Surface((MAX_RADIUS * 2 + 4, MAX_RADIUS * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (80, 200, 80, 40),  (MAX_RADIUS + 2, MAX_RADIUS + 2), MAX_RADIUS)
            pygame.draw.circle(ring, (120, 240, 120, 130), (MAX_RADIUS + 2, MAX_RADIUS + 2), MAX_RADIUS, 2)
            surf.blit(ring, (sx - MAX_RADIUS - 2, sy - MAX_RADIUS - 2))
            dx, dy = cx - sx, cy - sy
            dist = math.hypot(dx, dy)
            if dist > DEAD_ZONE:
                clamp = min(dist, MAX_RADIUS)
                kx = int(sx + dx / dist * clamp)
                ky = int(sy + dy / dist * clamp)
                knob = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(knob, (160, 255, 160, 200), (16, 16), 14)
                surf.blit(knob, (kx - 16, ky - 16))

    def run(self) -> dict:
        while True:
            dt = self.clock.tick(60) / 1000.0

            all_events = pygame.event.get()
            touch_angle, touch_boost = None, False

            for event in all_events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                if event.type == pygame.KEYDOWN and event.key == pygame.K_AC_BACK:
                    self.paused = not self.paused
                if IS_ANDROID and event.type == pygame.FINGERDOWN:
                    fx = int(event.x * SCREEN_W)
                    fy = int(event.y * SCREEN_H)
                    if self._pause_btn.collidepoint(fx, fy):
                        self.paused = not self.paused
                        self._touches.clear()
                elif IS_ANDROID and self.paused and event.type == pygame.FINGERUP:
                    self.paused = False
                    self._touches.clear()

            if IS_ANDROID:
                touch_angle, touch_boost = self._handle_touch_events(all_events)

            if not self.paused and not self.world.game_over:
                keys = pygame.key.get_pressed()
                turn_left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
                turn_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

                # Mouse / touch steering
                mx, my = pygame.mouse.get_pos()
                spx = self.world.player.x - self.world.cam_x
                spy = self.world.player.y - self.world.cam_y
                mdx, mdy = mx - spx, my - spy
                mouse_angle = math.atan2(mdy, mdx) if mdx*mdx+mdy*mdy > 20*20 else None

                # UP/DOWN keys override
                if keys[pygame.K_UP]   or keys[pygame.K_w]: mouse_angle = -math.pi/2
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]: mouse_angle =  math.pi/2

                # Prefer FINGER-based angle on Android
                if IS_ANDROID and touch_angle is not None:
                    mouse_angle = touch_angle

                # Boost: keyboard/mouse on desktop, touch zone on Android
                mb    = pygame.mouse.get_pressed()
                boost = (touch_boost if IS_ANDROID else
                         (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT] or mb[2]))

                self.world.update(dt, turn_left, turn_right, mouse_angle, boost)

            self.world.draw(self.screen)
            draw_hud(self.screen, self.world, self.paused)

            if IS_ANDROID:
                _draw_boost_zone(self.screen, self.world.boosting, self._boost_zone_x)
                self._draw_touch_joystick(self.screen)
                # pause button
                pb = self._pause_btn
                pygame.draw.rect(self.screen, (30, 55, 30), pb, border_radius=6)
                pygame.draw.rect(self.screen, (80, 160, 80), pb, 1, border_radius=6)
                draw_text(self.screen, "II", 20, C_WHITE, pb.centerx, pb.centery)

            pygame.display.flip()

            if self.world.game_over:
                pygame.time.wait(700)
                return {'score': self.world.score, 'kills': self.world.kills,
                        'skin_id': self.skin_id}


def _draw_boost_zone(surf: pygame.Surface, active: bool, zone_x: int):
    """Semi-transparent boost button area on the right side for Android."""
    w = SCREEN_W - zone_x
    zone = pygame.Surface((w, SCREEN_H), pygame.SRCALPHA)
    col  = (255, 140, 30, 55) if active else (80, 120, 80, 30)
    zone.fill(col)
    surf.blit(zone, (zone_x, 0))
    # divider line
    pygame.draw.line(surf, (80, 160, 80, 120) if not active else (255, 180, 60),
                     (zone_x, 0), (zone_x, SCREEN_H), 1)
    # label
    label = get_font(22).render("加速", True,
                                (255, 200, 80) if active else (100, 160, 100))
    surf.blit(label, label.get_rect(center=(zone_x + w//2, SCREEN_H//2)))


# ══════════════════════════════════════════════════════════════════════════════
# Game Over
# ══════════════════════════════════════════════════════════════════════════════
class GameOver:
    def __init__(self, screen, result: dict, save: dict):
        self.screen = screen
        self.result = result
        self.save   = save
        self.bg     = StarBG()
        self.clock  = pygame.time.Clock()

    def run(self) -> str:
        score    = self.result['score']
        kills    = self.result['kills']
        new_best = score >= self.save.get('high_score', 0)

        while True:
            dt = self.clock.tick(60) / 1000.0
            self.bg.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_retry.collidepoint(event.pos): return 'retry'
                    if btn_menu.collidepoint(event.pos):  return 'menu'
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_r): return 'retry'
                    if event.key == pygame.K_ESCAPE: return 'menu'

            s  = self.screen
            cx = SCREEN_W // 2
            s.fill(BG_COLOR); self.bg.draw(s)
            draw_text(s, "游  戏  结  束", 64, C_RED, cx, 100)
            draw_text(s, f"本局得分: {score}", 38, C_GOLD, cx, 200)
            if new_best:
                draw_text(s, "★ 新 纪 录 ★", 30, C_GOLD, cx, 246)
            draw_text(s, f"击杀: {kills}", 28, C_WHITE, cx, 290)
            draw_text(s, f"历史最高: {self.save['high_score']}", 26, C_GRAY, cx, 330)
            draw_text(s, f"累计总分: {self.save['total_score']}", 26, C_GRAY, cx, 364)

            # newly unlocked skins
            py = 400
            for sid in SKIN_ORDER:
                sk = SKINS[sid]
                if (sk['unlock'] > 0 and sid in self.save['unlocked_skins']):
                    draw_text(s, f"✦ 解锁: {sk['name']} ✦", 26, sk['glow'], cx, py)
                    py += 34

            btn_retry = pygame.Rect(cx-215, SCREEN_H-105, 200, 54)
            btn_menu  = pygame.Rect(cx+15,  SCREEN_H-105, 200, 54)
            draw_button(s, "再来一局", 32, btn_retry, hover=is_hover(btn_retry))
            draw_button(s, "主 菜 单", 32, btn_menu,
                        bg=(42,28,28), border=(185,55,55), hover=is_hover(btn_menu))
            tip = ("点击按钮继续" if IS_ANDROID else "R / Enter = 再来  ·  ESC = 主菜单")
            draw_text(s, tip, 18, C_GRAY, cx, SCREEN_H - 38)
            draw_text(s, f"© {AUTHOR}  |  贪吃龙大作战", 15, (60,90,60), cx, SCREEN_H - 18)
            pygame.display.flip()
