"""
A repository of file manipulation functions.

Functions:
reverse_tilemap(in_path, out_path): generate a second tilemap with horizontally reversed symbols.
"""

def reverse_tilemap(in_path, out_path=None):
    """
    Generate a second tilemap with horizontally reversed symbols.
    
    If output path is not provided, default to [in_name]_reversed.txt.
    """
    if not out_path:
        out_path = in_path[:-4] + "_reversed.txt"

    with open(in_path, 'r') as infile:
        lines = infile.readlines()
        
    with open(out_path, 'w') as outfile:
        for line in lines:
            outfile.write(",".join(line.rstrip().split(",")[::-1]) + '\n')

