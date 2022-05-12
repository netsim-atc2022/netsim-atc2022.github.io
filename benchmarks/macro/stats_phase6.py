import sys
import json

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from scipy.stats import linregress

def main():
    db = TinyDB(storage=MemoryStorage)
    with open("phase6.json", 'r') as inf:
        db.insert_multiple(json.load(inf))

    run(db, 'perf_duration-time-sec')
    run(db, 'seconds_to_init')
    run(db, 'seconds_post_init')
    run(db, 'mem_used_gib')

def run(db, metric):
    x_phantom = [1000 * 2**e for e in range(7)]
    x_classic = [1000 * 2**e for e in range(5)]

    y_seccomp = [select(db, q, 'seccomp', metric) for q in x_phantom]
    y_ptrace = [select(db, q, 'ptrace', metric) for q in x_phantom]
    y_classic = [select(db, q, 'classic', metric) for q in x_classic]

    run_regression(f'seccomp {metric}', x_phantom, y_seccomp)
    print(f'{metric} values:', json.dumps(y_seccomp))

    run_regression(f'ptrace {metric}', x_phantom, y_ptrace)
    print(f'{metric} values:', json.dumps(y_ptrace))

    run_regression(f'classic {metric}', x_classic, y_classic)
    print(f'{metric} values:', json.dumps(y_classic))


def run_regression(label, x, y):
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    print(f'label: {label}\n\tslope: {slope}\n\tr: {r_value}\n\tr2: {r_value**2}\n\tp: {p_value}')

def select(db, eq, im, metric):
    q = Query()

    records = db.search(
        (q.exe.msgload == 100) &
        (q.exe.quantity == eq) &
        (q.exe.weights == 'skewed') &
        (q.interpose_method == im) &
        (q.num_workers == 28) &
        (q.scheduling_policy == 'host') &
        (q.use_memory_manager == (None if im == 'classic' else True)) &
        (q.use_pinning == True) &
        (q.use_realtime == False) &
        (q.use_syscall_preloading == (None if im == 'classic' else True))
    )

    #print(json.dumps(records, sort_keys=True, indent=2))
    assert len(records) == 1

    result = records[0]['~results'][metric]
    #print(json.dumps(result, sort_keys=True, indent=2))
    return result['mean']
    

if __name__ == "__main__":
    sys.exit(main())
