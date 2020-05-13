import chess
import chess.svg
import random

TREE_LEVEL = 3
MY_COLOR = chess.WHITE
DEBUG_TREE = False

SCORE_MAX =  999999
SCORE_MIN = -999999

piece_scores = {
    chess.PAWN:1000,
    chess.KNIGHT:3000,
    chess.BISHOP:3000,
    chess.ROOK:3000,
    chess.QUEEN:5000,
    chess.KING:0 # king needs no inherent value as checkmate beats all scores
}

treeglobal = 0

def getBoardScore(board, mycolor):
    if board.is_checkmate():
        if board.turn == mycolor:
            return SCORE_MAX
        else:
            return SCORE_MIN
    score = 0

    for square, piece in board.piece_map().items():

        # --Add major piece values--
        piece_value = piece_scores[piece.piece_type]

        # --Add minor piece values (positioning)--
        row = square // 8 # (0-7) 1 -> 8
        col = square % 8  # (0-7) a -> h

        # Add value based on how far forward the piece is
        forward = row if piece.color == chess.WHITE else 7-row
        if forward == 1: forward = 0
        piece_value += forward

        # Add value based on how protected the piece is
        is_protected = len(board.attackers(piece.color, square)) > 0
        if is_protected and piece.color == mycolor:
            piece_value += 20
        # --Apply piece value to the score--
        if piece.color == mycolor:
            score += piece_value + 10 # Bonus if the piece is mine
        else:
            score -= piece_value

    # Add misc values
    if board.is_check():
        if board.turn == mycolor:
            score += 500
        else:
            score -= 500

    return score

def boardScoreTest():
    board1 = chess.Board("rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR b KQkq - 0 1")
    board2 = chess.Board("rnbqkbnr/pppppppp/8/1N6/8/8/PPPPPPPP/R1BQKBNR b KQkq - 0 1")
    score1 = getBoardScore(board1, chess.WHITE)
    score2 = getBoardScore(board2, chess.WHITE)
    print(score1, score2)


class Tree:
    def __init__(self, board, move):
        self.children = []
        self.board = board
        self.move = move
    def add_child(self, node):
        assert isinstance(node, Tree)
        self.children.append(node)

def getBestMove(board, mycolor):
    bestMove = None
    bestMoveScore = SCORE_MIN
    for move in board.legal_moves:
        board.push(move)
        score = getBoardScore(board, mycolor)
        board.pop()
        if score > bestMoveScore:
            bestMove = move
            bestMoveScore = score
    return bestMove

# Generates a tree of possible moves
# Each node in the tree stores the board, and the move used to
# get to that board
def generatePossibilityTree(board, move=None, depth=0):
    tree = Tree(board, move)
    if board.legal_moves == [] or depth == TREE_LEVEL:
        return tree
    for move in board.legal_moves:
        global treeglobal
        treeglobal += 1
        newBoard = board.copy()
        newBoard.push(move)
        tree.add_child(generatePossibilityTree(newBoard, move, depth+1))
    return tree

def runTree(tree, mycolor, depth=0):
    if len(tree.children) == 0:
        #if DEBUG_TREE: print(str(depth) + "---"*depth + " "+str(getBoardScore(tree.board, mycolor)) + " for " + tree.move.uci())
        return getBoardScore(tree.board, mycolor), tree.move
    else:
        if tree.board.turn == mycolor:
            maxscore = SCORE_MIN
            maxscoremove = None
            for child in random.sample(tree.children, len(tree.children)):
                score, move = runTree(child, mycolor, depth+1)
                if score > maxscore:
                    maxscore = score
                    maxscoremove = move
            if DEBUG_TREE: print(str(depth) + "---" * depth + " " + str(maxscore) + " max for " + maxscoremove.uci())
            return maxscore, tree.move if tree.move else maxscoremove
        else:
            minscore = SCORE_MAX
            minscoremove = None
            for child in random.sample(tree.children, len(tree.children)):
                score, move = runTree(child, mycolor, depth+1)
                if score < minscore:
                    minscore = score
                    minscoremove = move
            if DEBUG_TREE: print(str(depth) + "---" * depth + " " + str(minscore) + " min for " + minscoremove.uci())
            return minscore,  tree.move if tree.move else minscoremove

def showBoard(board):
    board_str = str(board)
    nl = 0
    for label in range(7,0,-1):
        nl = board_str.find("\n", nl) +1
        board_str = board_str[:nl] + str(label) + "| " + board_str[nl:]
        label -= 1
    whitescore = getBoardScore(board, chess.WHITE)
    blackscore = getBoardScore(board, chess.BLACK)
    board_str = " __a_b_c_d_e_f_g_h "+str(blackscore)+"\n8| " + board_str
    board_str += " " + str(whitescore)
    print(board_str)

def saveSvgBoard(board, mycolor, lastmove):
    svg = chess.svg.board(board=board, flipped=mycolor, lastmove=lastmove)
    with open("board.svg", "w") as f:
        f.write(svg)

def main():
    global treeglobal, DEBUG_TREE
    board = chess.Board()

    mycolor = chess.BLACK
    playself = False
    lastmove = None
    tempplayself = False
    while True:
        print()
        showBoard(board)
        saveSvgBoard(board, mycolor, lastmove)

        if board.is_checkmate(): break
        if board.is_check(): print("CHECK!")
        if board.turn == mycolor or playself or tempplayself:
            print("My Move")
            tree = generatePossibilityTree(board)
            print("Considering " + str(treeglobal) + " moves")
            score, move = runTree(tree, mycolor)
            treeglobal = 0
            print("I move " + move.uci() + ", a move with a score of " + str(score))
            board.push(move)
            lastmove = move
            if tempplayself: tempplayself = False
        else:
            print("Your move")
            while True:
                move = input(" > ")
                if move == "toggledebug":
                    DEBUG_TREE = not DEBUG_TREE
                    print(DEBUG_TREE)
                    continue
                if move == "youtakethis":
                    tempplayself = True
                    break
                try:
                    lastmove = board.push_uci(move)
                except ValueError:
                    print("Illegal Move")
                else:
                    break


if __name__ == '__main__': main()