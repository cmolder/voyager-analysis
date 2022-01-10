class LoadTraceInstruction(object):
    """Track load trace instruction in an orderly manner."""
    def __init__(self, line):
        tokens = line.split(', ')
        self.uiid = int(tokens[0])
        self.cycle = int(tokens[1])
        self.addr = int(tokens[2], 16)
        self.pc = int(tokens[3], 16)
        self.is_hit = bool(tokens[4])

        # List of (pc, dec) tuples, from most recent to least recent.
        #print(tokens[5:])
        self.branches = [(int(tokens[i], 16), bool(int(tokens[i + 1]))) for i in range(5, len(tokens), 2)]

    def __str__(self):
        s = f'uiid={self.uiid} cycle={self.cycle} pc={hex(self.pc)} addr={hex(self.addr)} is_hit={self.is_hit} branches=['
        for pc, dec in self.branches:
            if pc == 0 and not dec:
                continue
            s += f'(pc={hex(pc)} dec={"T" if dec else "NT"})'
        s += ']'
        return s


def get_instructions(f):
    """Process the load trace as a generator, (note the yield)
    yielding every loaded data address.
    Can call using gather_correlation_data inside an
    open (or variant) context."""
    for line in f:
        # For handling some invalid lines in the ML-DPC load traces
        if line.startswith('***') or line.startswith('Read'):
            continue
        yield LoadTraceInstruction(line)
