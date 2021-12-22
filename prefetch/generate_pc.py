#!/bin/python
import argparse
import lzma

def process_line(line):
    # File format for ML Prefetching Competition
    # See github.com/Quangmire/ChampSim
    # Uniq Instr ID, Cycle Count,   Load Address,      PC of Load,        LLC Hit or Miss
    # int(split[0]), int(split[1]), int(split[2], 16), int(split[3], 16), split[4] == '1'

    # Return Inst ID, PC, and Load Address
    split = line.strip().split(', ')
    if len(split) == 3:
        return (int(split[0]), int(split[2], 16), int(split[1], 16))
    else:
        return (int(split[0]), int(split[3], 16), int(split[2], 16))

def read_file(f, start):
    pc_data = {}
    data = []
    for i, line in enumerate(f):
        # Necessary for some extraneous lines in MLPrefetchingCompetition traces
        if line.startswith('***') or line.startswith('Read'):
            continue
        inst_id, pc, addr = process_line(line)
        if pc not in pc_data:
            pc_data[pc] = []
        if len(pc_data[pc]) > 0 and pc_data[pc][-1][0] >= start * 1000 * 1000:
            data.append('{} {}'.format(pc_data[pc][-1][0], hex((addr >> 6) << 6)))
        pc_data[pc].append((inst_id, hex((addr >> 6) << 6)))

    return data

parser = argparse.ArgumentParser()
parser.add_argument('load_trace')
parser.add_argument('pc_load_trace')
parser.add_argument('start', type=int)
args = parser.parse_args()

if args.load_trace.endswith('xz'):
    with lzma.open(args.load_trace, mode='rt', encoding='utf-8') as f:
        data = read_file(f, args.start)
else:
    with open(args.load_trace) as f:
        data = read_file(f, args.start)

with open(args.pc_load_trace, 'w') as f:
    for line in data:
        print(line, file=f)
