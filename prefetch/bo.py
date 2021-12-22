
import argparse
import lzma
from collections import deque

def process_line(line):
    # File format for ML Prefetching Competition
    # See github.com/Quangmire/ChampSim
    # Uniq Instr ID, Cycle Count,   Load Address,      PC of Load,        LLC Hit or Miss
    # int(split[0]), int(split[1]), int(split[2], 16), int(split[3], 16), split[4] == '1'

    # Return Inst ID, PC, and Load Address
    split = line.strip().split(', ')
    return (int(split[0]), int(split[3], 16), int(split[2], 16))


OFFSETS = [
    1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 7, -7, 8, -8, 9, -9, 
    10, -10, 11, -11, 12, -12, 13, -13, 14, -14, 15, -15, 16, -16, 
    18, -18, 20, -20, 24, -24, 30, -30, 32, -32, 36, -36, 40,-40
]
SCORE_MAX = 31
ROUND_MAX = 100
BAD_SCORE = 10
LOW_SCORE = 20
DQSIZE = 15  # Delay queue size 
RRSIZE = 128 # Recent request table size - Emulating 2 banks, 64 entries per bank.

# Data structures
dq = deque([]) # Delay queue (stalls entries to RR queue)
rr = deque([]) # Recent requests (RR) table (implemented as LRU queue)
D = 0   # Best offset (0 = no prefetch)

# Learning phase data
off_idx = 0 
n_rounds = 0
scores = {o: 0 for o in OFFSETS}

def update_prefetcher(addrB):
    """Perform learning phase iteratively."""
    global off_idx
    global D
    global n_rounds
    global scores
    
    di = OFFSETS[off_idx]
    if addrB - di in rr:
        scores[di] += 1
    
    # Use the next offset in the list next time.
    off_idx += 1
    
    # End of round - reset offset index and
    # loop through the offsets again.
    if off_idx == len(OFFSETS):
        n_rounds += 1
        off_idx = 0
        
        # If this is the last round of the learning phase - set best offset
        # and clear tables. Then, start the learning process over.
        best_score, best_off = max([(s, o) for o, s in scores.items()])
        if best_score >= SCORE_MAX or n_rounds >= ROUND_MAX:
            D = best_off if best_score > BAD_SCORE else 0 # Choose best offset
            scores = {o: 0 for o in OFFSETS} # Reset training data
            n_rounds = 0
            
            
def update_tables(addrB):
    """Update RR and delay queue tables given the base address.
    
    Recent addresses:
        1. Move it to the tail of the rr table. (so it doesn't get evicted)
    
    New / non-recent addresses:
        1. Add it to the delay queue.
        2. If (1) makes the delay queue full,
           take a delayed address and put it in the rr table.
        3. If (2) makes the rr table full, 
           evict the least-recently used address in the rr table.
    """
    if addrB in rr:
        rr.remove(addrB)
        rr.append(addrB)
    
    else:
        dq.append(addrB) 
        if len(dq) > DQSIZE:
            rr.append(dq.popleft())
        if len(rr) > RRSIZE:
            rr.popleft()


def read_file(f, start, stop_train):
    data = []
    for i, line in enumerate(f):
        # Necessary for some extraneous lines in MLPrefetchingCompetition traces
        if line.startswith('***') or line.startswith('Read'):
            continue
        if 'Warmup' in line or 'Heartbeat' in line:
            continue
        if len(line.strip()) == 0:
            continue
        inst_id, pc, addr = process_line(line)
        if inst_id < start * 1000 * 1000:
            continue
        addrB = addr >> 6;
        if inst_id < stop_train * 1000 * 1000:
            # TODO : Only update tables / prefetcher on misses or prefetched hits.
            update_tables(addrB)
            update_prefetcher(addrB)
        if D != 0:
            data.append('{} {}'.format(inst_id, hex((addrB << 6) + D)))
            

    return data

parser = argparse.ArgumentParser()
parser.add_argument('load_trace')
parser.add_argument('pc_load_trace')
parser.add_argument('--start', type=int, default=0)
parser.add_argument('--stop-train', type=int, default=500)
args = parser.parse_args()

if args.load_trace.endswith('xz'):
    with lzma.open(args.load_trace, mode='rt', encoding='utf-8') as f:
        data = read_file(f, args.start, args.stop_train)
else:
    with open(args.load_trace) as f:
        data = read_file(f, args.start, args.stop_train)

with open(args.pc_load_trace, 'w') as f:
    for line in data:
        print(line, file=f)
'''
with open(args.pc_load_trace, 'w') as f:
    for line in data[-args.length:]:
        print(line, file=f)
'''
