import pandas as pd

game_data = pd.read_excel("chess_moves.xlsx")

selected_data = game_data[['move', 'fen', 'response'] ]

selected_data.to_excel("selected_chess_moves.xlsx", index=False)
