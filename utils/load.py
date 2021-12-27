import os
import glob
import lzma
import gzip
import numpy as np
import pandas as pd
import attrdict


def get_open_function(path):
    """Choose an open function based on the file's extension."""
    if path.endswith('xz'):
        return lzma.open
    elif path.endswith('gz'):
        return gzip.open
    return open



def load_simpoint_weights(simpoints_dir, trace):
    """Load simpoint weights for a given trace."""
    simpoints = pd.DataFrame(columns=['trace', 'weight'])
    for f in glob.glob(os.path.join(simpoints_dir, '*.csv')):
        df = pd.read_csv(f)
        simpoints = pd.concat((simpoints, df))
    tr_points = simpoints[simpoints.trace.str.contains(trace)]
    weights = np.array(tr_points.weight.array)
    return weights


def parse_champsim_result_file(f, max_instruction_num=None, min_instruction_interval=0):
    data = {
        'instructions': [],
        'cycles': [],
        'heartbeat_ipcs': [],
        'cumulative_ipcs': [],
        'cumulative_sim_times': [],
    }
    
    last_instruction = 0
    warmups_completed = 0 # 0 = none, 1 = CPU, 2 = CPU + prefetch
    for line in f:
        line_tokens = line.split(' ')
        
        # Only append data after the prefetch warmup completes.
        # DEBUG - Hardcoded stop condition (for now. It should stop
        # automatically, but for some reason it doesn't).
        if 'Warmup complete' in line:
            warmups_completed += 1
        
        if 'Heartbeat' in line:
            #print(line)
            instructions = int(line_tokens[line_tokens.index('instructions:') + 1])
            cycles = int(line_tokens[line_tokens.index('cycles:') + 1])
            heartbeat_ipc = float(line_tokens[line_tokens.index('heartbeat') + 2])
            cumulative_ipc = float(line_tokens[line_tokens.index('cumulative') + 2])
            cumulative_sim_time = int(line_tokens[line_tokens.index('time:') + 1]) * 3600 \
                              + int(line_tokens[line_tokens.index('time:') + 3]) * 60 \
                              + int(line_tokens[line_tokens.index('time:') + 5]) \

            # DEBUG - Temporary fix until we can figure out why
            # ChampSim runs too long.
            if max_instruction_num and instructions >= max_instruction_num: 
                warmups_completed = 0
            
            if warmups_completed >= 2 and instructions - last_instruction > min_instruction_interval:
                data['instructions'].append(instructions)
                data['cycles'].append(cycles)
                data['heartbeat_ipcs'].append(heartbeat_ipc)
                data['cumulative_ipcs'].append(cumulative_ipc)
                data['cumulative_sim_times'].append(cumulative_sim_time)
                last_instruction = instructions
        
        if 'LLC PREFETCH' in line and 'REQUESTED' in line:
            #print(line)
            #print(line.split())
            data['useless_prefetches'] = int(line.split()[-4])
            data['useful_prefetches'] = int(line.split()[-6])
            data['uac_correct_prefetches'] = int(line.split()[-1])
            data['issued_prefetches'] = int(line.split()[-8])
        if 'LLC LOAD' in line:
            data['llc_load_hits'] = int(line.split()[-3])
            data['llc_load_misses'] = int(line.split()[-1])            
        if 'LLC RFO' in line:
            data['llc_rfo_hits'] = int(line.split()[-3])
            data['llc_rfo_misses'] = int(line.split()[-1])
            
    safediv = lambda x, y : x / y if y != 0 else 0
    data['accuracy'] = safediv(data['useful_prefetches'], (data['useful_prefetches'] + data['useless_prefetches']))
    data['uac'] = safediv(data['uac_correct_prefetches'], data['issued_prefetches'])
    # Coverage must be calculated separately, since it depends on the baseline prefetcher.
    
    return attrdict.AttrDict(data)

def load_champsim_base_results(base, tracename, verbose=False, **kwargs):
    base_path = base + f'*{tracename}*.txt'
    data = {}
    if verbose:
        print('Loading results from:', base_path)
    variation_paths = sorted(glob.glob(base_path))
    for path in variation_paths:
        if '-bo' in os.path.basename(path):
            variation_name = 'BO'
        elif '-sisb_bo' in os.path.basename(path):
            variation_name = 'ISB+BO'
        elif '-sisb-' in os.path.basename(path):
            variation_name = 'ISB'
        elif '-no' in os.path.basename(path):
            variation_name = 'NoPrefetcher'
        else:
            continue
        with open(path, 'r') as f:
            data[variation_name] = parse_champsim_result_file(
                f, **kwargs
            )
    if verbose:
        print('    Found variations:', *data.keys())
    return data

def parse_paper_result_file(f, strip_prefixes=False):
    df = pd.read_csv(f, index_col='prefetcher')
    
    if strip_prefixes:
        newcolumns = []
        for c in df.columns:
            c = c.split('.')[-1]
            newcolumns.append(c)
        df.columns = newcolumns
    
    return df.to_dict()