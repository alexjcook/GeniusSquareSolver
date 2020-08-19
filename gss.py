#! /usr/bin/env python3

import random
import time
import numpy as np
import matplotlib.pyplot as plt


SOLUTION_LIMIT = 10  # stop after finding this many solutions
PLOT_SOLUTIONS = True  # Use Matplotlib to draw board and line plot
CONTINUOUS_DRAW = False  # continuously draw while solving (slow!!)
ROW_LABELS = list('ABCDEF')
COL_LABELS = list(map(str, range(1, 7)))

# The Genius Square uses a special set of dice, which means
# only certain roll combinations are possible.
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
    """
    A class to represent game pieces that can be placed on the board.
    i.e. blocker pieces and coloured game pieces.
    """

    def __init__(self, name, uid, color, mask):
        """
        Initialise game piece and precompute a mask for all possible
        orientations of that piece (by flipping and rotating).

        Args:
            name (str): Descriptive name of the game piece.
            uid (int): Unique id to fill board spaces when piece is placed.
            color (list of float): Color in [R,G,B] as a percentage (0.0-1.0).
            mask (2D list of bool): Array representing shape of game piece.
        """

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
        """
        Determines if the given mask is identical to any existing generated
        mask for this game piece.

        Args:
            new_mask (Numpy ndarray): new mask for comparison

        Returns:
            True if given mask is identical to any existing mask, False
            otherwise.
        """
        for m in self.mask:
            if np.array_equal(m, new_mask):
                return True
        return False


class Dice:
    """
    A class to represent a singular die, but Dice sounds nicer!
    """

    def __init__(self, faces):
        """
        Initialise the die and populate list of die faces.

        Args:
            faces (str): Space delimited list of faces (eg. "A1 B3 E2 ...")
        """
        faces_as_list = faces.split(' ')
        self.faces = faces_as_list

    def roll(self):
        """
        Simulate a roll of the die by randomly choosing a face.

        Returns:
            Die face as string and a tuple of board indices
            (row: int, column: int) corresponding to the die face.
        """
        random_face_index = random.randrange(len(self.faces))
        face = self.faces[random_face_index]
        row = ROW_LABELS.index(face[0])
        col = COL_LABELS.index(face[1])
        return face, (row, col)


