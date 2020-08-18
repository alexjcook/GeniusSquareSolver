#! /usr/bin/env python3

import random
import time
import numpy as np
import matplotlib.pyplot as plt


SOLUTION_LIMIT = 20  # stop after finding this many solutions
PLOT_SOLUTIONS = True
ROW_LABELS = list('ABCDEF')
COL_LABELS = list(map(str, range(1, 7)))
DEFAULT_DICE = [
    'A1 F3 D1 E2 D2 C1',
    'A2 A3 B1 B2 C2 B3',
    'A4 B5 C5 C6 F6 D6',
    'A5 F2 A5 F2 E1 B6',
    'A6 F1 A6 F1 A6 F1',
    'B4 C3 C4 D3 E3 D4',
    'D5 E4 E5 E6 F4 F5'
]


class GamePiece:

    def __init__(self, name, uid, color, mask):

        self.name = name
        self.uid = uid
        self.color = color
        self.mask = []

        for flip in [True, False]:
            for rotation in [0, 1, 2, 3]:
                new_mask = np.array(mask)
                new_mask = np.fliplr(new_mask) if flip else new_mask
                new_mask = np.rot90(new_mask, rotation)

                if not self.mask_exists(new_mask):
                    self.mask.append(new_mask)

    def mask_exists(self, new_mask):
        for m in self.mask:
            if np.array_equal(m, new_mask):
                return True
        return False


class Dice:

    def __init__(self, faces):

        faces_as_list = faces.split(' ')
        self.faces = faces_as_list

    def roll(self):

        random_face_index = random.randrange(len(self.faces))
        face = self.faces[random_face_index]
        row = ROW_LABELS.index(face[0])
        col = COL_LABELS.index(face[1])
        return face, (row, col)


class Board:

    def __init__(self, context, from_existing_board=None):
        self.context = context
        if from_existing_board is None:
            self.space = np.zeros((6, 6), np.int8)
            self.depth = 0
        else:
            self.space = from_existing_board.space.copy()
            self.depth = from_existing_board.depth + 1

    def draw(self):

        # update board image
        ax_sq = self.context.plot_ax[0]
        color_data = np.ones((6, 6, 3))
        for row, row_val in enumerate(self.space):
            for col, col_val in enumerate(row_val):
                if col_val == 99:  # blocker piece
                    color = self.context.all_pieces[0].color
                    circ = plt.Circle((col, row), radius=0.45, color=color)
                    ax_sq.add_patch(circ)
                elif col_val > 0:
                    color = self.context.piece_colors.get(col_val, [0, 0, 0])
                    color_data[row, col] = color
        ax_sq.imshow(color_data)

        # update line plot
        x = [0] + self.context.solution_ts
        y = range(len(self.context.solution_ts) + 1)
        self.context.plot_ln.set_data(x, y)
        self.context.plot_ax[1].set_xlim([0, max(10, time.process_time())])
        self.context.plot_ax[1].set_ylim([0, SOLUTION_LIMIT + 1])
        plt.pause(0.001)  # show plot and allow processing to continue

    def drawToConsole(self):
        output = "    "
        output += "  ".join(COL_LABELS) + "\n"
        for row_index, row in enumerate(self.space):
            output += ROW_LABELS[row_index] + " "
            output += ''.join([str(col).rjust(3) for col in row])
            output += '\n'
        print(output)

    def isSolved(self):
        empty_spaces = self.space[self.space == 0]
        solved = (empty_spaces.size == 0)
        return solved

    def piece_fits_at_space(self, row, col, piece):
        for mask_index, piece_mask in enumerate(piece.mask):
            piece_rows, piece_cols = piece_mask.shape

            board_slice = self.space[row:row+piece_rows, col:col+piece_cols]
            if board_slice.shape != piece_mask.shape:
                # this shape & orientation extends past the board edges, skip
                continue
            board_mask = (board_slice == 0) # array of booleans where True is an empty space

            # If boolean "AND" operation of empty spaces & piece mask results
            # in the piece mask, it means we can fit it in!
            if np.array_equal(board_mask & piece_mask, piece_mask):
                return mask_index
        return None # does not fit

    def place_piece(self, row, col, piece, orientation=0):

        piece_mask = piece.mask[orientation]
        piece_rows, piece_cols = piece_mask.shape
        board_slice = self.space[row:row+piece_rows, col:col+piece_cols]
        add_slice = piece_mask * piece.uid
        board_slice[:] += add_slice  # replace the range

    def recursiveSolve(self, remaining, limit=1):

        piece = remaining[0]
        for row in range(6):
            for col in range(6): 
                orientation = self.piece_fits_at_space(row, col, piece)
                if orientation is not None:
                    new_board = Board(self.context, self)
                    new_board.place_piece(row, col, piece, orientation)
                    new_remaining = remaining.copy()
                    new_remaining.remove(piece)

                    if new_board.isSolved():
                        self.context.solution_ts.append(time.process_time() - self.context.start_ts)
                        
                        print('Found a solution after {:.2f} seconds'.format(time.process_time() - self.context.start_ts))
                        new_board.drawToConsole()
                        if PLOT_SOLUTIONS:
                            new_board.draw()
                        return (len(self.context.solution_ts) >= limit)

                    if not new_remaining:  # No remaining pieces we can place!
                        return False      # Jump back to shallower recursion depth

                    hit_limit = new_board.recursiveSolve(new_remaining, limit)
                    if hit_limit:  # and (len(self.context.solution_ts) >= limit):
                        return True #exit out of the recursion
        return False # cannot solve at this depth


