import pygame as pg
from abc import abstractmethod, ABC
from typing import Any, NoReturn


def _get_direction(start_pos: tuple, end_pos: tuple) -> tuple:
    direction = (start_pos[0] - end_pos[0], start_pos[1] - end_pos[1])

    def norm(x: int):
        if x == 0:
            return 0
        return x // abs(x)

    return norm(direction[0]), norm(direction[1])


def _precalculate_allowed_pos(figure: 'BoardFigure', directions: tuple) -> set:
    positions = set()
    for direction in directions:
        x = figure.position[0]
        y = figure.position[1]
        for _ in range(figure.max_step):
            x += direction[0]
            y += direction[1]
            cell = figure.board.get((x, y))
            if not cell:
                break
            positions.add((x, y))
            if cell.figure:
                break
    return positions


def _is_attacked(figure: 'BoardFigure') -> bool:
    for i in range(figure.board.size):
        for j in range(figure.board.size):
            cell = figure.board.get((i, j))
            if cell.figure and cell.figure.player.player_type != figure.player.player_type:
                if figure.position in cell.figure.calc_allowed_positions():
                    return True
    return False


class BoardFigure(ABC):
    def __init__(self, image: pg.Surface, size: int, cell,
                 directions: tuple, max_step: int, player: 'Player', moves_count: int) -> None:
        self.__rect = cell.rect.inflate(-size, -size)
        self.__image = pg.transform.scale(image, self.__rect.size)
        self.__image.fill(player.color, None, pg.BLEND_RGB_MULT)

        self.__player = player
        self.__board = cell.board
        self.moves_count = moves_count
        self.__pos = cell.board_pos
        self.__max_step = max_step
        self.__directions = directions

    def __str__(self) -> str:
        return type(self).__name__

    @property
    def rect(self) -> pg.Rect:
        return self.__rect

    @property
    def image(self) -> pg.Surface:
        return self.__image

    @property
    def player(self) -> 'Player':
        return self.__player

    @property
    def position(self) -> tuple:
        return self.__pos

    @property
    def max_step(self) -> int:
        return self.__max_step

    @property
    def board(self) -> 'Board':
        return self.__board

    @property
    def directions(self) -> tuple:
        return self.__directions

    @abstractmethod
    def calc_allowed_positions(self) -> NoReturn:
        raise NotImplementedError()

    @property
    def allowed_positions(self) -> set:
        king = self.board.get_king(self.__player)
        pos, enemy_fig_pos = king.get_checked_positions()
        pos = set(pos)
        def_fig_count = 0
        for f_pos in pos:
            cell = self.board.get(f_pos)
            if cell and cell.figure and cell.figure.__class__ is not King \
                    and cell.figure.player.player_type == self.player.player_type:
                def_fig_count += 1

        if king.is_checked:
            if self.__class__ == King:
                return self.calc_allowed_positions().difference(pos)
            else:
                res_set = set()
                king_enemy_dir = _get_direction(king.position, enemy_fig_pos)
                for candidate in self.calc_allowed_positions():
                    candidate_enemy_dir = _get_direction(king.position, candidate)
                    if candidate_enemy_dir == king_enemy_dir and \
                            (candidate[0] < king.position[0] or candidate[1] < king.position[1]):
                        res_set.add(candidate)
                pos.add(enemy_fig_pos)
                return res_set.intersection(pos)
        else:
            if len(pos) > 0 and self.position in pos and self.__class__ != King and def_fig_count < 2:
                pos.add(enemy_fig_pos)
                return self.calc_allowed_positions().intersection(pos)
            else:
                return self.calc_allowed_positions()


class Pawn(BoardFigure):
    def __init__(self, cell: 'Cell', player: 'Player', moves_count: int = 0) -> None:
        image = pg.image.load('resources/pawn.png').convert_alpha()
        idx = -1 if player.player_type == 'white' else 1
        directions = ((0, idx), (-1, idx), (1, idx))
        super().__init__(image, 45, cell, directions, 2, player, moves_count)

    def calc_allowed_positions(self) -> set:
        positions = set()
        idx = -1 if self.player.player_type == 'white' else 1

        def has_fig(pos: tuple) -> bool:
            cell = self.board.get(pos)
            return cell and cell.figure

        is_on_start_set_pos = self.board.get_from_start_set(self.position) is Pawn

        def add_position(pos: tuple, func: Any) -> None:
            if func(pos):
                positions.add(pos)

        next_pos = (self.position[0], self.position[1] + idx)
        next_d_pos = (self.position[0], self.position[1] + 2 * idx)
        next_l_pos = (self.position[0] - 1, self.position[1] + idx)
        next_r_pos = (self.position[0] + 1, self.position[1] + idx)
        add_position(next_pos, lambda x: not has_fig(next_pos))
        add_position(next_d_pos, lambda x: not has_fig(next_pos) and not has_fig(next_d_pos) and is_on_start_set_pos)
        add_position(next_l_pos, lambda x: has_fig(next_l_pos))
        add_position(next_r_pos, lambda x: has_fig(next_r_pos))
        return positions


class Rook(BoardFigure):
    def __init__(self, cell: 'Cell', player: 'Player', moves_count: int = 0) -> None:
        image = pg.image.load('resources/rook.png').convert_alpha()
        directions = ((1, 0), (-1, 0), (0, -1), (0, 1))
        super().__init__(image, 30, cell, directions, cell.board.size, player, moves_count)

    def calc_allowed_positions(self) -> set:
        return _precalculate_allowed_pos(self, self.directions)


