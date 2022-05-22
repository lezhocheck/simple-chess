import pygame as pg
from sortedcontainers import SortedSet
import utility
from game_objects import Board, Text, Clickable


class GameSession:
    def __init__(self) -> None:
        pg.init()
        pg.font.init()
        self.__colliders = SortedSet(key=lambda x: x.layer)
        self.__window_size = (1200, 800)
        self.__surface = pg.display.set_mode(self.__window_size)
        pg.display.set_caption('Simple chess')
        icon = 'resources/pawn.png'
        icon = pg.image.load(icon).convert_alpha()
        icon.fill(utility.BLACK, None, pg.BLEND_RGB_MULT)
        pg.display.set_icon(icon)

        self.quit_event = utility.GameEvent(event_type='quit')
        self.quit_event += lambda: (pg.quit(), exit())
        self.update_event = utility.GameEvent(event_type='update')
        self.mouse_on_event = utility.GameEvent(event_type='mouse_collision')
        self.mouse_down_event = utility.GameEvent(event_type='mouse_collision_click')

        self.moves_count = 0
        diff = max(self.__window_size) - min(self.__window_size)
        self.__player_b = Player(self, 'black')
        self.__player_w = Player(self, 'white')
        self.__board = Board(self, (diff / 2, 0), min(self.__window_size))
        self.update_event += self.__player_w.update
        self.update_event += self.__player_b.update

    def add_collider(self, collider: Clickable) -> None:
        self.__colliders.add(collider)

    @property
    def board(self) -> Board:
        return self.__board

    @property
    def player_black(self) -> 'Player':
        return self.__player_b

    @property
    def player_white(self) -> 'Player':
        return self.__player_w

    @property
    def next_player(self) -> 'Player':
        return self.__player_w if self.moves_count % 2 == 0 else self.__player_b

    @property
    def window_size(self) -> tuple:
        return self.__window_size

    @property
    def canvas(self) -> pg.Surface:
        return self.__surface

    @property
    def colliders(self) -> SortedSet:
        return self._colliders

    def start(self) -> None:
        while True:
            self.__surface.fill(utility.BG)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit_event()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    r_colliders = reversed(self.__colliders)
                    for collider in r_colliders:
                        if collider.rect.collidepoint(pg.mouse.get_pos()):
                            self.mouse_down_event(collider)
                            break

            self.update_event()

            r_colliders = reversed(self.__colliders)
            for collider in r_colliders:
                if collider.rect.collidepoint(pg.mouse.get_pos()):
                    self.mouse_on_event(collider)
                    break
            pg.display.flip()


class Player:
    def __init__(self, gs: GameSession, player_type: str) -> None:
        if player_type not in ['white', 'black']:
            raise RuntimeError()

        self.__player_type = player_type
        self.__defeated_figures = {}
        self.__gs = gs

    @property
    def player_type(self) -> str:
        return self.__player_type

    def update(self) -> None:
        w_size = self.__gs.window_size
        if w_size[0] - 150 <= w_size[1]:
            return

        if self == self.__gs.next_player:
            t_size = 20
            pos = (10, 10)
            turn_text = Text(f"{self.player_type.capitalize()}'s turn", t_size, pos, self.color)
            self.__gs.canvas.blit(turn_text.surface, turn_text.rect)

        if self.__gs.board.get_king(self).is_mated:
            t_size = 48
            pos = (self.__gs.window_size[0] / 2, self.__gs.window_size[1] / 2)
            player = self.__gs.player_black if self == self.__gs.player_white else self.__gs.player_white
            turn_text = Text(f'Player {player.player_type.capitalize()} wins!', t_size, pos, player.color)
            rect = turn_text.rect.move(-turn_text.rect.size[0] / 2, -turn_text.rect.size[1] / 2)
            self.__gs.canvas.blit(turn_text.surface, rect)

        elif self.__gs.board.get_king(self).is_checked:
            t_size = 48
            pos = (self.__gs.window_size[0] / 2, self.__gs.window_size[1] / 2)
            turn_text = Text(f'King was attacked!', t_size, pos, self.color)
            rect = turn_text.rect.move(-turn_text.rect.size[0] / 2, -turn_text.rect.size[1] / 2)
            self.__gs.canvas.blit(turn_text.surface, rect)

        size_y = 200
        position = (10, 100)

        if self.player_type == 'black':
            position = (position[0], self.__gs.window_size[1] - size_y - position[1])

        figures = ['Pawn', 'Bishop', 'Knight', 'Rook', 'Queen']
        im_bias = size_y / len(figures) * 0.1
        size_x = (size_y - (im_bias * (len(figures) - 1) + im_bias / len(figures))) / len(figures)
        im_size = (size_x, size_x)

        x, y = position
        for i in range(0, len(figures)):
            image = 'resources/' + figures[i].lower() + '.png'
            image = pg.image.load(image).convert_alpha()
            image = pg.transform.scale(image, im_size)
            image.fill(self.color, None, pg.BLEND_RGB_MULT)
            rect = image.get_rect().move(x, y)
            text_size = 18
            text_pos = rect.midright
            text_pos = (text_pos[0], text_pos[1] - text_size / 2)
            text = Text(f': {self.get_defeated(figures[i])}', text_size, text_pos, self.color)

            self.__gs.canvas.blit(image, rect)
            self.__gs.canvas.blit(text.surface, text.rect)
            y += im_size[1] + im_bias

    @property
    def color(self) -> tuple:
        return utility.WHITE if self.__player_type == 'white' else utility.BLACK

    def add_defeated(self, figure: str) -> None:
        allowed = ['Pawn', 'Bishop', 'Knight', 'Rook', 'Queen', 'King']
        if figure not in allowed:
            raise RuntimeError()
        if figure not in self.__defeated_figures:
            self.__defeated_figures[figure] = 1
        else:
            self.__defeated_figures[figure] += 1

    def get_defeated(self, figure: str):
        if figure not in self.__defeated_figures:
            return 0

        return self.__defeated_figures[figure]
