import math, os, sys

# ── Platform ─────────────────────────────────────────────
IS_ANDROID = (hasattr(sys, 'getandroidapilevel') or
              'ANDROID_ARGUMENT' in os.environ)

# ── Screen ──────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
TITLE  = "贪吃龙大作战"
AUTHOR = "吴恙"

# ── World ────────────────────────────────────────────────
WORLD_W, WORLD_H = 5600, 4200

# ── Dragon ───────────────────────────────────────────────
SEG_RADIUS     = 10       # px, half-width of each segment circle
SEG_SPACING    = 6        # px between segment centers in trail (smaller = smoother curves)
HEAD_RADIUS    = 14       # px
INIT_SEGS      = 22       # initial segment count
PLAYER_SPEED   = 260      # px / s
TURN_SPEED_DEG = 245      # degrees / s  (keyboard)
TURN_SPEED_RAD = TURN_SPEED_DEG * math.pi / 180
MAX_REVIVALS   = 2
RESPAWN_PROTECT = 3.0     # s of invincibility after respawn

# ── Speed Boost (hold SPACE / right-click) ───────────────
BOOST_SPEED_MULT      = 1.6    # multiplier while boosting
BOOST_DRAIN_INTERVAL  = 0.35   # s per segment drained
BOOST_MIN_SEGS        = 14     # can't boost below this length

# ── Growth ───────────────────────────────────────────────
MEAT_GROWTH        = 1    # segments per meat chunk
STAR_DOUBLE_AT     = 20   # every N stars → grow bonus
FRUIT_DOUBLE_AT    = 8    # every N fruits → grow bonus
FRUIT_FROM_STARS   = 5    # eat this many stars → spawn 1 fruit

# ── Items ────────────────────────────────────────────────
STAR_SPAWN_INTERVAL = 5.0   # s
MAX_STARS  = 40
MAX_FRUITS = 8
MEAT_LIFETIME = 18.0  # s before meat disappears

# ── Difficulty ───────────────────────────────────────────
DIFFICULTIES = {
    'easy':   {'label': '简单', 'ai_count': 3,  'speed_mult': 0.80, 'react': 0.35},
    'medium': {'label': '普通', 'ai_count': 5,  'speed_mult': 1.00, 'react': 0.60},
    'hard':   {'label': '困难', 'ai_count': 8,  'speed_mult': 1.20, 'react': 0.85},
}

# ── Skins ────────────────────────────────────────────────
SKIN_ORDER = ['green', 'black', 'lightning', 'red', 'yellow']
SKINS = {
    'green': {
        'name': '绿龙',
        'unlock': 0,
        'body':    (55,  200,  60),
        'body2':   (35,  160,  40),
        'head':    (30,  170,  35),
        'eye':     (240, 240, 240),
        'pupil':   (20,  20,   20),
        'glow':    (80,  255, 100),
        'pattern': 'solid',
    },
    'black': {
        'name': '黑龙',
        'unlock': 500,
        'body':    (35,   35,  35),
        'body2':   (20,   20,  20),
        'head':    (15,   15,  15),
        'eye':     (255,  50,  50),
        'pupil':   (200,   0,   0),
        'glow':    (180,   0,   0),
        'pattern': 'scale',
    },
    'lightning': {
        'name': '霹雳龙',
        'unlock': 1000,
        'body':    (60,   80, 230),
        'body2':   (30,   50, 180),
        'head':    (20,   35, 160),
        'eye':     (255, 240,  50),
        'pupil':   (200, 190,   0),
        'glow':    (120, 150, 255),
        'pattern': 'lightning',
    },
    'red': {
        'name': '辣条红龙',
        'unlock': 2000,
        'body':    (220,  50,  50),
        'body2':   (160,  25,  25),
        'head':    (180,  20,  20),
        'eye':     (255, 200,  50),
        'pupil':   (200, 140,   0),
        'glow':    (255,  80,  30),
        'pattern': 'stripe',
    },
    'yellow': {
        'name': '加农炮黄龙',
        'unlock': 3000,
        'body':    (220, 180,  10),
        'body2':   (180, 140,   0),
        'head':    (200, 160,   0),
        'eye':     (50,   80, 255),
        'pupil':   (0,    30, 200),
        'glow':    (255, 230,  80),
        'pattern': 'cannon',
    },
}

