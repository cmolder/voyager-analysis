INST_SIZE = 64
N_INST_DESTS = 2
N_INST_SRCS = 4

def read_champsim_trace(f, max_inst=100):
    for i, bytes in enumerate(_get_instruction_bytes(f)):
        #print(f'{i:8}:', bytes)
        inst = Instruction(bytes)
        print(f'{i:8}:', inst)

        if i >= max_inst:
            return

def _get_instruction_bytes(f):
    while True:
        bytes = f.read(INST_SIZE)
        if not bytes or len(bytes) < INST_SIZE:
            break
        yield bytes


def get_instructions(f):
    while True:
        bytes = f.read(INST_SIZE)
        if not bytes or len(bytes) < INST_SIZE:
            break
        yield Instruction(bytes)


class Instruction:
    def __init__(self, bytes):
        self.pc = int.from_bytes(bytes[:8], 'big')
        assert bytes[8] == 0 or bytes[8] == 1, f'is_branch not boolean, is {bytes[8]}'
        assert bytes[9] == 0 or bytes[9] == 1, f'branch_taken not boolean, is {bytes[9]}'
        self.is_branch = bool(bytes[8])
        self.branch_taken = bool(bytes[9])

        self.dest_regs = []
        self.src_regs = []
        self.dest_mem = []
        self.src_mem = []

        for i in range(N_INST_DESTS):
            reg = bytes[10 + i]
            if reg > 0:
                self.dest_regs.append(reg)
        for i in range(N_INST_SRCS):
            reg = bytes[10 + N_INST_DESTS + i]
            if reg > 0:
                self.src_regs.append(reg)
        for i in range(N_INST_DESTS):
            start = 10 + N_INST_DESTS + N_INST_SRCS + i * 8
            addr = int.from_bytes(bytes[start : start + 8], 'big')
            if addr > 0:
                self.dest_mem.append(addr)
        for i in range(N_INST_SRCS):
            start = 10 + 9*N_INST_DESTS + N_INST_SRCS + i * 8
            addr = int.from_bytes(bytes[start : start + 8], 'big')
            if addr > 0:
                self.dest_mem.append(addr)

    def __str__(self):
        return f'pc={hex(self.pc)} branch={str(self.is_branch):5} branch_taken={str(self.branch_taken):5} dest_regs={self.dest_regs} src_regs={self.src_regs} dest_mem={[hex(a) for a in self.dest_mem]} src_mem={[hex(a) for a in self.src_mem]}'
