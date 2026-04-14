with open('w2_con.csv', 'r') as f:
    lines = f.readlines()

fixed = []
for i, line in enumerate(lines):
    if 3 <= i <= 12:
        # Extract first quoted string
        start = line.find('"')
        if start >= 0:
            end = line.find('"', start + 1)
            if end > start:
                first_quoted = line[start:end+1]
                # Create a simple line with just the quoted string
                fixed_line = first_quoted + '\n'
                fixed.append(fixed_line)
                continue
    fixed.append(line)

with open('w2_con_simple.csv', 'w') as f:
    f.writelines(fixed)

print("Done")