class Board:
    """
    A class to represent the state of the game board, with any number of pieces
    already placed on the board.
    """

    def __init__(self, context, from_existing_board=None):
        """
        Initialise the board, then populate all spaces as empty, or copied
        from an existing board if provided.

        Args:
            context (GameContext): Game context to associate with this board.
            from_existing_board (Board, optional): An existing Board from which
                the new Board will be populated from. If None, new
                Board will be empty. Defaults to None.
        """

        self.context = context
        if from_existing_board is None:
            self.space = np.zeros((6, 6), np.int8)
        else:
            self.space = from_existing_board.space.copy()

    def draw(self):
        """
        Uses Matplotlib to displays a visual representation of the board, along
        with a line plot of the number of solutions discovered (using the
        board's GameContext).
        """

        # update board image
        ax_sq = self.context.plot_ax[0]
        color_data = np.ones((6, 6, 3))
        for row, row_val in enumerate(self.space):
            for col, col_val in enumerate(row_val):
                if col_val > 0 and col_val < 99:  # not a blocker piece
                    color = self.context.piece_colors.get(col_val, [1, 1, 1])
                    color_data[row, col] = color
        self.context.plot_im.set_data(color_data)

        # update line plot
        x = [0] + self.context.solution_ts
        y = range(len(self.context.solution_ts) + 1)
        self.context.plot_ln.set_data(x, y)
        self.context.plot_ax[1].set_xlim([0, max(10, time.process_time())])
        self.context.plot_ax[1].set_ylim([0, SOLUTION_LIMIT + 1])
        plt.pause(0.001)  # show plot and allow processing to continue

    def draw_to_console(self):
        """Prints visual representation of the board."""

        output = "    "
        output += "  ".join(COL_LABELS) + "\n"
        for row_index, row in enumerate(self.space):
            output += ROW_LABELS[row_index] + " "
            output += ''.join([str(col).rjust(3) for col in row])
            output += '\n'
        print(output)

    def is_solved(self):
        """
        Checks if the Board has been solved by counting the number of empty
        spaces.

        Returns:
            True if there are no empty spaces, otherwise False.
        """
        empty_spaces = self.space[self.space == 0]
        solved = (empty_spaces.size == 0)
        return solved

    def piece_fits_at_space(self, row, col, piece):
        """
        Checks if a GamePiece can fit on the Board at the given row & column,
        by iterating through each of the piece's orientation masks. The top-
        left of the piece mask will be used as the origin.

        Args:
            row (int): Board row index at which to check.
            col (int): Board column index at which to check.
            piece (GamePiece): the GamePiece to check.

        Returns:
            index to the GamePiece's mask for the first orientation that
        will fit on the Board. If none fit, return None.
        """

        for mask_index, piece_mask in enumerate(piece.mask):
            piece_rows, piece_cols = piece_mask.shape

            # Get the slice of the board where the piece will be placed
            board_slice = self.space[row:row+piece_rows, col:col+piece_cols]

            if board_slice.shape != piece_mask.shape:
                # the size of the resulting board slice and the size of the
                # piece don't match up, which means the piece extended past the
                # edge of the board.
                continue

            # Create a mask of the board slice where True is an empty space
            board_mask = (board_slice == 0)

            # If boolean "AND" operation of empty spaces & piece mask results
            # in the piece mask, it means we can fit it in!
            if np.array_equal(board_mask & piece_mask, piece_mask):
                return mask_index

        return None  # does not fit

    def place_piece(self, row, col, piece, orientation=0):
        """
        Place a GamePiece on the board at the given row & column. The top-left
        of the piece will be used as the origin.

        Args:
            row (int): Board row index at which to place piece.
            col (int): Board column index at whcih to place piece.
            piece (GamePiece): the GamePiece to place.
            orientation (int): the index of the GamePiece's orientation mask to
                use when placing the piece. Default to 0.
        """
        piece_mask = piece.mask[orientation]
        piece_rows, piece_cols = piece_mask.shape
        board_slice = self.space[row:row+piece_rows, col:col+piece_cols]
        add_slice = piece_mask * piece.uid
        board_slice[:] += add_slice  # replace the range

    def recursive_solve(self, remaining, limit=1):
        """
        Recursive function to iterate through all board spaces and remaining
        pieces, to check if any will fit on the board. If a piece can fit, a
        copy of the board and remaining piece list is made, and the piece is
        placed on the copy. The board copy is checked to see if it has been
        solved, and if not, this function is called on the copy.

        Args:
            remaining (list of GamePiece): List of pieces available to place.
            limit (int): the number of solutions to find. Default to 1.

        Returns:
            True if a solution was found and the limit was reached, or if
            the limit had already been reached in a deeper call to this
            function. Otherwise False, when all pieces have been used or when
            all spaces have been checked and no pieces fit.
        """
        piece = remaining[0]
        for row in range(6):
            for col in range(6):
                orientation = self.piece_fits_at_space(row, col, piece)
                if orientation is not None:
                    new_board = Board(self.context, self)
                    new_board.place_piece(row, col, piece, orientation)
                    if CONTINUOUS_DRAW:
                        new_board.draw()
                    new_remaining = remaining.copy()
                    new_remaining.remove(piece)

                    if new_board.is_solved():
                        duration = time.process_time() - self.context.start_ts
                        self.context.solution_ts.append(duration)

                        print('Found a solution after {:.2f} seconds'.format(duration))
                        new_board.draw_to_console()
                        if PLOT_SOLUTIONS:
                            new_board.draw()
                            if CONTINUOUS_DRAW:
                                time.sleep(1)
                        return (len(self.context.solution_ts) >= limit)

                    if not new_remaining:
                        return False  # No remaining pieces to place!

                    hit_limit = new_board.recursive_solve(new_remaining, limit)
                    if hit_limit:  # Limit reached in a deeper call
                        return True  # Quickly exit out of the recursion
        # cannot solve at this depth, no pieces fit
        return False


