"""Read ChampSim trace (compressed binary)"""
import lzma
import gzip
import argparse
#from tqdm import tqdm

try:
    from utils.champsim_trace import read_champsim_trace
except:
    import os
    os.chdir('../')
    from utils.champsim_trace import read_champsim_trace

parser = argparse.ArgumentParser()
parser.add_argument('trace')
parser.add_argument('--max-inst', default=100, type=int)
#parser.add_argument('--progress', action='store_true')
args = parser.parse_args()

if args.trace.endswith('xz'):
    with lzma.open(args.trace, mode='rt', encoding='utf-8') as f:
        data = read_champsim_trace(f, args.max_inst)
elif args.trace.endswith('gz'):
    #if args.progress:
    #    with f.open(args.trace, mode='rb') as f:
    #        g = gzip.GzipFile(fileobj=f)
    #        data = read_champsim_trace(g, args.max_inst)
    # else:
    with gzip.open(args.trace, mode='r') as f:
        data = read_champsim_trace(f, args.max_inst)
else:
    with open(args.trace) as f:
        data = read_champsim_trace(f, args.max_inst)