class GameContext:

    def __init__(self):

        self.start_ts = 0
        self.solution_ts = []

        # This feels really messy. Is there a better way to do this?
        self.all_pieces = []
        self.all_pieces.append(GamePiece('Blocker', 99, [0.6, 0.4, 0.05], [[True]]))
        self.all_pieces.append(GamePiece('Blue', 1, [0,0,1.0], [[True]]))
        self.all_pieces.append(GamePiece('Brown', 2, [0.5,0.3,0.3], [[True, True]]))
        self.all_pieces.append(GamePiece('Orange', 3, [1.0,0.4,0], [[True, True, True]]))
        self.all_pieces.append(GamePiece('Grey', 4, [0.5,0.5,0.5], [[True, True, True, True]]))
        self.all_pieces.append(GamePiece('Red', 5, [1.0,0,0], [[False, True, True],
                                                                [True, True, False]]))
        self.all_pieces.append(GamePiece('Yellow', 6, [1.0,0.7,0], [[True, True, True],
                                                                    [False, True, False]]))
        self.all_pieces.append(GamePiece('Cyan', 7, [0.2,0.5,1.0], [[True, True, True],
                                                                    [True, False, False]]))
        self.all_pieces.append(GamePiece('Green', 8, [0,1.0,0], [[True, True],
                                                                    [True, True]]))
        self.all_pieces.append(GamePiece('Purple', 9, [0.5,0,0.5], [[True, True],
                                                                        [True, False]]))
        self.piece_colors = {x.uid: x.color for x in self.all_pieces}
        self.play_pieces = self.all_pieces[1:]  # all pieces except the Blocker are available to play
        
        self.board = Board(self)

        if PLOT_SOLUTIONS:
            self.plot_fig, self.plot_ax = plt.subplots(1, 2, figsize=(10, 5))
            # configure axes for Square board plot
            self.plot_ax[0].xaxis.tick_top()
            self.plot_ax[0].set_xticks(np.arange(6))
            self.plot_ax[0].set_yticks(np.arange(6))
            self.plot_ax[0].set_xticklabels(COL_LABELS)
            self.plot_ax[0].set_yticklabels(ROW_LABELS)

            # configure axes for Line plot
            self.plot_ax[1].set_xlabel('Seconds')
            self.plot_ax[1].set_ylabel('Solutions')
            self.plot_ax[1].xaxis.get_major_locator().set_params(integer=True)
            self.plot_ax[1].yaxis.get_major_locator().set_params(integer=True)
            self.plot_ln, = self.plot_ax[1].plot([0], [0], 'r-')
            self.plot_fig.tight_layout()

            plt.ion()
            plt.show()

    def roll_dice(self):

        print("Rolling dice...")
        dice_result_output = ' '
        for d in DEFAULT_DICE:
            # Create & roll each dice and place a blocker piece on the board
            dice = Dice(d)
            face, (row, col) = dice.roll()
            dice_result_output += face + ' '
            self.board.place_piece(row, col, self.all_pieces[0])
        print(dice_result_output + '\n')

    def solve(self, limit, strategic_sort):

        self.play_pieces.sort(key=lambda x: strategic_sort.index(x.uid))
        sort_string = [str(x.uid) + '-' + x.name for x in self.play_pieces]

        out = 'Attempting to find {} solutions '.format(limit)
        out += 'using the following sort strategy:\n'
        out += ', '.join(sort_string) + '\n'
        print(out)

        self.start_ts = time.process_time()
        hit_limit = self.board.recursiveSolve(self.play_pieces, limit)
        duration = time.process_time() - self.start_ts
        if limit > 1:
            if hit_limit:
                print('Hit limit of {} solutions in {:.2f} seconds'.format(
                    len(self.solution_ts), duration))
            else:
                print('Found a total of {} solutions in {:.2f} seconds'.format(
                    len(self.solution_ts), duration))




def main():

    game = GameContext()
    game.roll_dice()
    game.board.drawToConsole()
    if PLOT_SOLUTIONS:
        game.board.draw()

    strategic_sort = [4, 5, 6, 7, 8, 9, 3, 2, 1]
    # Grey, Red, Yellow, Cyan, Green, Purple, Orange, Brown, Blue
    
    game.solve(SOLUTION_LIMIT, strategic_sort)

    if PLOT_SOLUTIONS:
        print('Finished. Close plot window to exit.')
        plt.ioff()
        plt.show()  # keeps program running until the plot is closed


if __name__ == "__main__":
    main()
