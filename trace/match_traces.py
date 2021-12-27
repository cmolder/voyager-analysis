"""Read ChampSim trace and load trace simultaneously,
trying to match LLC loads to their locations in
the ChampSim trace. If something is off, an
error is raised explaining the issue.

Need to run from above corr/ directory. If you still get an error,
try export PYTHONPATH=.
"""

import lzma
import gzip
import argparse
from utils.champsim_trace import get_instructions, INST_SIZE


def parse_load_line(line):
    uiid, cycle, src_addr, pc, cache_hit = tuple(s.replace(' ', '') for s in line.split(','))
    uiid = int(uiid)
    cycle = int(cycle)
    src_addr = '0x' + src_addr
    pc = '0x' + pc
    cache_hit = bool(cache_hit)
    return uiid, cycle, src_addr, pc, cache_hit


def match_traces(cf, lf):
    # Both traces are sorted temporally. So, we traverse along the
    # load trace and, for each load, search in increasing order
    # for the matching load in the ChampSim trace.
    prev_uiid = 0
    src_mapping = {}

    for line in lf:
        # For handling some invalid lines in the ML-DPC load traces
        if line.startswith('***') or line.startswith('Read'):
            continue
        uiid, _, src_addr, pc, _ = parse_load_line(line)

        if uiid > prev_uiid:
            for i in range(prev_uiid, uiid):
                inst = next(get_instructions(cf), None)
        else:
            cf.seek((uiid - 1) * INST_SIZE)
            inst = next(get_instructions(cf), None)

        prev_uiid = uiid

        if not inst:
            print('Done matching traces. Everything checks out.')
            return

        # Assertion checks
        assert len(inst.src_mem) == 1, f'{uiid} matches with instruction with 0 / 2+ load addreses {inst.src_mem} : {inst}'
        assert hex(inst.pc) == pc, f'{uiid} pcs do not match: CS pc={hex(inst.pc)}, load PC={pc}'
        if src_addr in src_mapping:
            assert src_mapping[src_addr] == inst.src_mem, '{uiid} mapping between addresses is not one-to-one: Load {src_addr}, CS {hex(inst.pc)} vs. {hex(src_mapping[src_addr])}'
        src_mapping[src_addr] = inst.src_mem

        print()
        print(f'{uiid:8} Load: pc={pc} src_mem={src_addr}')
        print(f'{uiid:8} CS  : pc={hex(inst.pc)} src_mem={hex(inst.src_mem[0])}')
        #print(f'{uiid:8} Load: pc={bin(int(pc[2:], 16))} src_mem={bin(int(src_addr[2:], 16))}')
        #print(f'{uiid:8} CS  : pc={bin(inst.pc)} src_mem={bin(inst.src_mem[0])}')


"""Driver (and helper) functions"""
def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('champsim_trace')
    parser.add_argument('load_trace')
    args = parser.parse_args()

    print('Arguments:')
    print('    ChampSim trace :', args.champsim_trace)
    print('    Load trace     :', args.load_trace)

    return args


if __name__ == '__main__':
    args = get_argument_parser()
    if args.champsim_trace.endswith('xz'):
        cs_open = lzma.open
    elif args.champsim_trace.endswith('gz'):
        cs_open = gzip.open
    else:
        cs_open = open

    if args.load_trace.endswith('xz'):
        l_open = lzma.open
    elif args.load_trace.endswith('gz'):
        l_open = gzip.open
    else:
        l_open = open

    with cs_open(args.champsim_trace, mode='rb') as cf, l_open(args.load_trace, mode='rt', encoding='utf-8') as lf:
        match_traces(cf, lf)


