import random
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import os
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

import chess
import chess.svg
from time import sleep
import random
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QApplication, QWidget

import pandas as pd
import os
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from stockfish import Stockfish

import numpy as np
import tensorflow as tf
import chess
import chess.engine #to use stockfish evaluation
from stockfish import Stockfish



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(80, 80, 880, 880)

        self.widgetSvg = QSvgWidget(parent=self)
        self.widgetSvg.setGeometry(8, 8, 800, 800)

        self.chessboard = chess.Board()

        self.chessboardSvg = chess.svg.board(self.chessboard).encode("UTF-8")
        self.widgetSvg.load(self.chessboardSvg)
        
        

def AI_BOT(model, legal_features, legal_y, board):
        bot_move = PEPE_AI_v2(model, legal_features, legal_y, board)
        if bot_move == '':
            return bot_move, board
        if not pawn_promotion(board, bot_move):
            board.push_san(bot_move)
        else:
            board.push_san(bot_move +'q')
        chessboardSvg = chess.svg.board(board,flipped=True).encode("UTF-8")
        window.widgetSvg.load(chessboardSvg)
        app.processEvents()
        
        return bot_move

def USER_MOVE(board):
        if board.is_checkmate():
            # Determine the winner based on the last move played
            last_move = board.peek()  # Get the last move without modifying the board
            winner = "White" if board.turn == chess.BLACK else "Black"
            print("Winner:", winner)
            
            player_move = '' #just to output same thing
            return player_move, winner
        else: #if not checkmate
            legal_moves = [move.uci() for move in board.legal_moves]
            while True:
                try:
                    player_move = input("Your move:")  
                    #if not pawn promotion
                    if not pawn_promotion(board, player_move):
                        board.push_san(player_move)
                    else:
                        #user chooses promotion piece
                        promotion_piece = input("Piece to promote to (q, r, k, b):")
                        board.push_san(player_move + promotion_piece)
                    break
                except ValueError or player_move not in legal_moves:
                    print("Illegal move. Try again.")
        
# =============================================================================
#         Display Board
# =============================================================================
            
            chessboardSvg = chess.svg.board(board,flipped=True).encode("UTF-8")
            window.widgetSvg.load(chessboardSvg)
            window.show()
            app.processEvents()
            sleep(2)

        return player_move, board
    
def pawn_promotion(board, move):
    
    print(move)
    #get piece type from location
    square = chess.parse_square(move[:2])
    piece = board.piece_at(square)
    if len(move) != 4 or type(piece) is type(None):  # If not a valid move
        print("Invalid move:", move)
        return False

    else:      
        start_rank = int(move[1])
        end_rank = int(move[3])
        if piece.piece_type == chess.PAWN and ((start_rank == 2 and end_rank == 1) or (start_rank == 7 and end_rank == 8)):
            promotion = True
        else:
            promotion = False
        
    return promotion