class Bishop(BoardFigure):
    def __init__(self, cell: 'Cell', player: 'Player', moves_count: int = 0) -> None:
        image = pg.image.load('resources/bishop.png').convert_alpha()
        directions = ((-1, 1), (1, -1), (-1, -1), (1, 1))
        super().__init__(image, 30, cell, directions, cell.board.size, player, moves_count)

    def calc_allowed_positions(self) -> set:
        return _precalculate_allowed_pos(self, self.directions)


class Knight(BoardFigure):
    def __init__(self, cell: 'Cell', player: 'Player', moves_count: int = 0) -> None:
        image = pg.image.load('resources/knight.png').convert_alpha()
        directions = ((2, 1), (1, 2), (-1, 2), (2, -1),
                      (1, -2), (-2, 1), (-1, -2), (-2, -1))
        super().__init__(image, 40, cell, directions, 1, player, moves_count)

    def calc_allowed_positions(self) -> set:
        return _precalculate_allowed_pos(self, self.directions)


class Queen(BoardFigure):
    def __init__(self, cell: 'Cell', player: 'Player', moves_count: int = 0) -> None:
        image = pg.image.load('resources/queen.png').convert_alpha()
        directions = ((1, 0), (-1, 0), (0, -1), (0, 1),
                      (1, -1), (-1, 1), (1, 1), (-1, -1))
        super().__init__(image, 20, cell, directions, cell.board.size, player, moves_count)

    def calc_allowed_positions(self) -> set:
        return _precalculate_allowed_pos(self, self.directions)


class King(BoardFigure):
    def __init__(self, cell: 'Cell', player: 'Player', moves_count: int = 0) -> None:
        image = pg.image.load('resources/king.png').convert_alpha()
        directions = ((1, 0), (-1, 0), (0, -1), (0, 1),
                      (1, -1), (-1, 1), (1, 1), (-1, -1))
        super().__init__(image, 20, cell, directions, 1, player, moves_count)

    def calc_allowed_positions(self) -> set:
        positions = _precalculate_allowed_pos(self, self.directions)
        occupied_by_other = set()
        for i in range(self.board.size):
            for j in range(self.board.size):
                cell = self.board.get((i, j))
                if cell.figure and cell.figure.player.player_type != self.player.player_type:
                    if cell.figure.__class__ is Pawn:
                        idx = -1 if cell.figure.player.player_type == 'white' else 1

                        pos = (cell.board_pos[0] + 1, cell.board_pos[1] + idx)
                        if self.board.get(pos):
                            occupied_by_other.add(pos)

                        pos = (cell.board_pos[0] - 1, cell.board_pos[1] + idx)
                        if self.board.get(pos):
                            occupied_by_other.add(pos)
                    elif cell.figure.__class__ is King:
                        occupied_by_other.update(_precalculate_allowed_pos(cell.figure, cell.figure.directions))
                    else:
                        occupied_by_other.update(cell.figure.calc_allowed_positions())

        # check for roque
        if self.moves_count == 0:
            left_rook_pos = (self.position[0] - 4, self.position[1])
            right_rook_pos = (self.position[0] + 3, self.position[1])

            def check_roque(rook_pos: tuple, spacing: tuple, bias: int) -> None:

                def has_fig(x: tuple, ind: int) -> bool:
                    t_cell = self.board.get((x[0] + ind, x[1]))
                    return t_cell and t_cell.figure

                r_cell = self.board.get(rook_pos)
                if r_cell and r_cell.figure and r_cell.figure.__class__ is Rook and r_cell.figure.moves_count == 0:
                    is_fig = False
                    for step in range(spacing[0], spacing[1]):
                        if has_fig(self.position, step):
                            is_fig = True
                    new_pos = (self.position[0] + bias, self.position[1])
                    if not is_fig and self.board.get(new_pos) and not _is_attacked(r_cell.figure):
                        positions.add(new_pos)

            check_roque(left_rook_pos, (-3, 0), -2)
            check_roque(right_rook_pos, (1, 3), 2)

        return positions.difference(occupied_by_other)

    def get_checked_positions(self) -> tuple:
        attack_positions = set()
        enemy_fig_positions = None
        for i in range(self.board.size):
            for j in range(self.board.size):
                cell = self.board.get((i, j))
                if cell.figure and cell.figure.player.player_type != self.player.player_type:
                    if cell.figure.__class__ is Pawn or cell.figure.__class__ is Knight:
                        pos = cell.figure.calc_allowed_positions()
                        if self.position in pos:
                            attack_positions = pos.intersection(self.position)
                            enemy_fig_positions = cell.figure.position
                    elif cell.figure.__class__ is not King:
                        pos = set()
                        direction = _get_direction(self.position, cell.figure.position)
                        x, y = cell.figure.position
                        while self.board.get((x, y)):
                            x += direction[0]
                            y += direction[1]
                            pos.add((x, y))
                            new_pos = self.board.get((x, y))
                            if new_pos and new_pos.figure:
                                if new_pos.figure.player.player_type == cell.figure.player.player_type:
                                    break

                        if self.position in pos:
                            attack_positions.update(pos)
                            enemy_fig_positions = cell.figure.position

        return frozenset(attack_positions), enemy_fig_positions

    @property
    def is_checked(self) -> bool:
        return _is_attacked(self)

    @property
    def is_mated(self) -> bool:
        if not self.is_checked:
            return False
        allowed_pos = set()
        for i in range(self.board.size):
            for j in range(self.board.size):
                cell = self.board.get((i, j))
                if cell.figure and cell.figure.player.player_type == self.player.player_type:
                    allowed_pos.update(cell.figure.allowed_positions)
        for pos in allowed_pos.copy():
            fig = self.board.get(pos).figure
            if fig and fig.player.player_type == self.player.player_type:
                allowed_pos.remove(pos)
        return len(allowed_pos) == 0
