#! /usr/bin/env python3

import random
import time
import numpy as np
import matplotlib.pyplot as plt


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
SOLUTION_LIMIT = 1  # stop after finding this many solutions


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

    def __init__(self, from_existing_board=None):
        
        if from_existing_board is None:
            self.space = np.zeros((6, 6), np.int8)
            self.depth = 0
        else:
            self.space = from_existing_board.space.copy()
            self.depth = from_existing_board.depth + 1

    def draw(self):

        color_data = np.ones((6, 6, 3))
        fig, ax = plt.subplots()

        for row, row_val in enumerate(self.space):
            for col, col_val in enumerate(row_val):
                if col_val == 99:  # blocker piece
                    color = all_pieces[0].color
                    circ = plt.Circle((col, row), radius=0.45, color=color)
                    ax.add_patch(circ)
                elif col_val > 0:
                    color_data[row, col] = piece_colors.get(col_val, [0, 0, 0])

        ax.imshow(color_data)
        ax.xaxis.tick_top()
        ax.set_xticks(np.arange(6))
        ax.set_yticks(np.arange(6))
        ax.set_xticklabels(COL_LABELS)
        ax.set_yticklabels(ROW_LABELS)
        plt.draw()
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
                    newBoard = Board(self)
                    newBoard.place_piece(row, col, piece, orientation)
                    newRemaining = remaining.copy()
                    newRemaining.remove(piece)

                    if newBoard.isSolved():
                        global nSolutions, start_time
                        nSolutions += 1
                        print('Found a solution in {:.2f} seconds'.format(time.process_time() - start_time))
                        newBoard.drawToConsole()
                        newBoard.draw()
                        return (nSolutions >= limit)

                    if not newRemaining:  # No remaining pieces we can place!
                        return False      # Jump back to shallower recursion depth

                    solutionFound = newBoard.recursiveSolve(newRemaining, limit)
                    if solutionFound and (nSolutions >= limit):
                        return True #exit out of the recursion
        return False # cannot solve at this depth




all_pieces = []
all_pieces.append(GamePiece('Blocker', 99, [0.6, 0.4, 0.05], False, False, [[True]]))
all_pieces.append(GamePiece('Blue', 1, [0,0,1.0], False, False, [[True]]))
all_pieces.append(GamePiece('Brown', 2, [0.5,0.3,0.3], True, False, [[True, True]]))
all_pieces.append(GamePiece('Orange', 3, [1.0,0.4,0], True, False, [[True, True, True]]))
all_pieces.append(GamePiece('Grey', 4, [0.5,0.5,0.5], True, False, [[True, True, True, True]]))
all_pieces.append(GamePiece('Red', 5, [1.0,0,0], True, True, [[False, True, True],
                                                        [True, True, False]]))
all_pieces.append(GamePiece('Yellow', 6, [1.0,0.7,0], True, False,[[True, True, True],
                                                            [False, True, False]]))
all_pieces.append(GamePiece('Cyan', 7, [0.2,0.5,1.0], True, True, [[True, True, True],
                                                            [True, False, False]]))
all_pieces.append(GamePiece('Green', 8, [0,1.0,0], False, False, [[True, True],
                                                            [True, True]]))
all_pieces.append(GamePiece('Purple', 9, [0.5,0,0.5], True, False, [[True, True],
                                                                [True, False]]))
piece_colors = {x.uid: x.color for x in all_pieces}

play_pieces = all_pieces[1:]  # all pieces except the Blocker are available to play

theBoard = Board()

# Roll each dice and place a blocker piece on the board
print("Rolling dice...")
dice_result_output = ' '
for d in DEFAULT_DICE:
    dice = Dice(d)
    face, (row, col) = dice.roll()
    dice_result_output += face + ' '
    theBoard.place_piece(row, col, all_pieces[0])  # place the blocker pieces
print(dice_result_output + '\n')

print('Using following stategy:')
strategic_sort = [4, 5, 6, 7, 8, 9, 3, 2, 1]  # Grey, Red, Yellow, Cyan, Green, Purple, Orange, Brown, Blue
play_pieces.sort(key=lambda x: strategic_sort.index(x.uid))
print(', '.join([x.name for x in play_pieces]) + '\n')

print('Solving...')
start_time = time.process_time()
nSolutions = 0
theBoard.recursiveSolve(play_pieces, SOLUTION_LIMIT)
print('Found {} solutions in {:.2f} seconds'.format(nSolutions, time.process_time() - start_time))
plt.show() #keeps program running until the plot is closed
