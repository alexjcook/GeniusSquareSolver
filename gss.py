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

    def __init__(self, name, uid, color,
                 checkRotated, checkFlipped, mask):

        self.name = name
        self.uid = uid
        self.color = color
        self.checkRotated = checkRotated
        self.checkFlipped = checkFlipped
        self.mask = []

        flips = [0, 1] if checkFlipped else [0]
        rotations = [0, 1, 2, 3] if checkRotated else [0]

        for flip in flips:
            for rotation in rotations:
                new_mask = np.array(mask)
                new_mask = np.fliplr(new_mask) if flip else new_mask
                new_mask = np.rot90(new_mask, rotation)
                self.mask.append(new_mask)


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

        fig = self.context.plot_fig
        ax_sq = self.context.plot_ax[0]
        ax_ln = self.context.plot_ax[1]

        color_data = np.ones((6, 6, 3))
        

        for row, row_val in enumerate(self.space):
            for col, col_val in enumerate(row_val):
                if col_val == 99:  # blocker piece
                    color = self.context.all_pieces[0].color
                    circ = plt.Circle((col, row), radius=0.45, color=color)
                    ax_sq.add_patch(circ)
                elif col_val > 0:
                    color_data[row, col] = self.context.piece_colors.get(col_val, [0, 0, 0])

        ax_sq.imshow(color_data)

        x = [0] + self.context.solution_ts
        y = range(len(self.context.solution_ts)+1)
        self.context.plot_ln.set_xdata(x)
        self.context.plot_ln.set_ydata(y)
        ax_ln.set_xlim([0,max(10,time.process_time())])
        ax_ln.set_ylim([0,SOLUTION_LIMIT])
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
            pieceRows, pieceCols = piece_mask.shape

            boardSlice = self.space[row:row+pieceRows, col:col+pieceCols]
            if boardSlice.shape != piece_mask.shape:
                continue # this shape & orientation extends past the board edges, skip

            boardSliceMask = (boardSlice == 0) # array of booleans where True is an empty space
            if np.array_equal(boardSliceMask & piece_mask, piece_mask):
                # intersection of empty spaces & piece shape results in the piece shape, it means we can fit it in!
                return mask_index
        return None # does not fit


    def place_piece(self, row, col, piece, orientation=0):
        piece_mask = piece.mask[orientation]
        piece_rows, piece_cols = piece_mask.shape
        board_slice = self.space[row:row+piece_rows, col:col+piece_cols]
        add_slice = piece_mask * piece.uid
        board_slice[:] += add_slice # we want to replace the range, not update reference to point to addSlice

    def recursiveSolve(self, remaining, limit = 1):
        piece = remaining[0]
        for row in range(6):
            for col in range(6): 
                orientation = self.piece_fits_at_space(row, col, piece)
                if orientation != None:
                    newBoard = Board(self.context, self)
                    newBoard.place_piece(row, col, piece, orientation)
                    newRemaining = remaining.copy()
                    newRemaining.remove(piece)

                    if newBoard.isSolved():
                        self.context.solution_ts.append(time.process_time() - self.context.start_ts)
                        
                        print('Found a solution after {:.2f} seconds'.format(time.process_time() - self.context.start_ts))
                        newBoard.drawToConsole()
                        if PLOT_SOLUTIONS:
                            newBoard.draw()
                        return (len(self.context.solution_ts) >= limit)

                    if not newRemaining:  # No remaining pieces we can place!
                        return False      # Jump back to shallower recursion depth

                    solutionFound = newBoard.recursiveSolve(newRemaining, limit)
                    if solutionFound and (len(self.context.solution_ts) >= limit):
                        return True #exit out of the recursion
        return False # cannot solve at this depth

