from pygame import Surface, Rect
import utility
from figures import *
from abc import abstractmethod, ABC
from typing import NoReturn, Any, Type, Union

_Figure = Type[Union[None, Pawn, Rook, Bishop, Knight, Queen, King]]


class Clickable(ABC):
    def __init__(self, gs: 'GameSession', rect: Rect, color: tuple, layer: int) -> None:
        self.__rect = rect
        self.__color = color
        self.__layer = layer
        self.__gs = gs
        gs.add_collider(self)

    @property
    def rect(self) -> Rect:
        return self.__rect

    @property
    def color(self) -> tuple:
        return self.__color

    @property
    def canvas(self) -> Surface:
        return self.__gs.canvas

    @property
    def layer(self) -> int:
        return self.__layer


class Text:
    def __init__(self, text: str, size: int, pos: tuple = (0, 0), color: tuple = utility.WHITE) -> None:
        font = pg.font.SysFont('Arial', size, True)
        self.__ts = font.render(text, True, color)
        self.__rect = self.__ts.get_rect().move(pos[0], pos[1])

    @property
    def rect(self) -> Rect:
        return self.__rect

    @property
    def surface(self) -> pg.Surface:
        return self.__ts


class Cell(Clickable):
    def __init__(self, gs: 'GameSession', size: int, board: 'Board',
                 board_pos: tuple, figure: _Figure) -> None:
        rect = Rect((board_pos[0] * size + board.start_pos[0],
                     board_pos[1] * size + board.start_pos[1]), (size,) * 2)
        self.__board = board
        super().__init__(gs, rect, self.__board.colors[(board_pos[0] + board_pos[1]) % 2], 0)
        self.__size = size
        self.__gs = gs
        self.__figure = None
        self.__board_pos = board_pos
        self.__labels = []
        player = gs.player_white if board_pos[1] >= self.__board.size / 2 else gs.player_black
        if figure is not None:
            self.__figure = figure(self, player)
        image = pg.image.load('resources/empty.png')
        self.__image = pg.transform.scale(image, self.rect.size)
        self.__image.fill(self.color, None, pg.BLEND_RGB_MULT)

    def add_label(self, label: str, position: str = 'top_left',
                  size: int = 15, bias: int = 5, color: tuple = utility.WHITE) -> None:
        allowed_pos = {'top_left': self.rect.move((bias * 2, bias)).topleft,
                       'top_right': self.rect.move((-size - bias, bias)).topright}
        if position not in allowed_pos:
            raise RuntimeError()

        self.__labels.append(Text(label, size, allowed_pos[position], color))

    @property
    def board(self) -> 'Board':
        return self.__board

    @property
    def board_pos(self) -> tuple:
        return self.__board_pos

    @property
    def size(self) -> int:
        return self.__size

    @property
    def figure(self) -> _Figure:
        return self.__figure

    @figure.setter
    def figure(self, value) -> None:
        self.__figure = value

    def draw(self) -> None:
        self.canvas.blit(self.__image, self.rect)
        for label in self.__labels:
            self.canvas.blit(label.surface, label.rect)
        if self.__figure:
            self.canvas.blit(self.__figure.image, self.__figure.rect)


