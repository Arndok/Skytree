"""
A repository of file manipulation functions.

Functions:
reverse_tilemap(in_path, out_path): generate a second tilemap with horizontally reversed symbols.
bake_bordered_mass(in_path, out_path, tile_symbol, edge_borders): calculate tileset index of each tile in a bordered mass.
"""

import os
import csv
            
def reverse_tilemap(in_path, out_path=None):
    """
    Generate a second tilemap with horizontally reversed symbols using CSV.
    
    If output path is not provided, default to [in_name]_reversed.txt.
    """
    if not out_path:
        name, extension = os.path.splitext(in_path)
        out_path = name + "_reversed" + extension

    # Open input file, reverse rows and write then to output file
    with open(in_path, 'r') as infile, open(out_path, 'w', newline='') as outfile:
        csv.writer(outfile).writerows([row[::-1] for row in csv.reader(infile)])

def bake_bordered_mass(in_path, out_path=None, tile_symbol=0, edge_borders=False):
    """
    Calculate index of each tile in a tileset mass.
    
    Take an input file with a tile symbol that represents a tile that belongs
    to a bordered mass (default 0) and calculate the symbol of each of those tiles
    in function of the presence or absence of each of their 8 neighbours.
    If output path is not provided, default to [in_name]_bordered_mass_[tile_symbol].txt.
    if edge_borders is set to False, out-of-bounds positions will be treated as neighbour matches.
    
    Check terrain.png on the example_resources folder to see how the tiles should be ordered in the tileset.
    """
    if not out_path:
        name, extension = os.path.splitext(in_path)
        out_path = name + "_bordered_mass_{s}".format(s = tile_symbol) + extension

    # Read input file
    with open(in_path, 'r') as file:
        reader = csv.reader(file)
        # Read each value and convert it to int if possible
        tiles = [[int(value.strip()) if value.strip().lstrip('-').isdigit() else value for value in row] for row in reader]

    # Treat out-of-bounds positions as neighbour matches if edge_borders = True
    def get_tile(row, col):
        if 0 <= row < len(tiles) and 0 <= col < len(tiles[row]):
            return tiles[row][col]
        elif edge_borders:
            return None
        else:
            return tile_symbol
            
    out_tiles = []
    # Loop through the grid and adjust the tiles
    for row in range(len(tiles)):
        new_row = []
        for col in range(len(tiles[row])):
            if tiles[row][col] == tile_symbol:
                # Check presence of uldr neighbours
                index = (get_tile(row-1, col) == tile_symbol) * 1 + \
                        (get_tile(row, col+1) == tile_symbol) * 2 + \
                        (get_tile(row+1, col) == tile_symbol) * 4 + \
                        (get_tile(row, col-1) == tile_symbol) * 8
                # Single neighbour and sandwich cases are already dealt with
                # Corner cases
                if (index == 3 and get_tile(row-1, col+1) == tile_symbol) or \
                   (index == 6 and get_tile(row+1, col+1) == tile_symbol) or \
                   (index == 9 and get_tile(row-1, col-1) == tile_symbol) or \
                   (index == 12 and get_tile(row+1, col-1) == tile_symbol):
                    index = 15 + index // 3
                # T cases
                elif index == 7:
                    corner_mod = (get_tile(row-1, col+1) == tile_symbol) * 1 + (get_tile(row+1, col+1) == tile_symbol) * 2
                    if corner_mod > 0:
                        index = 19 + corner_mod
                elif index == 11:
                    corner_mod = (get_tile(row-1, col-1) == tile_symbol) * 1 + (get_tile(row-1, col+1) == tile_symbol) * 2
                    if corner_mod > 0:
                        index = 22 + corner_mod
                elif index == 13:
                    corner_mod = (get_tile(row-1, col-1) == tile_symbol) * 1 + (get_tile(row+1, col-1) == tile_symbol) * 2
                    if corner_mod > 0:
                        index = 25 + corner_mod
                elif index == 14:
                    corner_mod = (get_tile(row+1, col-1) == tile_symbol) * 1 + (get_tile(row+1, col+1) == tile_symbol) * 2
                    if corner_mod > 0:
                        index = 28 + corner_mod
                # Surrounded case
                elif index == 15:
                    corner_mod = (get_tile(row-1, col-1) == tile_symbol) * 1 + \
                                 (get_tile(row-1, col+1) == tile_symbol) * 2 + \
                                 (get_tile(row+1, col+1) == tile_symbol) * 4 + \
                                 (get_tile(row+1, col-1) == tile_symbol) * 8
                    if corner_mod > 0:
                        index = 31 + corner_mod

                new_row.append(str(index + tile_symbol).rjust(2))
            else:
                new_row.append(str(tiles[row][col]).rjust(2))
        out_tiles.append(new_row)
    
    # Write to output
    with open(out_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(out_tiles)
