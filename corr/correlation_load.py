"""Compute correlation between access history and next prefetch,
using load(-branch) traces.

TODO: Implement branch history (if looking at a load-branch trace.)

Need to run from above corr/ directory. If you still get an error,
try export PYTHONPATH=.
"""

import argparse
import time
from tqdm import tqdm
from utils.load import get_open_function
from utils.load_trace import get_instructions


def gather_correlation_data(f, cd, pcd):
    """Wrapper function to gather correlation data
    from each address in the load trace."""

    # Count number of lines
    nlines = 0
    for _ in f:
        nlines += 1
    f.seek(0)

    #for addr in read_file(f):
    for inst in tqdm(get_instructions(f), total=nlines, unit='line', dynamic_ncols=True):
        addr = inst.addr
        cd.add_addr(addr)
        pcd.add_addr(addr)


class CorrelationData(object):
    """Track correlation between address histories (triggers) and the next prefetch address.

    depth : ?
    max_hist_len     : number of prior PC-localized load addresses to consider as part of the trigger.
        - Track all triggers of length 1 to max_hist_len (inclusive)
    max_branch_len   : number of prior branches to track as part of the trigger.
    track_branch_pc  : whether to track the PC of each prior branch.
    track_branch_dec : whether to track the taken/not taken decision of each prior branch.
    shift            : number of bits to cut-off for tracking
        - 0 corresponds to cache line temporal correlation
        - 6 corresponds to page temporal correlation
    """
    def __init__(self, depth, max_hist_len, max_branch_len=0, track_branch_pc=False, track_branch_dec=False, shift=0):
        self.depth = depth
        self.hist = []
        # We're considering the correlation for triggers of length 1 to max_hist_len (inclusive)
        self.max_hist_len = max_hist_len
        self.data = {i: {} for i in range(1, max_hist_len + 1)}
        # How much extra to cutoff for tracking.
        # 0 corresponds to cache line temporal correlation
        # 6 corresponds to page temporal correlation
        self.max_branch_len = max_branch_len
        if self.max_branch_len > 0:
            assert track_branch_pc or track_branch_dec, 'Must track at least one of PC / taken decision if tracking prior branches.'

        self.track_branch_pc = track_branch_pc
        self.track_branch_dec = track_branch_dec
        self.shift = shift

    def add_addr(self, addr):
        # Only take some bits of the full address
        addr_tag = self.addr_tag(addr)

        if len(self.hist) == self.max_hist_len + self.depth - 1:
            # For every history length, keep track of how many times addr_tag shows up
            # given the history
            for hist_len in self.data:
                # tag is the history trigger
                tag = tuple(self.hist[(self.max_hist_len - hist_len):self.max_hist_len])
                if tag not in self.data[hist_len]:
                    self.data[hist_len][tag] = {}

                # Add the current address
                if addr_tag not in self.data[hist_len][tag]:
                    self.data[hist_len][tag][addr_tag] = 0

                self.data[hist_len][tag][addr_tag] += 1

        # Update history with addr_tag
        self.hist.append(addr_tag)
        if len(self.hist) > self.max_hist_len + self.depth - 1:
            self.hist = self.hist[1:]

    def addr_tag(self, addr):
        return addr >> (self.shift + 6)

    def compute_freqs(self, weighted=False):
        freqs = {}
        for hist_len in self.data:
            freqs[hist_len] = {}

            for tag in self.data[hist_len]:
                # # of unique correlated addresses
                num_unique_correlated_addrs = len(self.data[hist_len][tag])
                if num_unique_correlated_addrs not in freqs[hist_len]:
                    freqs[hist_len][num_unique_correlated_addrs] = 0

                # If we want the frequency to be weighted by # of addresses for this
                # history trigger
                if weighted:
                    freqs[hist_len][num_unique_correlated_addrs] += sum(self.data[hist_len][tag].values())
                else:
                    freqs[hist_len][num_unique_correlated_addrs] += 1

        return freqs


def print_freqs(freqs, suffix=''):
    for hist_len in freqs:
        print(hist_len, suffix)
        print({k: freqs[hist_len][k] for k in sorted(freqs[hist_len])})


def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('load_trace')
    parser.add_argument('-d', '--depth', type=int, default=1)
    parser.add_argument('-l', '--max-hist-len', type=int, default=5)
    args = parser.parse_args()

    print('Arguments:')
    print('    Load trace     :', args.load_trace)
    print('    Depth          :', args.depth)
    print('    Max history len:', args.max_hist_len)

    return args


def compute_correlation(load_trace, depth, max_hist_len):
    """Main temporal correlation computation"""
    correlation_data = CorrelationData(depth, max_hist_len)
    page_correlation_data = CorrelationData(depth, max_hist_len, shift=6)
    start = time.time()

    l_open = get_open_function(load_trace)
    with l_open(load_trace, mode='rt', encoding='utf-8') as f:
        gather_correlation_data(f, correlation_data, page_correlation_data)

    print_freqs(correlation_data.compute_freqs(), 'Cache Lines')
    print_freqs(page_correlation_data.compute_freqs(), 'Pages')
    print_freqs(correlation_data.compute_freqs(weighted=True), 'Weighted Cache Lines')
    print_freqs(page_correlation_data.compute_freqs(weighted=True), 'Weighted Pages')
    print('Time to run:', (time.time() - start) / 60, 'min')


if __name__ == '__main__':
    args = get_argument_parser()
    compute_correlation(args.load_trace, args.depth, args.max_hist_len)
