"""Compute correlation between access history and next prefetch,
using ChampSim traces.

TODO: Implement branch history
"""

import argparse
import lzma
import time

try:
    from utils.champsim_trace import get_instructions
except:
    import os
    os.chdir('../')
    from utils.champsim_trace import get_instructions


"""File I/O"""
def gather_correlation_data(f, cd, pcd):
    """Wrapper function to gather correlation data
    from each address in the load trace."""
    for inst in get_instructions(f):
        if not inst.is_branch and len(inst.src_mem) > 0:
            cd.add_addr(inst.src_mem[0])
            pcd.add_addr(inst.src_mem[0]) # TODO what if there is more than one source address?


def extract_addr(line):
    return int(line.split(', ')[2], 16)


"""Correlation"""
class CorrelationData(object):

    def __init__(self, depth, max_hist_len, shift=0):
        self.depth = depth
        self.hist = []
        # We're considering the correlation for triggers of length 1 to max_hist_len (inclusive)
        self.max_hist_len = max_hist_len
        self.data = {i: {} for i in range(1, max_hist_len + 1)}
        # How much extra to cutoff for tracking.
        # 0 corresponds to cache line temporal correlation
        # 6 corresponds to page temporal correlation
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

# Main temporal correlation computation

"""Driver (and helper) functions"""
def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('load_trace')
    parser.add_argument('--depth', type=int, default=1)
    parser.add_argument('--max-hist-len', type=int, default=5)
    args = parser.parse_args()
    
    print('Arguments:')
    print('    Load trace     :', args.load_trace)
    print('    Depth          :', args.depth)
    print('    Max history len:', args.max_hist_len)

    return args


def compute_correlation(load_trace, depth, max_hist_len):
    correlation_data = CorrelationData(depth, max_hist_len)
    page_correlation_data = CorrelationData(depth, max_hist_len, shift=6)
    start = time.time()

    if load_trace.endswith('xz'):
        with lzma.open(load_trace, mode='rt', encoding='utf-8') as f:
            gather_correlation_data(f, correlation_data, page_correlation_data)     
    else:
        with open(load_trace) as f:
            gather_correlation_data(f, correlation_data, page_correlation_data)

    print_freqs(correlation_data.compute_freqs(), 'Cache Lines')
    print_freqs(page_correlation_data.compute_freqs(), 'Pages')
    print_freqs(correlation_data.compute_freqs(weighted=True), 'Weighted Cache Lines')
    print_freqs(page_correlation_data.compute_freqs(weighted=True), 'Weighted Pages')
    print('Time to run:', time.time() - start)


if __name__ == '__main__':
    args = get_argument_parser()
    compute_correlation(args.load_trace, args.depth, args.max_hist_len)
