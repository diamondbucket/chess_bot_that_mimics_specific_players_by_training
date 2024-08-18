from converter.pgn_data import PGNData
import pandas as pd

# pgn_data = PGNData(r"C:\Users\Pranav\Downloads\ballloverpgo-white.pgn")
# pgn_data.export()

chess_excel_data = pd.read_csv('ballloverpgo-white_moves.csv')
GFG = pd.ExcelWriter("chess_moves.xlsx", engine='openpyxl')
chess_excel_data.to_excel(GFG, index=False)
GFG.close()
