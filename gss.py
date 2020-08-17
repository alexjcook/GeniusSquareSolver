#! /usr/bin/env python3

import random
import time
import numpy as np
import matplotlib.pyplot as plt

ROW_LABELS = list('ABCDEF')
COL_LABELS = list(map(str,range(1, 7)))


class GamePiece:

    def __init__(self, name, uid, color,
                 checkRotated, checkFlipped, mask):
        self.name = name
        self.uid = uid
        self.color = color
        self.checkRotated = checkRotated
        self.checkFlipped = checkFlipped
        self.mask = np.array(mask)


class Dice:

    def __init__(self, face_list):
        self.faces = face_list

    def roll(self):
        random_face_index = random.randrange(len(self.faces))
        face = self.faces[random_face_index]
        row = ROW_LABELS.index(face[0])
        col = COL_LABELS.index(face[1])
        return face, (row, col)


class Board:

    def __init__(self, fromExistingBoard=None):

        self.depth = 0
        if fromExistingBoard is None:
            self.space = np.zeros((6, 6), np.int8)
        else:
            self.space = fromExistingBoard.space.copy()

    def draw(self):

        data_with_color = np.ones((6, 6, 3))
        fig, ax = plt.subplots()

        for rowIndex, row in enumerate(self.space):
            for colIndex, col in enumerate(row):
                if col == 99: # blocker piece
                    color = all_pieces[0].color
                    circ = plt.Circle((colIndex, rowIndex), radius=0.45, color=color)
                    ax.add_patch(circ)
                elif col > 0:
                    data_with_color[rowIndex, colIndex] = piece_colors.get(col, [0, 0, 0])

        ax.imshow(data_with_color)
        ax.xaxis.tick_top()
        ax.set_xticks(np.arange(6))
        ax.set_yticks(np.arange(6))

        ax.set_xticklabels(COL_LABELS)
        ax.set_yticklabels(ROW_LABELS)

        plt.draw()
        plt.pause(0.001)
        # show plot and allow processing to continue

    def drawToConsole(self):
        output = "    "
        output += "  ".join(COL_LABELS) + "\n"
        for rowIndex, row in enumerate(self.space):
            output += ROW_LABELS[rowIndex] + " "
            for colIndex, col in enumerate(row):
                output += str(col).rjust(3)
            output += '\n'
        print(output)

    def isSolved(self):
        empty_spaces = self.space[self.space == 0]
        solved = (empty_spaces.size == 0)
        return solved

    def pieceFitsAtSpace(self, piece, row, col):
        flipList = [0,1] if piece.checkFlipped else [0]
        rotateList = [0,1,2,3] if piece.checkRotated else [0]

        for flip in flipList:
            for rotation in rotateList:
                pieceRows, pieceCols = piece.mask.shape

                if rotation % 2 != 0: # for odd rotations, swap row & col sizes
                    pieceRows, pieceCols = pieceCols, pieceRows

                boardSlice = self.space[row:row+pieceRows, col:col+pieceCols]
                pieceSlice = np.fliplr(piece.mask) if flip else piece.mask
                pieceSlice = np.rot90(pieceSlice, rotation)
                if boardSlice.shape != pieceSlice.shape:
                    continue # this shape & orientation extends past the board edges, skip

                boardSliceMask = (boardSlice == 0) # array of booleans where True is an empty space
                if np.array_equal(boardSliceMask & pieceSlice, pieceSlice):
                    # intersection of empty spaces & piece shape results in the piece shape, it means we can fit it in!
                    return (rotation, flip)
        return None # does not fit

    def placePiece(self, piece, row, col, orientation):
        pieceRows, pieceCols = piece.mask.shape
        if orientation[0] % 2 != 0: # for odd rotations, swap row & col sizes
            pieceRows, pieceCols = pieceCols, pieceRows

        boardSlice = self.space[row:row+pieceRows, col:col+pieceCols]
        pieceSlice = np.fliplr(piece.mask) if orientation[1] else piece.mask
        pieceSlice = np.rot90(pieceSlice, orientation[0])

        addSlice = pieceSlice * piece.uid
        boardSlice[:] += addSlice # we want to replace the range, not update reference to point to addSlice

        
d = []
d.append(Dice(['A1','F3','D1','E2','D2','C1']))
d.append(Dice(['A2','A3','B1','B2','C2','B3']))
d.append(Dice(['A4','B5','C5','C6','F6','D6']))
d.append(Dice(['A5','F2','A5','F2','E1','B6']))
d.append(Dice(['A6','F1','A6','F1','A6','F1']))
d.append(Dice(['B4','C3','C4','D3','E3','D4']))
d.append(Dice(['D5','E4','E5','E6','F4','F5']))

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

strategicSort = [4, 5, 6, 7, 8, 9, 3, 2, 1]

theBoard = Board()

print("Rolling dice...")
diceResult = ' '
for i in range(len(d)):  # iterate dice list and roll each one
    face, (row, col) = d[i].roll()
    diceResult += face + ' '
    theBoard.placePiece(all_pieces[0], row, col, (0, 0))  # place the blocker pieces
diceResult += '\n'
print(diceResult)


def recursiveSolve(board, remaining, stopAtFirstSolution = False):
    piece = remaining[0]
    for row in range(6):
        for col in range(6): 
            orientation = board.pieceFitsAtSpace(piece, row, col)
            if orientation != None:
                newBoard = Board(board)
                newBoard.depth = board.depth + 1
                newBoard.placePiece(piece, row, col, orientation)
                newRemaining = remaining.copy()
                newRemaining.remove(piece)

                if newBoard.isSolved():
                    global nSolutions, start_time
                    nSolutions += 1
                    print('Found a solution in {:.2f} seconds'.format(time.process_time() - start_time))
                    newBoard.drawToConsole()
                    
                    newBoard.draw()
                    return stopAtFirstSolution

                if not newRemaining: # no remaining pieces, jump back up a recursion level
                    return False

                solutionFound = recursiveSolve(newBoard, newRemaining, stopAtFirstSolution)
                if solutionFound and stopAtFirstSolution:
                    return True #exit out of the recursion
    return False # cannot solve at this depth


play_pieces.sort(key=lambda x: strategicSort.index(x.uid))
print('Using following stategy')
print([x.name for x in play_pieces])
print('Solving...')
start_time = time.process_time()
nSolutions = 0
recursiveSolve(theBoard, play_pieces, stopAtFirstSolution = True)
print('Found {} solutions in {:.2f} seconds'.format(nSolutions, time.process_time() - start_time))
plt.show() #keeps program running until the plot is closed