class GameContext:

    def __init__(self):
        
        self.start_ts = time.process_time()  # Note: will be overridden during Solve()
        self.solution_ts = []

        self.all_pieces = []
        self.all_pieces.append(GamePiece('Blocker', 99, [0.6, 0.4, 0.05], False, False, [[True]]))
        self.all_pieces.append(GamePiece('Blue', 1, [0,0,1.0], False, False, [[True]]))
        self.all_pieces.append(GamePiece('Brown', 2, [0.5,0.3,0.3], True, False, [[True, True]]))
        self.all_pieces.append(GamePiece('Orange', 3, [1.0,0.4,0], True, False, [[True, True, True]]))
        self.all_pieces.append(GamePiece('Grey', 4, [0.5,0.5,0.5], True, False, [[True, True, True, True]]))
        self.all_pieces.append(GamePiece('Red', 5, [1.0,0,0], True, True, [[False, True, True],
                                                                [True, True, False]]))
        self.all_pieces.append(GamePiece('Yellow', 6, [1.0,0.7,0], True, False,[[True, True, True],
                                                                    [False, True, False]]))
        self.all_pieces.append(GamePiece('Cyan', 7, [0.2,0.5,1.0], True, True, [[True, True, True],
                                                                    [True, False, False]]))
        self.all_pieces.append(GamePiece('Green', 8, [0,1.0,0], False, False, [[True, True],
                                                                    [True, True]]))
        self.all_pieces.append(GamePiece('Purple', 9, [0.5,0,0.5], True, False, [[True, True],
                                                                        [True, False]]))
        self.piece_colors = {x.uid: x.color for x in self.all_pieces}

        self.play_pieces = self.all_pieces[1:]  # all pieces except the Blocker are available to play
        
        self.board = Board(self)

        if PLOT_SOLUTIONS:
            
            self.plot_fig, self.plot_ax = plt.subplots(1, 2, figsize=(10,5))
            # configure axes for Square
            self.plot_ax[0].xaxis.tick_top()
            self.plot_ax[0].set_xticks(np.arange(6))
            self.plot_ax[0].set_yticks(np.arange(6))
            self.plot_ax[0].set_xticklabels(COL_LABELS)
            self.plot_ax[0].set_yticklabels(ROW_LABELS)

            # configure axes for Line
            self.plot_ax[1].set_xlabel('Seconds')
            self.plot_ax[1].set_ylabel('Solutions')
            self.plot_ax[1].xaxis.get_major_locator().set_params(integer=True)
            self.plot_ax[1].yaxis.get_major_locator().set_params(integer=True)
            self.plot_ln, = self.plot_ax[1].plot([0],[0],'r-')
            self.plot_fig.tight_layout()

            plt.ion()
            plt.show()



    def roll_dice(self):
        # Roll each dice and place a blocker piece on the board
        print("Rolling dice...")
        dice_result_output = ' '
        for d in DEFAULT_DICE:
            dice = Dice(d)
            face, (row, col) = dice.roll()
            dice_result_output += face + ' '
            self.board.place_piece(row, col, self.all_pieces[0])  # place the blocker pieces
        print(dice_result_output + '\n')

    def solve(self, limit):
        self.start_ts = time.process_time()
        self.board.recursiveSolve(self.play_pieces, limit)
        if limit > 1:
            print('Found a total of {} solutions in {:.2f} seconds'.format(
                len(self.solution_ts), time.process_time() - self.start_ts))
        if PLOT_SOLUTIONS:
            plt.show() #keeps program running until the plot is closed


def main():

    game = GameContext()
    game.roll_dice()
    game.board.drawToConsole()
    game.board.draw()

    print('Using following stategy:')
    strategic_sort = [4, 5, 6, 7, 8, 9, 3, 2, 1]  # Grey, Red, Yellow, Cyan, Green, Purple, Orange, Brown, Blue
    game.play_pieces.sort(key=lambda x: strategic_sort.index(x.uid))
    print(', '.join([x.name for x in game.play_pieces]) + '\n')

    print('Solving...')
    game.solve(SOLUTION_LIMIT)
    


if __name__ == "__main__": 
    main() 