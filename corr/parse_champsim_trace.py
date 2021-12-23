"""Read ChampSim trace (compressed binary)

Need to run from above corr/ directory. If you still get an error,
try export PYTHONPATH=."""
import lzma
import gzip
import argparse
from utils.champsim_trace import read_champsim_trace

parser = argparse.ArgumentParser()
parser.add_argument('trace')
parser.add_argument('--max-inst', default=100, type=int)
#parser.add_argument('--progress', action='store_true')
args = parser.parse_args()

if args.trace.endswith('xz'):
    with lzma.open(args.trace, mode='rb') as f:
        read_champsim_trace(f, args.max_inst)
elif args.trace.endswith('gz'):
    with gzip.open(args.trace, mode='rb') as f:
        read_champsim_trace(f, args.max_inst)
else:
    with open(args.trace, mode='rb') as f:
        read_champsim_trace(f, args.max_inst)

