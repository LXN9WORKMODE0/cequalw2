#!/usr/bin/env python3
import sys

with open(r'C:\Users\NING\Desktop\v455\temp_compile\w2_con.csv', 'r') as f:
    lines = f.readlines()

print("代码读取顺序 vs CSV行号:")
print("=" * 60)

read_num = 0
line_idx = 0

# Lines 35-37: 3 blank reads
for i in range(3):
    read_num += 1
    content = lines[line_idx].strip()[:50] if lines[line_idx].strip() else "(blank)"
    print(f"READ #{read_num}: 跳过空白 -> CSV行{line_idx+1}: {content}")
    line_idx += 1

# Lines 38-40: DO loop reads 10 title lines
for j in range(10):
    read_num += 1
    content = lines[line_idx].strip()[:50] if lines[line_idx].strip() else "(blank)"
    print(f"  Title line {j+1}: CSV行{line_idx+1}: {content}")
    line_idx += 1

# Lines 41-42: 2 blank reads
for i in range(2):
    read_num += 1
    print(f"READ #{read_num}: 跳过 -> CSV行{line_idx+1}")
    line_idx += 1

# Line 43: NWB header
read_num += 1
print(f"READ #{read_num}: NWB -> CSV行{line_idx+1}: {lines[line_idx].strip()[:60]}")
line_idx += 1

# Lines 44-45: 2 blank reads
for i in range(2):
    read_num += 1
    print(f"READ #{read_num}: 跳过 -> CSV行{line_idx+1}")
    line_idx += 1

# Line 46: NTR header
read_num += 1
print(f"READ #{read_num}: NTR -> CSV行{line_idx+1}: {lines[line_idx].strip()[:60]}")
line_idx += 1

# Lines 47-48: 2 blank reads
for i in range(2):
    read_num += 1
    print(f"READ #{read_num}: 跳过 -> CSV行{line_idx+1}")
    line_idx += 1

# Line 49: NGC header
read_num += 1
print(f"READ #{read_num}: NGC -> CSV行{line_idx+1}: {lines[line_idx].strip()[:60]}")
line_idx += 1

# Lines 50-51: 2 blank reads
for i in range(2):
    read_num += 1
    print(f"READ #{read_num}: 跳过 -> CSV行{line_idx+1}")
    line_idx += 1

# Line 52: NOD/SELECTC data
read_num += 1
print()
print(f"*** READ #{read_num}: NOD数据 -> CSV行{line_idx+1} ***")
print(f"    内容: {lines[line_idx].strip()[:80]}")
print()
print(f"代码期望在CSV第{line_idx+1}行读取NOD数据")