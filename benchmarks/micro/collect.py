import sys
import os
import json

from numpy import mean, median, std, var, percentile

def main():
    process_benchmark('exps')

def process_benchmark(dirname):
    data = process_sims(dirname)
    with open('results.json', 'w') as outf:
        json.dump(data, outf, sort_keys=True, indent=2)

def process_sims(dirname):
    data = []

    for name in os.listdir(dirname):
        path = os.path.join(dirname, name)

        if 'shadow_' not in name or os.path.isfile(path):
            continue

        with open(os.path.join(path, 'shadow.json'), 'r') as inf:
            shadow_json = json.load(inf)

        peerdir = os.path.join(path, 'shadow.data/hosts/peer')
        peerstdout = ''
        for name in os.listdir(peerdir):
            if 'peer' in name and 'stdout' in name and 'benchmark' in name:
                peerstdout = os.path.join(peerdir, name)
                break

        perf_stats = parse_shadow_stderr(os.path.join(path, 'stderr'))
        syscall_counts = parse_shadow_stdout(os.path.join(path, 'stdout'))
        noop_stats, bmark_stats = parse_peer_stdout(peerstdout)

        shadow_json['~results'] = {
            'perf': perf_stats,
            'bmark': bmark_stats,
            'noop': noop_stats,
            'syscalls': syscall_counts,
        }

        data.append(shadow_json)

    return data

def parse_shadow_stderr(filepath):
    d = {}
    with open(filepath, 'r') as inf:
        for line in inf:
            if line[0] == '*':
                continue
            parts = line.strip().split(';')
            if len(parts) < 3:
                continue
            k = parts[2]
            if k == 'duration_time':
                k = 'duration-time-nanos'
                d[k] = int(parts[0])
            elif k == 'task-clock':
                k = 'task-clock-msec'
                d[k] = float(parts[0])
            else:
                d[k] = int(parts[0])
    return d

def parse_shadow_stdout(filepath):
    d = {}
    token = "Global syscall counts: "
    with open(filepath, 'r') as inf:
        for line in inf:
            if token in line:
                line = line.strip()
                i = line.index(token)
                l = len(token)
                s = line[i+l:]
                s = s.replace('{', '{"')
                s = s.replace(':', '":')
                s = s.replace(' ', ' "')
                d = json.loads(s)
                break
    return d

def parse_peer_stdout(filepath):
    noop_usecs = []
    func_usecs = []
    with open(filepath, 'r') as inf:
        for line in inf:
            if 'Time spent in' in line and 'function call' in line:
                parts = line.strip().split()
                if len(parts) < 8:
                    continue
                usec = round(float(parts[7]) * 1000.0, 3)
                if 'write/read function call' in line or 'nanosleep function call' in line:
                    func_usecs.append(usec)
                elif 'no-op function call' in line:
                    noop_usecs.append(usec)

    return get_stats(noop_usecs), get_stats(func_usecs)

def get_stats(usecs):
    stats = {
        'count': len(usecs),
        'min': min(usecs),
        'max': max(usecs),
        'mean': mean(usecs),
        'median': median(usecs),
        'std': std(usecs),
        'var': var(usecs),
    }
    for p in range(5, 100, 5):
        stats[f'p{p}'] = percentile(usecs, p)
    return stats

if __name__ == '__main__':
    sys.exit(main())