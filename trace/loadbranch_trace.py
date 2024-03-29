"""Read ChampSim trace and LLC load trace simultaneously,
matching each LLC load to its location in the ChampSim
trace, to build a LLC load-branch trace where each LLC
load has features of prior branch instructions added.

We determine each LLC load's <n_branches> prior branch PCs
and taken decisions, and print this data out (-v) and/or
save it to a load-branch trace file (-o <output_trace>).

If something is off, an error is raised explaining the issue.

Need to run from above trace/ directory. If you still get an error,
try export PYTHONPATH=.
"""

import time
import argparse
import bisect
from utils.champsim_trace import get_instructions, INST_SIZE
from utils.load import get_open_function
#from tqdm import tqdm

MAX_BRANCHES_TRACKED = 10000
WRITE_INTERVAL = 1000 # Write in batches to reduce compression computations.


def parse_load_line(line):
    data = [s.replace(' ', '') for s in line.split(',')]
    uiid, cycle, src_addr, pc, cache_hit = tuple(data[:5])
    uiid = int(uiid)
    cycle = int(cycle)
    src_addr = '0x' + src_addr
    pc = '0x' + pc
    cache_hit = bool(cache_hit)
    return uiid, cycle, src_addr, pc, cache_hit


def assert_comparison(csim_inst, load_uiid, load_pc):
    assert len(csim_inst.src_mem) == 1, f'{load_uiid} matches with an instruction with 0 / 2+ load addreses {csim_inst.src_mem} : {csim_inst}'
    assert hex(csim_inst.pc) == load_pc, f'{load_uiid} pcs do not match: CS pc={hex(csim_inst.pc)}, load PC={load_pc}'


def match_traces(cf, lf, branch_hist=0, max_inst=None, verbose=False, write_f=None):
    # Both traces are sorted temporally. So, we traverse along the
    # load trace and, for each load, search in increasing order
    # for the matching load in the ChampSim trace.
    max_seen_uiid = 0
    branch_data = {}
    branch_uiids = []
    out_buffer = ''

    # Count number of lines
    nlines = 0
    for line in lf:
        nlines += 1
    lf.seek(0)

    #for line in tqdm(lf, total=nlines, unit='line', dynamic_ncols=True):
    start = time.time()
    for lnum, line in enumerate(lf):

        if lnum > 0 and lnum % 10000 == 0:
            pct = lnum / nlines
            elapsed_time = time.time() - start
            left_time = (elapsed_time / lnum * nlines) - elapsed_time # estimated time left
            print(f'{lnum} / {nlines} ({pct*100:.2f}%) ({elapsed_time / 60:.2f} min) ({left_time / 60:.2f} min est. rem.)')

        # Parse load trace line
        if line.startswith('***') or line.startswith('Read'): # For handling some invalid lines in the ML-DPC load traces
            continue
        uiid, _, src_addr, pc, _ = parse_load_line(line)

        # Return early if we exceed the maximum instruction limit
        if max_inst and uiid > max_inst:
            return

        # If this instruction is higher than the maximum seen UIID, build
        # the branch table up to this instruction's UIID.
        if uiid > max_seen_uiid:
            cf.seek(max_seen_uiid * INST_SIZE)
            for i in range(max_seen_uiid, uiid):
                inst = next(get_instructions(cf), None)
                if not inst:
                    print('ChampSim trace out of instructions. Returning.')
                    return
                if inst.is_branch: # Insert the branch into the sorted list (sorted by uiid)
                    bisect.insort(branch_uiids, i)
                    branch_data[i] = (inst.pc, inst.branch_taken)

                    # Clear old branch instructions to conserve memory
                    # (should not cause major impacts)
                    if len(branch_uiids) > MAX_BRANCHES_TRACKED:
                        remove_uiid = branch_uiids[0]
                        branch_uiids = branch_uiids[1:]
                        del branch_data[remove_uiid]

            max_seen_uiid = uiid
        #else:
        #    cf.seek((uiid - 1) * INST_SIZE)
        #    inst = next(get_instructions(cf), None)

        # Assertion checks
        #assert_comparison(inst, uiid, pc)

        if verbose:
            print(f'\n{uiid:8} Load    : pc={pc} src_mem={src_addr}')
            print(f'{uiid:8} CS      : pc={hex(inst.pc)} src_mem={hex(inst.src_mem[0])}')
            #print(f'{uiid:8} Load    : pc={bin(int(pc[2:], 16))} src_mem={bin(int(src_addr[2:], 16))}')
            #print(f'{uiid:8} CS      : pc={bin(inst.pc)} src_mem={bin(inst.src_mem[0])}')

        # Match each load to its most recent branches, and print / write results.
        if branch_hist > 0:
            idx = bisect.bisect_left(branch_uiids, uiid)
            low, high = max(0, idx - branch_hist), min(idx, len(branch_uiids))
            prior_branch_uiids = branch_uiids[low:high][::-1] # Reverse so the most recent branch appears first.

            if verbose:
                for buiid in prior_branch_uiids:
                    pc, dec = branch_data[buiid]
                    print(f'({hex(pc)}, {"T" if dec else "NT"}) ', end='')
                print()

            # Write results to a load trace augmented with the branches.
            # Row: <load data>, <branch 1 PC>, <branch 1 T/NT>, <branch 2 PC>, <branch 2 T/NT>, ...
            # Branch 1 is the most recent branch.
            # Branch <n_branches> is the least recent branch.
            # If there are less than <n_branches> prior branches, the PC/Taken will both be 0.
            if write_f:
                out_buffer += line.rstrip('\n')
                for i in range(branch_hist):
                    pc, dec = branch_data[prior_branch_uiids[i]] if i < len(prior_branch_uiids) else (0, 0)
                    out_buffer += f', {hex(pc)[2:]}, {int(dec)}'
                out_buffer += '\n'

                # Batch out output writing
                if lnum % WRITE_INTERVAL == 0:
                    print(out_buffer, end='', file=write_f)
                    out_buffer = ''

    # Write anything left over in buffer.
    print(out_buffer, end='', file=write_f)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('champsim_trace')
    parser.add_argument('load_trace')
    parser.add_argument('n_branches', type=int)
    parser.add_argument('-o', '--output-trace', type=str)
    parser.add_argument('-i', '--max-inst', default=None, type=int)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    print('Arguments:')
    print('    ChampSim trace :', args.champsim_trace)
    print('    Load trace     :', args.load_trace)
    print('    Num branches   :', args.n_branches)
    print('    Output trace   :', args.output_trace)
    print('    Max load inst. :', args.max_inst if args.max_inst else 'Full load trace')
    print('    Verbose        :', args.verbose)

    return args


if __name__ == '__main__':
    args = get_arguments()

    cs_open = get_open_function(args.champsim_trace)
    l_open = get_open_function(args.load_trace)
    o_open = get_open_function(args.output_trace) if args.output_trace else None

    if args.output_trace:
        of = o_open(args.output_trace, mode='wt', encoding='utf-8')
    else:
        of = None

    with cs_open(args.champsim_trace, mode='rb') as cf, l_open(args.load_trace, mode='rt', encoding='utf-8') as lf:
        match_traces(
            cf, lf,
            branch_hist=args.n_branches,
            max_inst=args.max_inst,
            verbose=args.verbose,
            write_f=of
        )

    if args.output_trace:
        of.close()