# ── AI skin pool (distinct from player) ─────────────────
AI_SKINS = [
    {'body': (180, 70,  200), 'body2': (130, 40, 150), 'head': (100, 30, 120),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (220,100,240), 'pattern': 'solid'},
    {'body': (30,  180, 180), 'body2': (20, 130, 130), 'head': (15,  110, 110),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (60, 220, 220), 'pattern': 'solid'},
    {'body': (200, 120,  40), 'body2': (150,  80, 20), 'head': (130,  60, 10),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (240, 160, 60), 'pattern': 'solid'},
    {'body': (80,  200, 100), 'body2': (50,  150, 70), 'head': (30,  130, 50),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (100, 240, 120), 'pattern': 'solid'},
    {'body': (200,  80,  80), 'body2': (150,  50, 50), 'head': (130,  30, 30),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (240,  80,  80), 'pattern': 'solid'},
    {'body': (80,   80, 200), 'body2': (50,   50,150), 'head': (30,   30,130),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': ( 80,  80, 240), 'pattern': 'solid'},
    {'body': (200, 160,  80), 'body2': (160, 120, 50), 'head': (140, 100, 30),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (240, 200, 80), 'pattern': 'solid'},
    {'body': (100, 180,  50), 'body2': ( 70, 130, 30), 'head': (50,  110, 20),
     'eye': (255,255,255), 'pupil': (0,0,0), 'glow': (130, 220, 80), 'pattern': 'solid'},
]

# ── Colors ───────────────────────────────────────────────
BG_COLOR     = (12,  22,  12)
GRID_COLOR   = (18,  32,  18)
STAR_COLOR   = (255, 230,  50)
STAR_GLOW    = (255, 200,   0)
FRUIT_COLORS = [
    (255, 100, 100),
    (100, 220, 100),
    (100, 150, 255),
    (255, 165,  50),
    (220,  80, 220),
]
MEAT_COLOR   = (190,  90,  90)

# ── Score ────────────────────────────────────────────────
SCORE_STAR   = 10
SCORE_FRUIT  = 50
SCORE_MEAT   =  5
SCORE_KILL   = 100

# ── Special items ─────────────────────────────────────────
MAGNET_SPAWN_INTERVAL  = 45.0   # s between magnet spawns
MAGNET_DURATION        = 10.0   # s magnet effect lasts
MAGNET_RANGE           = 380    # px pull radius
MAGNET_PULL_SPEED      = 240    # px/s

GROWTH_SPAWN_INTERVAL  = 55.0   # s between growth boost spawns
GROWTH_BOOST_SEGS      = 50     # segments granted

SKIN_FRUIT_SPAWN_INTERVAL = 22.0  # s between skin-fruit spawns (any player can collect)

# Effect durations (s)
EFFECT_SPEED      = 8.0
EFFECT_INVINCIBLE = 8.0
EFFECT_RAGE       = 6.0
EFFECT_SCORE      = 10.0
EFFECT_FREEZE     = 4.0   # freeze all AI
EFFECT_PULSE_R    = 320   # px radius of lightning pulse

# New items
SHIELD_SPAWN_INTERVAL = 55.0   # s
FREEZE_SPAWN_INTERVAL = 48.0   # s
BOMB_SPAWN_INTERVAL   = 32.0   # s
BOMB_MEAT_COUNT       = 32     # meat chunks per bomb

# Skin-fruit per skin
SKIN_FRUIT_DATA = {
    'green':     {'seg': 25, 'effect': 'speed',     'label': '森林精华', 'glow': (80,255,80)},
    'black':     {'seg': 25, 'effect': 'invincible', 'label': '暗夜精魂', 'glow': (180,0,180)},
    'lightning': {'seg': 25, 'effect': 'pulse',     'label': '雷晶果',   'glow': (100,160,255)},
    'red':       {'seg': 25, 'effect': 'rage',      'label': '火辣精华', 'glow': (255,80,30)},
    'yellow':    {'seg': 25, 'effect': 'score',     'label': '黄金果',   'glow': (255,220,50)},
}

# Speed scaling: speed = base * (INIT_SEGS / seg_count) ^ SPEED_SCALE_EXP
SPEED_SCALE_EXP   = 0.35
SPEED_SCALE_MIN   = 0.52   # floor multiplier
SPEED_SCALE_MAX   = 1.70   # ceiling multiplier (small dragon bonus)