# =============================================================================
# given array with multiple FEN object, turn it into array of numbers suitable for model.fit
# =============================================================================
def FEN2ARRAY(fen_array):
    # Create a mapping of piece characters to numeric values
    piece_mapping = {'p': -1, 'n': -2, 'b': -3, 'r': -4, 'q': -5, 'k': -6,
                     'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6, '.': 0}
    
    if isinstance(fen_array, str):
        fen_array = [fen_array]  # Convert single FEN string to a list
        
    feature_matrices = []
    
    for fen in fen_array:
        board = chess.Board(fen)
        feature_matrix = np.zeros((8, 8), dtype=int)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                piece_value = piece_mapping[piece.symbol()]
                rank = chess.square_rank(square)
                file = chess.square_file(square)
                feature_matrix[rank][file] = piece_value
        
        feature_matrices.append(feature_matrix)
    
    features = np.concatenate(feature_matrices, axis=0)
    return features.reshape(len(fen_array), -1)

# =============================================================================
# TRAIN MODEL WITH DATA
# =============================================================================
def PEPE_AI_Train(X, y, board):
    #X: array of FEN representation of board states for all games
    #y: moves(i) played after position X(i) has been reached
    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    features = FEN2ARRAY(X_train) #all moves
    #features_test = FEN2ARRAY(X_test) #all moves
    
    # Create the machine learning model
    model = RandomForestClassifier(n_estimators=1000)
    
    # Select a subset of training samples
    n_samples=1000
    subset_features = features[:n_samples]
    subset_labels = y_train[:n_samples]
    
    #set legal moves
    legal_moves = [move.uci() for move in board.legal_moves]
    indices_to_keep = [i for i, move in enumerate(y_train) if move in legal_moves]
    legal_y = [move for move in y_train if move in legal_moves] #target variable (to predict)
    X_train2 = [other_element for i, other_element in enumerate(X_train) if i in indices_to_keep]
    legal_features = FEN2ARRAY(X_train2) #all legal moves from training data
    
    # Train the model on current legal moves:
    model.fit(legal_features, legal_y)
    
    return model, legal_features, legal_y

# =============================================================================
#PEPE AI (version 2)

#It plays exclusively with data moves,
#but if stockfish detects that move is a bad blunder,
#it plays best_move 90% of the times

# =============================================================================  
def PEPE_AI_v2(model, X, y, board):
        #if board is in initial state, bot is white and is opening the game:
        if board.fen() == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1':
            first_move = 'e2e4'
            print(first_move)
            return first_move
        else:
            #Make prediction on input board:
            board_features = FEN2ARRAY(board.fen())
            y_pred = model.predict(board_features)
            print("Move from Data: ", y_pred)
            
            #if predicted move is not legal, re-run data-based AI to train based on new legal_moves
            legal_moves = [move.uci() for move in board.legal_moves]
            if y_pred[0] not in legal_moves:
                print("Setting new legal moves, please wait...")
                model, legal_features, legal_y = PEPE_AI_Train(X, y, board)
                #Make new prediction:
                board_features = FEN2ARRAY(board.fen())
                y_pred = model.predict(board_features)
                print("Move from Data: ", y_pred)
                
            #stockfish evaluates AI classifier move choice
            board2 = board.copy()
            #get evaluation before and after to check if blunder:
            evaluation_before, engine_move = StockFish(board)
            print("Evaluation before: " , evaluation_before)
            print(type(evaluation_before) == type(None))
            if type(evaluation_before) == type(None):
                evaluation_before = 0
                print('evaluation before set to 0')
            #push candidate move
            board2.push_san(y_pred[0])
            evaluation_after, engine_move2 = StockFish(board2) #gets evaluation from opponent's perspective
            
            print(type(evaluation_after) == type(None))
            if type(evaluation_after) == type(None):
                evaluation_after = 0
                print('evaluation after set to 0')
            #print("Evaluation after: " , evaluation_after)
            evaluation_after = -1*evaluation_after
            
            
            dif_eval = abs(evaluation_before - evaluation_after)
            rand_nr = random.uniform(0,1) #even if blunder, give small probability to not seeing it
            
            #NOTE:
                #Evaluation is given by the turn
                #this means that evaluation before will be set for the bot pieces
                #evaluation after will be set for opponent pieces
                #e.g. if evaluation before < 0, bot is losing
                #if evaluation after > 0, opponent is winning
                # to get bot evaluation "after", need to negate the opponent evaluation
            
            print('Chosen move:')
            if dif_eval > 200 and evaluation_before > evaluation_after: #if blunder
                if rand_nr > 0.1: #if bot saw blunder
                    bot_move = engine_move #correct with engine move
                    print("Best move, ", bot_move)
                else: #bot didn't notice blunder 
                    bot_move = y_pred[0] #play blunder anyway
                    print("Move from Data: ",bot_move)
                    print("Blunder played anyway. Prob(not seeing) = ", rand_nr)
            else: #not a blunder, can play data move
                bot_move = y_pred[0] #play blunder anyway
                print("Move from Data, ",bot_move)
            
        return bot_move 

def StockFish(board):
    stockfishpath = r"C:\Users\Pranav\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
    with chess.engine.SimpleEngine.popen_uci(stockfishpath) as engine:
        result = engine.analyse(board, chess.engine.Limit(time=2.0))
        
        #get best move 
        stockfish=Stockfish(stockfishpath)
        stockfish.set_fen_position(board.fen())
        suggested_move = stockfish.get_best_move()
        #print(result)
        evaluation = result["score"]
        #print(evaluation)
        numeric_part = evaluation.relative.score() #if > 0, white's better.
        if type(numeric_part) == type(None):
                numeric_part = 0
                
        return numeric_part, suggested_move

# =============================================================================
#  Evaluation by Stockfish example:
# "PovScore": "Pov" stands for "Point of View," indicating that the evaluation is given from the perspective of the side to move.
# "Cp(+31)": "Cp" stands for centipawns, which is a unit used to measure the advantage or disadvantage in chess. A positive value (+31 in this case) indicates an advantage for the side to move, while a negative value would represent an advantage for the opponent.
# "WHITE": Indicates that the evaluation is given from the perspective of the white side.
# 
# =============================================================================

# =============================================================================
# DATA
# =============================================================================
game_data = pd.read_excel(r'C:\Users\Pranav\Desktop\chess_bot\ballloverpgo_white_V2.xlsx')
# Extract the FEN notation and move columns
moves = game_data['move'].values
X = game_data['fen'].values
y = game_data['response'].values

# =============================================================================
# START GAME
# =============================================================================

if __name__ == "__main__":
    app = QApplication([])

    #set up board
    board = chess.Board()
    #print(board)
    i=0
    #initialize 0th move for bot
    #IF BOT is White, set this to empty, otherwise no need to define

    player_move = ''
    bot_move = 'not empty'
    window = MainWindow()
    
    chessboardSvg = chess.svg.board(board, flipped=True).encode("UTF-8")
    window.widgetSvg.load(chessboardSvg)
    window.show()
    app.processEvents()
    
    #Train AI based on data:
    model, legal_features, legal_y = PEPE_AI_Train(X, y, board)
    
    while not ValueError or player_move == '' or bot_move != '':
        i=i+1
        print("Turn number " + str(i))
        # =============================================================================
        #  WHITE MOVES
        # =============================================================================
        #flip the board for white
            
        #bot_move = BOT_MOVE(df, board, player_move)
        bot_move = AI_BOT(model, X, y, board)
        
        # =============================================================================
        #  BLACK MOVES
        # =============================================================================

        player_move, board = USER_MOVE(board)
        
    #app.exec()
    app.quit()








