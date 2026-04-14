import csv

# Read the file
with open('w2_con.csv', 'r') as f:
    lines = f.readlines()

# Lines 4-13 (0-indexed: 3-12) have malformed duplicate titles
# Fix them by keeping only the first quoted string
fixed_lines = []
for i, line in enumerate(lines):
    if i in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:  # TITLE lines
        # Find the first quoted string and truncate after it
        in_quote = False
        quote_end = -1
        for j, c in enumerate(line):
            if c == '"':
                if not in_quote:
                    in_quote = True
                    quote_start = j
                else:
                    # End of quoted string
                    quote_end = j + 1
                    break
        if quote_end > 0:
            # Take everything up to and including the first quoted string
            fixed_line = line[:quote_end]
            # Find the next comma and end there for proper CSV format
            rest = line[quote_end:]
            next_comma = rest.find(',')
            if next_comma >= 0:
                fixed_line = fixed_line + rest[next_comma:]
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

with open('w2_con_fixed.csv', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed CSV written to w2_con_fixed.csv")
