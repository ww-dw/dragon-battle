import json, os
from config import SKIN_ORDER, SKINS

SAVE_PATH = os.path.join(os.path.expanduser("~"), ".dragon_game.json")

_DEFAULT = {
    'high_score':      0,
    'total_score':     0,
    'unlocked_skins':  ['green'],
    'last_skin':       'green',
}


def load() -> dict:
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k, v in _DEFAULT.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(_DEFAULT)


def save(data: dict):
    try:
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def record_game(score: int, skin_id: str) -> dict:
    data = load()
    data['total_score'] += score
    if score > data['high_score']:
        data['high_score'] = score
    data['last_skin'] = skin_id
    # Unlock skins based on cumulative total
    for sid in SKIN_ORDER:
        if (SKINS[sid]['unlock'] <= data['total_score']
                and sid not in data['unlocked_skins']):
            data['unlocked_skins'].append(sid)
    save(data)
    return data
