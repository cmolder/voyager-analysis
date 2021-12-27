INST_SIZE = 64
N_INST_DESTS = 2
N_INST_SRCS = 4


def read_champsim_trace(f, max_inst=100):
    """Read and print each instruction of the ChampSim trace,
    up to max_inst instructions.
    """
    for i, bytearr in enumerate(_get_instruction_bytes(f)):
        #print(f'{i + 1:8}:', bytearr)
        inst = Instruction(bytearr)
        print(f'{i + 1:8}:', inst)

        if i + 1 >= max_inst:
            return


def _get_instruction_bytes(f):
    """Yield the next INST_SIZE bytes of the file,
    as a generator."""
    while True:
        bytearr = f.read(INST_SIZE)
        if not bytearr or len(bytearr) < INST_SIZE:
            break
        yield bytearr


def get_instructions(f):
    """Yield the next instruction in the file,
    as a generator."""
    while True:
        bytearr = f.read(INST_SIZE)
        if not bytearr or len(bytearr) < INST_SIZE:
            break
        yield Instruction(bytearr)


class Instruction:
    """Interpret a INST_SIZE byte chunk of the file
    as its proper instruction notation.
    For further reference, see instruction code in ChampSim repo.
    """
    def __init__(self, bytearr):
        self.pc = int.from_bytes(bytearr[:8], 'little')
        assert bytearr[8] == 0 or bytearr[8] == 1, f'is_branch not boolean, is {bytearr[8]}'
        assert bytearr[9] == 0 or bytearr[9] == 1, f'branch_taken not boolean, is {bytearr[9]}'
        self.is_branch = bool(bytearr[8])
        self.branch_taken = bool(bytearr[9])

        self.dest_regs = []
        self.src_regs = []
        self.dest_mem = []
        self.src_mem = []

        for i in range(N_INST_DESTS):
            reg = bytearr[10 + i]
            if reg > 0:
                self.dest_regs.append(reg)
        for i in range(N_INST_SRCS):
            reg = bytearr[10 + N_INST_DESTS + i]
            if reg > 0:
                self.src_regs.append(reg)
        for i in range(N_INST_DESTS):
            start = 10 + N_INST_DESTS + N_INST_SRCS + i * 8
            addr = int.from_bytes(bytearr[start:start + 8], 'little')
            if addr > 0:
                self.dest_mem.append(addr)
        for i in range(N_INST_SRCS):
            start = 10 + 9 * N_INST_DESTS + N_INST_SRCS + i * 8
            addr = int.from_bytes(bytearr[start:start + 8], 'little')
            if addr > 0:
                self.src_mem.append(addr)

    def __str__(self):
        return f'pc={hex(self.pc)} branch={str(self.is_branch):5} branch_taken={str(self.branch_taken):5} dest_regs={self.dest_regs} src_regs={self.src_regs} dest_mem={[hex(a) for a in self.dest_mem]} src_mem={[hex(a) for a in self.src_mem]}'
