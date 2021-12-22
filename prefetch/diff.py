import sys
start = int(sys.argv[3]) * 1000 * 1000
import lzma

if len(sys.argv) > 4 and sys.argv[4] == 'trace':
    split = ', '
else:
    split = ' '

if sys.argv[1].endswith('xz'):
    with lzma.open(sys.argv[1], mode='rt', encoding='utf-8') as f1:
        d1 = {line.strip().split(split)[0]: line.strip().split(split)[2] for line in f1}
else:
    with open(sys.argv[1]) as f1:
        d1 = {line.strip().split(split)[0]: line.strip().split(split)[1] for line in f1}
if sys.argv[2].endswith('xz'):
    with lzma.open(sys.argv[2], mode='rt', encoding='utf-8') as f2:
        d2 = {line.strip().split(split)[0]: line.strip().split(split)[2] for line in f2}
else:
    with open(sys.argv[2]) as f2:
        d2 = {line.strip().split(split)[0]: line.strip().split(split)[1] for line in f2}

diffs = 0
total_keys = 0
diff1 = 0
diff2 = 0
diff12 = 0
for k1 in d1:
    if int(k1) < start:
        continue
    if k1 not in d2:
        diffs += 1
        total_keys += 1
        diff1 += 1
    elif d1[k1] != d2[k1]:
        diffs += 1
        total_keys += 1
        diff12 += 1
    else:
        total_keys += 1
for k2 in d2:
    if int(k2) < start:
        continue
    if k2 not in d1:
        diffs += 1
        total_keys += 1
        diff2 += 1
print(diffs / total_keys, diff1 / total_keys, diff2 / total_keys, diff12 / total_keys, diffs, diff1, diff2, diff12, total_keys)
