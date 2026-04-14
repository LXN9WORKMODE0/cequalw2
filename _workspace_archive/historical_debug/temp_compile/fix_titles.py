# Read the CSV
with open('w2_con.csv', 'r') as f:
    lines = f.readlines()

fixed = []
for i, line in enumerate(lines):
    # Lines 4-13 (0-indexed: 3-12) are TITLE lines
    if 3 <= i <= 12:
        # Extract first quoted string
        start = line.find('"')
        if start >= 0:
            end = line.find('"', start + 1)
            if end > start:
                first_quoted = line[start:end+1]
                # Check if this is an escaped quote situation
                # Pattern: "text"",,,,,... or """,,,,,...
                if end + 1 < len(line) and line[end+1] == '"':
                    # This is an escaped quote - the string ends with a quote
                    # So first_quoted already has the correct content
                    pass
                # Now check if there's a second quoted string after the commas
                rest = line[end+1:]
                # Skip commas to find next quote
                next_quote = rest.find('"')
                if next_quote >= 0:
                    # There's a second quoted string - skip it
                    # Find where it ends
                    next_end = rest.find('"', next_quote + 1)
                    if next_end > next_quote:
                        # Truncate after first quoted string + comma
                        fixed_line = first_quoted + ',\n'
                        fixed.append(fixed_line)
                        continue
        fixed.append(line)
    else:
        fixed.append(line)

with open('w2_con_fixed.csv', 'w') as f:
    f.writelines(fixed)

print("Fixed")
# Show lines 10-15 of fixed file
with open('w2_con_fixed.csv', 'r') as f:
    lines = f.readlines()
for i, l in enumerate(lines[9:15], start=10):
    print(f"Line {i}: {l[:80]}...")
