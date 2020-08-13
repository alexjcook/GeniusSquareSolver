#! /usr/bin/env python3

import random
import time
import numpy as np
import matplotlib.pyplot as plt


rowFromLetter = {
    'A':0,
    'B':1,
    'C':2,
    'D':3,
    'E':4,
    'F':5
}
letterFromRow = list(rowFromLetter.keys())



class Block:

    def __init__(self, name, bId, blockColor, checkRotated, checkFlipped, blockArray):
        self.name = name
        self.bId = bId
        self.blockArray = np.array(blockArray)
        self.blockColor = blockColor
        self.checkRotated = checkRotated
        self.checkFlipped = checkFlipped


allPieces = []
allPieces.append(Block('Blue', 1, [0,0,1.0], False, False, [[True]]))
allPieces.append(Block('Brown', 2, [0.5,0.3,0.3], True, False, [[True, True]]))
allPieces.append(Block('Orange', 3, [1.0,0.4,0], True, False, [[True, True, True]]))
allPieces.append(Block('Grey', 4, [0.5,0.5,0.5], True, False, [[True, True, True, True]]))
allPieces.append(Block('Red', 5, [1.0,0,0], True, True, [[False, True, True],
                                                        [True, True, False]]))
allPieces.append(Block('Yellow', 6, [1.0,0.7,0], True, False,[[True, True, True],
                                                            [False, True, False]]))
allPieces.append(Block('Cyan', 7, [0.2,0.5,1.0], True, True, [[True, True, True],
                                                            [True, False, False]]))
allPieces.append(Block('Green', 8, [0,1.0,0], False, False, [[True, True],
                                                            [True, True]]))
allPieces.append(Block('Purple', 9, [0.5,0,0.5], True, False, [[True, True],
                                                                [True, False]]))
blockColors = {x.bId: x.blockColor for x in allPieces}

strategicSort = [4,5,6,7,8,9,3,2,1]


class Dice:
    sides = []
    face = 0
    def __init__(self, *args):
        self.sides = args
        self.roll()
        
    def roll(self):
        maxNum = len(self.sides)-1
        self.face = random.randint(0,maxNum)
        return self.sides[self.face]

    def getSpaceLocation(self):
        dieFace = self.sides[self.face]
        rowAlpha = dieFace[0]
        col = int(dieFace[1])-1
        row = rowFromLetter.get(rowAlpha,0)
        return (row, col)
        
class Board:
    #space = []

    def __init__(self, fromExistingBoard = None):
        self.depth = 0
        if fromExistingBoard != None:
            self.space = fromExistingBoard.space.copy()
        else:
            self.space = np.zeros((6,6), np.int8)

    def draw(self):

        x = list(rowFromLetter.keys())
        y = letterFromRow
        Z = np.ones((6,6,3))
        fig, ax = plt.subplots()

        for rowIndex, row in enumerate(self.space):
            for colIndex, col in enumerate(row):
                if col==99:
                    circ = plt.Circle((colIndex, rowIndex), radius=0.45, color=(0.6,0.4,0.05))
                    ax.add_patch(circ)
                elif col > 0:
                    Z[rowIndex,colIndex] = blockColors.get(col,[0,0,0])

        ax.imshow(Z)
        ax.xaxis.tick_top()
        ax.set_xticks(np.arange(len(x)))
        ax.set_yticks(np.arange(len(y)))
        ax.set_xticklabels(x)
        ax.set_yticklabels(np.arange(1,7))

        plt.draw()
        plt.pause(0.001)
        # show plot and allow processing to continue

    def drawToConsole(self):
        output = "    1  2  3  4  5  6\n"
        for rowIndex, row in enumerate(self.space):
            output += letterFromRow[rowIndex]+ " "
            for colIndex, col in enumerate(row):
                output += str(col).rjust(3)
            output += '\n'
        print(output)

    def isSolved(self):
        return (self.space[self.space==0].size == 0)


    def pieceFitsAtSpace(self, piece, row, col):
        flipList = [0,1] if piece.checkFlipped else [0]
        rotateList = [0,1,2,3] if piece.checkRotated else [0]

        for flip in flipList:
            for rotation in rotateList:
                pieceRows, pieceCols = piece.blockArray.shape

                if rotation % 2 != 0: # for odd rotations, swap row & col sizes
                    pieceRows, pieceCols = pieceCols, pieceRows

                boardSlice = self.space[row:row+pieceRows, col:col+pieceCols]
                pieceSlice = np.fliplr(piece.blockArray) if flip else piece.blockArray
                pieceSlice = np.rot90(pieceSlice, rotation)
                if boardSlice.shape != pieceSlice.shape:
                    continue # this shape & orientation extends past the board edges, skip

                boardSliceMask = (boardSlice == 0) # array of booleans where True is an empty space
                if np.array_equal(boardSliceMask & pieceSlice, pieceSlice):
                    # intersection of empty spaces & piece shape results in the piece shape, it means we can fit it in!
                    return (rotation, flip)
        return None # does not fit

    def placePiece(self, piece, row, col, orientation):
        pieceRows, pieceCols = piece.blockArray.shape
        if orientation[0] % 2 != 0: # for odd rotations, swap row & col sizes
            pieceRows, pieceCols = pieceCols, pieceRows

        boardSlice = self.space[row:row+pieceRows, col:col+pieceCols]
        pieceSlice = np.fliplr(piece.blockArray) if orientation[1] else piece.blockArray
        pieceSlice = np.rot90(pieceSlice, orientation[0])

        addSlice = pieceSlice * piece.bId
        boardSlice[:] += addSlice # we want to replace the range, not update reference to point to addSlice


    def setSpace(self, loc, val):
        row,col = loc[0],loc[1]
        self.space[row][col] = val
        
d = []
d.append(Dice('A1','F3','D1','E2','D2','C1'))
d.append(Dice('A2','A3','B1','B2','C2','B3'))
d.append(Dice('A4','B5','C5','C6','F6','D6'))
d.append(Dice('A5','F2','A5','F2','E1','B6'))
d.append(Dice('A6','F1','A6','F1','A6','F1'))
d.append(Dice('B4','C3','C4','D3','E3','D4'))
d.append(Dice('D5','E4','E5','E6','F4','F5'))

theBoard = Board()

print("Rolling dice...")
diceResult = ' '
for i in range(len(d)):
    diceResult += d[i].roll() + ' '
    theBoard.setSpace(d[i].getSpaceLocation(),99)
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

                if len(newRemaining)==0: # no remaining pieces, jump back up a recursion level
                    return False

                solutionFound = recursiveSolve(newBoard, newRemaining, stopAtFirstSolution)
                if solutionFound and stopAtFirstSolution:
                    return True #exit out of the recursion
    return False # cannot solve at this depth


allPieces.sort(key=lambda x: strategicSort.index(x.bId))
print('Using following stategy')
print([x.name for x in allPieces])
print('Solving...')
start_time = time.process_time()
nSolutions = 0
recursiveSolve(theBoard, allPieces, stopAtFirstSolution = True)
print('Found {} solutions in {:.2f} seconds'.format(nSolutions, time.process_time() - start_time))
plt.show() #keeps program running until the plot is closed
