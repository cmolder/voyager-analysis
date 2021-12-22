"""Performs a sweep of prefetch trace generation,
generating directories and results autmoatically.
"""

import glob
import argparse
import os
import subprocess
import time
from collections import defaultdict
import pandas as pd

# Prefetchers:
#     generate_pc.py <load_trace> <pc_load_trace> <start> generates an optimal prefetch trace from instruction ID start (in millions).
#     pc_sisb.py <load_trace> <pc_load_trace> generates a (PC-localized?) SISB prefetch trace.
#     sisb.py <load_trace> <pc_load_trace> generates a SISB prefetch trace.

# Diff:
#     diff.py <trace1> <trace2> <start> gets the difference between two prefetch traces.



def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('load_trace_dir') # Input folder of load traces
    parser.add_argument('pc_trace_dir') # Output folder of prefetch traces
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--diff-start', default=10) # Diff start in millions
    args = parser.parse_args()

    print('Arguments:')
    print('    Load traces  :', args.load_trace_dir)
    print('    Output folder:', args.pc_trace_dir)
    print('    Diff start   :', args.diff_start, 'million')
    
    return args



"""Generate prefetch trace files"""
def prefetch_sweep(args):
    print('\n===\n===== Generating prefetch traces... =====\n===')
    
    if not args.dry_run:
        os.makedirs(os.path.join(args.pc_trace_dir, 'generate_pc'), exist_ok=True)
        os.makedirs(os.path.join(args.pc_trace_dir, 'pc_sisb'), exist_ok=True)
        os.makedirs(os.path.join(args.pc_trace_dir, 'sisb'), exist_ok=True)
        os.makedirs(os.path.join(args.pc_trace_dir, 'bo'), exist_ok=True)

    processes = []
    cwd = os.getcwd()
    files = glob.glob(os.path.join(args.load_trace_dir, '*.*'))
    for f in files:
        
        tracename = f.split('/')[-1].rstrip('.txt')
        gpc_outf = os.path.join(args.pc_trace_dir, 'generate_pc', tracename + '_out.txt')
        pcsisb_outf = os.path.join(args.pc_trace_dir, 'pc_sisb', tracename + '_out.txt')
        sisb_outf = os.path.join(args.pc_trace_dir, 'sisb', tracename + '_out.txt')
        bo_outf = os.path.join(args.pc_trace_dir, 'bo', tracename + '_out.txt')

        print(f'\n{tracename} ({f})')
        print(f'    generate_pc output: {gpc_outf}')
        print(f'    pc_sisb output    : {pcsisb_outf}')
        print(f'    sisb output       : {sisb_outf}')
        print(f'    bo output         : {bo_outf}')

        if args.dry_run:
            continue
            
        p = subprocess.Popen([
            'python',
            os.path.join(cwd, 'generate_pc.py'), 
            f, gpc_outf, '0'], 
        )
        processes.append(p)

        p = subprocess.Popen([
            'python',
            os.path.join(cwd, 'pc_sisb.py'), 
            f, pcsisb_outf], 
        )
        processes.append(p)

        p = subprocess.Popen([
            'python',
            os.path.join(cwd, 'sisb.py'), 
            f, sisb_outf], 
        )
        processes.append(p)

        subprocess.Popen([
            'python',
            os.path.join(cwd, "bo.py"), 
            f, bo_outf], 
        )

    if args.dry_run:
        return

    print('\nWaiting for trace generation to complete...')
    start = time.time()
    for p in processes:
        p.wait()
    print(f'Trace generation complete. Time: {time.time() - start:.2f} s')


    
"""Difference analysis"""
difference_keys = ['diffs', 'diff1', 'diff2', 'diff12', 'diffs_raw', 'diff1_raw', 
                   'diff2_raw', 'diff12_raw', 'total_keys']

def get_diff_data(file1, file2, start, trace_name, prefetcher_name):
    cwd = os.getcwd()
    out = subprocess.check_output([
        'python',
        os.path.join(cwd, 'diff.py'), 
        file1, file2, str(start)], 
    )
    
    values = out.decode('utf-8').replace('\n', '').split(' ')
    
    data = {}
    data['Trace'] = trace_name
    data['Baseline'] = prefetcher_name
    for i, v in enumerate(values):
        data[difference_keys[i]] = v
        
    return data


def difference_sweep(args):
    print('\n===\n===== Calculating differences... =====\n===')
    results_out = os.path.join(args.pc_trace_dir, 'diff.csv')
    files = glob.glob(os.path.join(args.load_trace_dir, '*.*'))
    results = defaultdict(list)
    print('Results data will be saved to:', results_out)
    
    for f in files:
        tracename = f.split('/')[-1].rstrip('.txt')
        gpc_outf = os.path.join(args.pc_trace_dir, 'generate_pc', tracename + '_out.txt')
        pcsisb_outf = os.path.join(args.pc_trace_dir, 'pc_sisb', tracename + '_out.txt')
        sisb_outf = os.path.join(args.pc_trace_dir, 'sisb', tracename + '_out.txt')
        bo_outf = os.path.join(args.pc_trace_dir, 'bo', tracename + '_out.txt')

        print(f'\n{tracename} ({f})')
        print('    pc_sisb')
        res = get_diff_data(gpc_outf, pcsisb_outf, args.diff_start, tracename, 'pc_sisb')
        for k in res:
            results[k].append(res[k])
       
        print('    sisb')
        res = get_diff_data(gpc_outf, sisb_outf, args.diff_start, tracename, 'sisb')
        for k in res:
            results[k].append(res[k])
            
        print('    bo')
        res = get_diff_data(gpc_outf, bo_outf, args.diff_start, tracename, 'bo')
        for k in res:
            results[k].append(res[k])

    results = pd.DataFrame.from_dict(results)
    
    
    if not args.dry_run:
        results.to_csv(results_out, index=False)
    
    
    
    
if __name__ == '__main__':
    args = get_argument_parser()
    prefetch_sweep(args)
    difference_sweep(args)