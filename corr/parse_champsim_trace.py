"""Read ChampSim trace (compressed binary)"""
import lzma
import gzip
import argparse

try:
    from utils.champsim_trace import read_champsim_trace
except:
    import os
    os.chdir('../')
    from utils.champsim_trace import read_champsim_trace

parser = argparse.ArgumentParser()
parser.add_argument('trace')
parser.add_argument('--max-inst', default=100, type=int)
args = parser.parse_args()

if args.trace.endswith('xz'):
    with lzma.open(args.trace, mode='rt', encoding='utf-8') as f:
        data = read_champsim_trace(f, args.max_inst)
elif args.trace.endswith('gz'):
    with gzip.open(args.trace, mode='r') as f:
        data = read_champsim_trace(f, args.max_inst)
else:
    with open(args.trace) as f:
        data = read_champsim_trace(f, args.max_inst)