class Board:
    __field: list[list[Cell]]

    def __init__(self, gs: 'GameSession', start_pos: tuple, size: int) -> None:
        self.__cell_labels_text = list(map(lambda x: (x[0], x[1]), 'A1 B2 C3 D4 E5 F6 G7 H8'.split(' ')))
        self.__gs = gs
        self.__start_pos = start_pos
        self.__start_set = [
            [Rook,    Pawn, None, None, None, None, Pawn,    Rook],
            [Knight,  Pawn, None, None, None, None, Pawn,  Knight],
            [Bishop,  Pawn, None, None, None, None, Pawn,  Bishop],
            [Queen,   Pawn, None, None, None, None, Pawn,   Queen],
            [King,    Pawn, None, None, None, None, Pawn,    King],
            [Bishop,  Pawn, None, None, None, None, Pawn,  Bishop],
            [Knight,  Pawn, None, None, None, None, Pawn,  Knight],
            [Rook,    Pawn, None, None, None, None, Pawn,    Rook]
        ]

        self.__cells_count = len(self.__start_set)
        self.__cell_size = round(size / self.__cells_count)
        self.__field = [[] for _ in range(self.__cells_count)]

        for i in range(self.__cells_count):
            for j in range(self.__cells_count):
                cell = Cell(gs, self.__cell_size, self, (i, j), self.__start_set[i][j])
                if i == 0:
                    cell.add_label(self.__cell_labels_text[j][0])
                if j == 0:
                    cell.add_label(self.__cell_labels_text[i][1], position='top_right')
                self.__field[i].append(cell)

        gs.update_event += self._update
        gs.mouse_on_event += self._mouse_on
        gs.mouse_down_event += self._mouse_down
        self.__selected_cell = None
        self.__markers = set()

    @property
    def colors(self) -> tuple:
        return utility.PALE, utility.BROWN, utility.WHITE

    @property
    def start_pos(self) -> tuple:
        return self.__start_pos

    @property
    def size(self) -> int:
        return self.__cells_count

    @property
    def game_session(self) -> 'GameSession':
        return self.__gs

    def get_king(self, player: 'Player') -> King:
        for row in self.__field:
            for cell in row:
                fig = cell.figure
                if fig and fig.__class__ == King and fig.player == player:
                    return cell.figure
        raise RuntimeError()

    def get(self, pos: tuple) -> Union[Cell, None]:
        if 0 <= pos[0] < self.__cells_count and 0 <= pos[1] < self.__cells_count:
            return self.__field[pos[0]][pos[1]]
        return None

    def get_from_start_set(self, pos: tuple) -> _Figure:
        if 0 <= pos[0] < self.__cells_count and 0 <= pos[1] < self.__cells_count:
            return self.__start_set[pos[0]][pos[1]]
        return None

    @staticmethod
    def _mouse_on(collider: Clickable) -> None:
        if collider.__class__ != Cell:
            return
        surf = pg.Surface(collider.rect.size)
        surf.set_alpha(50)
        surf.fill(utility.YELLOW)
        collider.canvas.blit(surf, collider.rect.topleft)

    def _mouse_down(self, collider: Clickable) -> None:
        if collider.__class__ != Cell or collider == self.__selected_cell:
            return

        if collider and collider.figure and collider.figure.player == self.__gs.next_player:
            self.__selected_cell = collider
            self.__markers = collider.figure.allowed_positions

        if self.__selected_cell and collider.board_pos in self.__markers:
            if self.__selected_cell.figure.__class__ is Pawn and (collider.board_pos[1] == 0
                                                                  or collider.board_pos[1] == self.size - 1):
                self.move_figure(self.__selected_cell, collider, Queen)
            elif self.__selected_cell.figure.__class__ is King:
                def move_rook(rook_type: str) -> None:
                    rook_types = ['left', 'right']
                    if rook_type not in rook_types:
                        raise RuntimeError()
                    move = (-4, -1) if rook_type == 'left' else (3, 1)
                    rook_cell = self.get((self.__selected_cell.board_pos[0] + move[0],
                                          self.__selected_cell.board_pos[1]))
                    new_rook_cell = self.get((self.__selected_cell.board_pos[0] + move[1],
                                              self.__selected_cell.board_pos[1]))
                    self.move_figure(rook_cell, new_rook_cell)
                    self.__selected_cell.figure.moves_count += 1

                if collider.board_pos[0] - self.__selected_cell.board_pos[0] > 1:
                    move_rook('right')
                elif collider.board_pos[0] - self.__selected_cell.board_pos[0] < -1:
                    move_rook('left')
            self.__markers.clear()

            self.move_figure(self.__selected_cell, collider)
            self.__gs.moves_count += 1

        if not collider.figure:
            self.__markers.clear()
        self.__selected_cell = collider

    def move_figure(self, old_cell: 'Cell', new_cell: 'Cell', fig_type=None) -> None:
        if not old_cell.figure:
            return
        if new_cell.figure:
            player = self.__gs.next_player
            player.add_defeated(str(new_cell.figure))

        fig = old_cell.figure.__class__ if not fig_type else fig_type
        new_cell.figure = fig(new_cell, old_cell.figure.player, old_cell.figure.moves_count)
        old_cell.figure = None
        new_cell.figure.moves_count += 1

    def _update(self) -> None:
        for row in self.__field:
            for cell in row:
                cell.draw()

        if self.__selected_cell:
            if self.__selected_cell.figure and self.__selected_cell.figure.player == self.__gs.next_player:
                pg.draw.rect(self.__gs.canvas, utility.RED, self.__selected_cell.rect, 5)
                for marker in self.__markers:
                    cell = self.get(marker)
                    if not cell.figure or cell.figure.player != self.__gs.next_player:
                        color = utility.GREEN if not cell.figure else utility.RED
                        pg.draw.ellipse(self.__gs.canvas, color, cell.rect.inflate(-80, -80))