class GameContext:
    """
    A class to represent the game state and bring together all the objects
    needed to play. Constructs all game pieces, dice, and initial board.
    """

    def __init__(self):
        """
        Initialise the GameContext, along with creating all the game pieces,
        the dice, and the initial board.
        """
        self.start_ts = 0
        self.solution_ts = []

        # This feels really messy. Is there a better way to do this?
        # Should probably be defined in a JSON file and loaded in.
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

        # Create a dict of piece:RGB color, this will be used later to
        # efficiently draw the board
        self.piece_colors = {x.uid: x.color for x in self.all_pieces}

        # all pieces except the Blocker are available to play
        self.play_pieces = self.all_pieces[1:]

        # create the "root" board
        self.board = Board(self)

        if PLOT_SOLUTIONS:

            # Get all the Matplotlib stuff configured to draw the board
            self.plot_fig, self.plot_ax = plt.subplots(1, 2, figsize=(10, 5))
            self.plot_ax[0].xaxis.tick_top()
            self.plot_ax[0].set_xticks(np.arange(6))
            self.plot_ax[0].set_yticks(np.arange(6))
            self.plot_ax[0].set_xticklabels(COL_LABELS)
            self.plot_ax[0].set_yticklabels(ROW_LABELS)
            blank_data = np.ones((6, 6, 3))
            self.plot_im = self.plot_ax[0].imshow(blank_data)

            # configure Line plot
            self.plot_ax[1].set_xlabel('Seconds')
            self.plot_ax[1].set_ylabel('Solutions')
            self.plot_ax[1].xaxis.get_major_locator().set_params(integer=True)
            self.plot_ax[1].yaxis.get_major_locator().set_params(integer=True)
            self.plot_ln, = self.plot_ax[1].plot([0], [0], 'r-')
            self.plot_fig.tight_layout()

            plt.ion()  # Matplotlib interactive mode ON
            plt.show()  # Show the board & plot

    def roll_dice(self):
        """
        Simulate rolling the dice
        """
        print("Rolling dice...")
        dice_result_output = ' '
        for d in DEFAULT_DICE:
            dice = Dice(d)
            face, (row, col) = dice.roll()  # get a random face from the die
            dice_result_output += face + ' '
            self.board.place_piece(row, col, self.all_pieces[0])
            self.draw_blocker(row, col)
        print(dice_result_output + '\n')

    def draw_blocker(self, row, col):
        """
        Draw a blocker on the board at the given row & column.

        Args:
            row (int): Board row index at which to place piece.
            col (int): Board column index at whcih to place piece.
        """
        if PLOT_SOLUTIONS:
            color = self.all_pieces[0].color
            circ = plt.Circle((col, row), radius=0.45, color=color)
            self.plot_ax[0].add_patch(circ)

    def solve(self, limit, strategic_sort):
        """
        Finds a number of solutions (up to the given limit) for the
        GameContext's board. Prints a summary of solutions found and the
        duration.

        Args:
            limit (int): Number of solutions to find.
            strategic_sort (list of int): The list of GamePiece uid's (1-9),
                sorted in the order in which to attempt to place on the board.
                The most efficient strategy is to place the larger or more
                complex pieces first.
        """

        # sort the list of play pieces according to the given strategy
        self.play_pieces.sort(key=lambda x: strategic_sort.index(x.uid))
        sort_string = [str(x.uid) + '-' + x.name for x in self.play_pieces]

        out = 'Attempting to find {} solutions '.format(limit)
        out += 'using the following sort strategy:\n'
        out += ', '.join(sort_string) + '\n'
        print(out)

        self.start_ts = time.process_time()

        # the guts of the action starts here!
        hit_limit = self.board.recursive_solve(self.play_pieces, limit)

        duration = time.process_time() - self.start_ts

        if limit > 1:
            if hit_limit:
                print('Hit limit of ', end='')
            else:
                print('Found a total of ', end='')

            print('{} solutions in {:.2f} seconds'.format(
                len(self.solution_ts), duration))


def main():
    """
    Create the GameContext, roll the dice, and find solutions.
    """
    game = GameContext()
    game.roll_dice()
    game.board.draw_to_console()
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
