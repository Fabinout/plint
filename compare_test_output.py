import sys

file0 = sys.argv[1]
file1 = sys.argv[2]

with open(file0) as f:
    content0 = f.read()

with open(file1) as f:
    content1 = f.read()

print(int(sorted(content0) == sorted(content1)))
