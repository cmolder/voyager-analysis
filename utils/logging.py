import time

def log_progress(iter_num, n_iters, start_time, interval=10000):
    # TODO add RAM usage.
    if iter_num > 0 and iter_num % interval == 0:
        pct = iter_num / n_iters
        elapsed_time = time.time() - start_time
        left_time = (elapsed_time / iter_num * n_iters) - elapsed_time # estimated time left
        print(f'{iter_num} / {n_iters} ({pct*100:.2f}%) ({elapsed_time / 60:.2f} min) ({left_time / 60:.2f} min est. rem.)')