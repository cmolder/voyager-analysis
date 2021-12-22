
import argparse
import lzma

def process_line(line):
    # File format for ML Prefetching Competition
    # See github.com/Quangmire/ChampSim
    # Uniq Instr ID, Cycle Count,   Load Address,      PC of Load,        LLC Hit or Miss
    # int(split[0]), int(split[1]), int(split[2], 16), int(split[3], 16), split[4] == '1'

    # Return Inst ID, PC, and Load Address
    split = line.strip().split(', ')
    return (int(split[0]), int(split[3], 16), int(split[2], 16))

tu = {}
cache = {}

def read_file(f):
    data = []
    for i, line in enumerate(f):
        # Necessary for some extraneous lines in MLPrefetchingCompetition traces
        if line.startswith('***') or line.startswith('Read'):
            continue
        if 'Warmup' in line or 'Heartbeat' in line:
            continue
        if len(line.strip()) == 0:
            continue
        try:
            inst_id, pc, addr = process_line(line)
        except:
            print(line)
        addrB = addr >> 6;
        if pc in tu:
            prev_addr = tu[pc]
            cache[(pc, prev_addr)] = addrB
        tu[pc] = addrB
        if (pc, addrB) in cache:
            data.append('{} {}'.format(inst_id, hex(cache[(pc, addrB)] << 6)))

    return data

parser = argparse.ArgumentParser()
parser.add_argument('load_trace')
parser.add_argument('pc_load_trace')
#parser.add_argument('length', type=int)
args = parser.parse_args()

if args.load_trace.endswith('xz'):
    with lzma.open(args.load_trace, mode='rt', encoding='utf-8') as f:
        data = read_file(f)
else:
    with open(args.load_trace) as f:
        data = read_file(f)

with open(args.pc_load_trace, 'w') as f:
    for line in data:
        print(line, file=f)
'''
with open(args.pc_load_trace, 'w') as f:
    for line in data[-args.length:]:
        print(line, file=f)
'''
