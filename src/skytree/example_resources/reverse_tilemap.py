
input_file = 'demo_scr4.txt'
output_file = 'demo_scr5.txt'

with open(input_file, 'r') as infile:
    lines = infile.readlines()
    
with open(output_file, 'w') as outfile:
    for line in lines:
        outfile.write(",".join(line.rstrip().split(",")[::-1]) + '\n')

