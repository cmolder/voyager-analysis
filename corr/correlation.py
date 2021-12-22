import argparse
​
# Process the file as a generator (note the yield)
# To use this script with another file format, you just have to implement a
# replacement for this function.
# All it does is yield every loaded data address
def read_file(load_trace):
​
    def extract_addr(line):
        return int(line.split(', ')[2], 16)
​
    import lzma
    with lzma.open(load_trace, mode='rt', encoding='utf-8') as f:
        for line in f:
            # For handling some invalid lines in the ML-DPC load traces
            if line.startswith('***') or line.startswith('Read'):
                continue
​
            # Yield address
            yield extract_addr(line)
​
class CorrelationData(object):
​
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
​
    def add_addr(self, addr):
        # Only take some bits of the full address
        addr_tag = self.addr_tag(addr)
​
        if len(self.hist) == self.max_hist_len + self.depth - 1:
            # For every history length, keep track of how many times addr_tag shows up
            # given the history
            for hist_len in self.data:
                # tag is the history trigger
                tag = tuple(self.hist[(self.max_hist_len - hist_len):self.max_hist_len])
                if tag not in self.data[hist_len]:
                    self.data[hist_len][tag] = {}
​
                # Add the current address
                if addr_tag not in self.data[hist_len][tag]:
                    self.data[hist_len][tag][addr_tag] = 0
​
                self.data[hist_len][tag][addr_tag] += 1
​
        # Update history with addr_tag
        self.hist.append(addr_tag)
        if len(self.hist) > self.max_hist_len + self.depth - 1:
            self.hist = self.hist[1:]
​
    def addr_tag(self, addr):
        return addr >> (self.shift + 6)
​
    def compute_freqs(self, weighted=False):
        freqs = {}
        for hist_len in self.data:
            freqs[hist_len] = {}
​
            for tag in self.data[hist_len]:
                # # of unique correlated addresses
                num_unique_correlated_addrs = len(self.data[hist_len][tag])
                if num_unique_correlated_addrs not in freqs[hist_len]:
                    freqs[hist_len][num_unique_correlated_addrs] = 0
​
                # If we want the frequency to be weighted by # of addresses for this
                # history trigger
                if weighted:
                    freqs[hist_len][num_unique_correlated_addrs] += sum(self.data[hist_len][tag].values())
                else:
                    freqs[hist_len][num_unique_correlated_addrs] += 1
​
        return freqs
​
def print_freqs(freqs, suffix=''):
    for hist_len in freqs:
        print(hist_len, suffix)
        print({k: freqs[hist_len][k] for k in sorted(freqs[hist_len])})
​
# Main temporal correlation computation
def compute_correlation(load_trace, depth, max_hist_len):
    correlation_data = CorrelationData(depth, max_hist_len)
    page_correlation_data = CorrelationData(depth, max_hist_len, shift=6)
    for addr in read_file(load_trace):
        correlation_data.add_addr(addr)
        page_correlation_data.add_addr(addr)
​
    print_freqs(correlation_data.compute_freqs(), 'Cache Lines')
    print_freqs(page_correlation_data.compute_freqs(), 'Pages')
    print_freqs(correlation_data.compute_freqs(weighted=True), 'Weighted Cache Lines')
    print_freqs(page_correlation_data.compute_freqs(weighted=True), 'Weighted Pages')
​
parser = argparse.ArgumentParser()
parser.add_argument('load_trace')
parser.add_argument('--depth', type=int, default=1)
parser.add_argument('--max-hist-len', type=int, default=5)
args = parser.parse_args()
​
compute_correlation(args.load_trace, args.depth, args.max_hist_len)
