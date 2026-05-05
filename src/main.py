"""
贪吃龙大作战  –  main entry point
作者：吴恙

Desktop : python main.py
Android : buildozer android debug
Package : pyinstaller --onefile --windowed main.py
"""
import sys, os

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
import config
from screens import MainMenu, SkinSelect, DifficultySelect, GameScreen, GameOver
import save_data as SD


def main():
    pygame.init()
    pygame.display.set_caption(config.TITLE)

    if config.IS_ANDROID:
        # Android: create a fixed-size logical surface that scales to fit screen
        # pygame.SCALED maps touch coordinates automatically to logical coords
        screen = pygame.display.set_mode(
            (config.SCREEN_W, config.SCREEN_H),
            pygame.FULLSCREEN | pygame.SCALED
        )
        pygame.mouse.set_visible(False)
        # Enable multi-touch events
        try:
            pygame.event.set_allowed([
                pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION,
                pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION,
                pygame.KEYDOWN, pygame.QUIT,
            ])
        except Exception:
            pass
    else:
        screen = pygame.display.set_mode(
            (config.SCREEN_W, config.SCREEN_H),
            pygame.FULLSCREEN | pygame.SCALED
        )
        pygame.mouse.set_visible(True)

    state    = 'menu'
    skin_id  = SD.load().get('last_skin', 'green')
    diff_key = 'medium'

    while True:
        if state == 'menu':
            state = MainMenu(screen).run()

        elif state == 'skin':
            next_state, skin_id = SkinSelect(screen).run()
            state = next_state

        elif state == 'difficulty':
            result = DifficultySelect(screen).run()
            if result is None:
                state = 'skin'
            else:
                diff_key = result
                state    = 'play'

        elif state == 'play':
            result   = GameScreen(screen, skin_id, diff_key).run()
            save     = SD.record_game(result['score'], result['skin_id'])
            state    = GameOver(screen, result, save).run()
            if state == 'retry':
                state = 'play'

        else:
            state = 'menu'


if __name__ == '__main__':
    main()
