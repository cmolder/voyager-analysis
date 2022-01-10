"""Compute correlation between access history and next prefetch,
using load-branch traces.

Need to run from above corr/ directory. If you still get an error,
try export PYTHONPATH=.
"""

import argparse
import time
from utils.load import get_open_function
from utils.load_trace import get_instructions
from utils.logging import log_progress


def gather_correlation_data(f, cd, pcd=None):
    """Wrapper function to gather correlation data
    from each address in the load trace."""

    # Count number of lines
    nlines = 0
    for _ in f:
        nlines += 1
    f.seek(0)

    start_time = time.time()
    for lnum, inst in enumerate(get_instructions(f)):
        
        # Periodically log progress
        log_progress(lnum, nlines, start_time, interval=50000)
        
        # Add load to correlation tracker
        addr, brs = inst.addr, inst.branches
        cd.add_addr(addr, brs)   
        if pcd:
            pcd.add_addr(addr, brs)
        
    # Print time to run
    print('Time to run:', (time.time() - start_time) / 60, 'min')


class CorrelationData(object):
    """Track correlation between address histories (triggers) and the next prefetch address.

    depth            : how many prefetches to look ahead
        - e.g. 1 = next prefetch, 2 = the second prefetch ahead, etc.
    max_hist_len     : number of prior global load addresses to consider as part of the trigger.
        - Track all load address triggers of length 1 to max_hist_len (inclusive)
    max_branch_len   : number of prior branches to track as part of the trigger.
        - Track all branch triggers of length 1 to max_branch_len (inclusive)
    shift            : number of bits to cut-off for tracking load addresses.
        - 0 : cache line temporal correlation
        - 6 : page temporal correlation
    """
    def __init__(self, depth, max_hist_len, 
                 max_branch_len=0, shift=0,
                 skip_branch_dec=False,
                 skip_branch_pc=False):
        self.depth = depth
        self.hist = []
        # We're considering the correlation for:
        # - load address triggers of length 1 to max_hist_len (inclusive), with
        # - branch triggers of length 0 (i.e. just loads) to max_branch_len (inclusive)
        #    - each trigger contains branch pc, branch decision, or both (all combinations checked) 
        
        self.max_hist_len = max_hist_len
        self.max_branch_len = max_branch_len
        self.shift = shift
        
        branch_types = []
        if self.max_branch_len > 0:
            assert not (skip_branch_dec and skip_branch_pc), 'Must track branch dec or PC for branches.'
        
        if not skip_branch_dec:
            branch_types.append('dec')
        if not skip_branch_pc:
            branch_types.append('pc')
        if not (skip_branch_dec or skip_branch_pc):
            branch_types.append('pcdec')
        
        self.data = {
            (i, j, k): {}
            for i in range(1, max_hist_len + 1)
            for j in range(0, max_branch_len + 1)
            for k in branch_types
        }
        
    
    def _is_load_history_full(self):
        return len(self.hist) == self.max_hist_len + self.depth - 1
    
    
    def _trim_load_history(self):
        if len(self.hist) > self.max_hist_len + self.depth - 1:
            self.hist = self.hist[1:]
    

    def add_addr(self, addr, branches):
        # Only take some bits of the full address
        addr_tag = self.addr_tag(addr)

        if self._is_load_history_full():
            # For every history length, keep track of how many times addr_tag shows up
            # given the history
            for trigger in self.data:
                hist_len, branch_len, branch_type = trigger # trigger type
                # tag is the trigger
                load_tag = self.hist[(self.max_hist_len - hist_len) : self.max_hist_len]
                branch_tag = []
                if branch_type in ['pc', 'pcdec']:
                    branch_tag.extend([b[0] for b in branches[:branch_len]])
                if branch_type in ['dec', 'pcdec']:
                     branch_tag.extend([int(b[1]) for b in branches[:branch_len]])
                
                tag = tuple([*load_tag, *branch_tag])

                if tag not in self.data[trigger]:
                    self.data[trigger][tag] = {}

                # Add the current address
                if addr_tag not in self.data[trigger][tag]:
                    self.data[trigger][tag][addr_tag] = 0

                self.data[trigger][tag][addr_tag] += 1

        
        self.hist.append(addr_tag) # Update history with addr_tag
        self._trim_load_history() # Trim load history to keep only most recent loads.
            

            
    def addr_tag(self, addr):
        return addr >> (self.shift + 6)

    
    def compute_freqs(self, weighted=False):
        freqs = {}
        for trigger in self.data: # trigger type = (hist_len, branch_len, branch_type)
            freqs[trigger] = {}

            for tag in self.data[trigger]:
                # # of unique correlated addresses
                num_unique_correlated_addrs = len(self.data[trigger][tag])
                if num_unique_correlated_addrs not in freqs[trigger]:
                    freqs[trigger][num_unique_correlated_addrs] = 0

                # If we want the frequency to be weighted by # of addresses for this
                # history trigger
                if weighted:
                    freqs[trigger][num_unique_correlated_addrs] += sum(self.data[trigger][tag].values())
                else:
                    freqs[trigger][num_unique_correlated_addrs] += 1

        return freqs


def print_freqs(freqs, suffix=''):
    for trigger in freqs:
        hist_len, branch_len, branch_type = trigger
        if branch_len > 0:
            print(f'{hist_len} {suffix} (With {branch_len} {branch_type} Prior Branches)')
        else:
            print(f'{hist_len} {suffix}')
            
        print({k: freqs[trigger][k] for k in sorted(freqs[trigger])})


def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('load_trace')
    parser.add_argument('-d', '--depth', type=int, default=1)
    parser.add_argument('-l', '--max-hist-len', type=int, default=4)
    parser.add_argument('-b', '--max-branch-len', type=int, default=0)
    args = parser.parse_args()

    print('Arguments:')
    print('    Load trace     :', args.load_trace)
    print('    Depth          :', args.depth)
    print('    Max history len:', args.max_hist_len)
    print('    Max branch len :', args.max_branch_len)
    return args


def compute_correlation(load_trace, depth, max_hist_len, max_branch_len):
    """Main temporal correlation computation"""
    correlation_data = CorrelationData(
        depth, max_hist_len,
        max_branch_len=max_branch_len
    )
    # page_correlation_data = CorrelationData(
    #     depth, max_hist_len, 
    #     max_branch_len=max_branch_len,
    #     shift=6
    # )
    
    l_open = get_open_function(load_trace)
    with l_open(load_trace, mode='rt', encoding='utf-8') as f:
        gather_correlation_data(f, correlation_data)#, page_correlation_data)

    #print_freqs(correlation_data.compute_freqs(), 'Cache Lines')
    #print_freqs(page_correlation_data.compute_freqs(), 'Pages')
    print_freqs(correlation_data.compute_freqs(weighted=True), 'Weighted Cache Lines')
    #print_freqs(page_correlation_data.compute_freqs(weighted=True), 'Weighted Pages')


if __name__ == '__main__':
    args = get_argument_parser()
    compute_correlation(
        args.load_trace, args.depth, 
        args.max_hist_len,
        args.max_branch_len
    )
