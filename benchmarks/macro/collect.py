import sys
import os
import json
import argparse
import re
import datetime

from numpy import mean, median, std, var, percentile

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', "--base_directory", 
        help="Path to a directory containing shadow phold results",
        default='exps'
    )
    parser.add_argument('-o', "--prefix_name", 
        help="Prefix for the json output file",
        default='results'
    )
    args = parser.parse_args()
    process_benchmark(args)

def process_benchmark(args):
    print(f"Parsing results from {args.base_directory}")
    data = process_sims(args.base_directory)

    outname = f'{args.prefix_name}.json'
    print(f"Saving results to {outname}")
    with open(outname, 'w') as outf:
        json.dump(data, outf, sort_keys=True, indent=2)

def process_sims(dirname):
    data = []

    for name in os.listdir(dirname):
        path = os.path.join(dirname, name)

        if 'shadow_' not in name or os.path.isfile(path):
            continue

        with open(os.path.join(path, 'shadow.json'), 'r') as inf:
            shadow_json = json.load(inf)

        #hostsdir = os.path.join(path, 'shadow.data/hosts')
        stderr_path = os.path.join(path, 'stderr')
        stdout_path = os.path.join(path, 'stdout')
        free_path = os.path.join(path, 'free.log')

        perf_stats = parse_shadow_stderr(stderr_path)
        seconds_to_init, syscall_counts, object_counts, packet_stats, byte_stats = parse_shadow_stdout(stdout_path)
        mem_used = parse_free_log(free_path)

        shadow_json['~results'] = {
            'perf': perf_stats,
            'syscalls': syscall_counts,
            'objects': object_counts,
            'packets_per_second': packet_stats,
            'bytes_per_second': byte_stats,
            'seconds_to_init': seconds_to_init,
            'mem_used': mem_used,
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
    heartbeat_times = {}
    syscalls, objects = {}, {}
    seconds_to_init = None

    # works for both classic and phantom
    heartbeat_prog = re.compile(" \[shadow-heartbeat\] \[node\] ")

    # classic does not log syscalls
    syscall_phantom_prog = re.compile("Global syscall counts:\s")

    object_phantom_prog = re.compile("Global allocated object counts:\s")
    object_classic_prog = re.compile("ObjectCounter: counter values:\s")

    init_phantom_prog = re.compile("process \'peer.*\' started")
    init_classic_prog = re.compile("ran the pth main thread until it blocked")

    with open(filepath, 'r') as inf:
        for line in inf:
            line = line.strip()

            match = heartbeat_prog.search(line)
            if match:
                parts = line.split(' ', 3)
                realtime = timestamp_to_seconds(parts[0])
                simtime = timestamp_to_seconds(parts[2])
                pkts_send, pkts_recv, bytes_send, bytes_recv = parse_heartbeat(line[match.end():])

                heartbeat_times.setdefault(simtime, {'pkts_send':0, 'pkts_recv':0, 'bytes_send':0, 'bytes_recv':0})
                heartbeat_times[simtime]['pkts_send'] += pkts_send
                heartbeat_times[simtime]['pkts_recv'] += pkts_recv
                heartbeat_times[simtime]['bytes_send'] += bytes_send
                heartbeat_times[simtime]['bytes_recv'] += bytes_recv

                continue

            match = syscall_phantom_prog.search(line)
            if match:
                syscalls = parse_counter_phantom(line[match.end():])
                continue

            match = object_phantom_prog.search(line)
            if match:
                objects = parse_counter_phantom(line[match.end():])
                continue

            match = object_classic_prog.search(line)
            if match:
                objects = parse_counter_classic(line[match.end():])
                continue

            match = init_phantom_prog.search(line)
            if match:
                seconds_to_init = timestamp_to_seconds(line.split(' ', 1)[0])
                continue

            match = init_classic_prog.search(line)
            if match:
                seconds_to_init = timestamp_to_seconds(line.split(' ', 1)[0])
                continue

    packets = [heartbeat_times[s]['pkts_send'] for s in heartbeat_times]
    bytes = [heartbeat_times[s]['bytes_send'] for s in heartbeat_times]

    return seconds_to_init, syscalls, objects, get_stats(packets), get_stats(bytes)

def timestamp_to_seconds(s):
    parts = s.split(':')
    return int(parts[0])*3600.0 + int(parts[1])*60.0 + float(parts[2])

def parse_heartbeat(s):
    parts = s.strip().split(';')
    counters_recv, counters_send = parts[3].split(','), parts[4].split(',')
    # count number of packets that carry >0 payloads, and total bytes in payloads
    return int(counters_send[6]), int(counters_recv[6]), int(counters_send[8]), int(counters_recv[8])

def parse_counter_phantom(s):
    s = s.replace('{', '{"')
    s = s.replace(':', '":')
    s = s.replace(' ', ' "')
    return json.loads(s)

def parse_counter_classic(s):
    d = {}
    parts = s.split(' ')
    for p in parts:
        key, val = p.split('=')
        d[key] = int(val)
    return d

def parse_free_log(filepath):
    mem_used = {}

    last_ts = None
    mem_header = None
    with open(filepath, 'r') as inf:
        for line in inf:
            if "+00" in line:
                ts_str = line.strip().split('+')[0]
                dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                last_ts = dt.timestamp()
            elif 'total' in line and mem_header == None:
                mem_header = [p.strip() for p in line.strip().split()]
            elif "Mem:" in line:
                parts = [p.strip() for p in line.strip().split()]
                mem_counts = [int(p) for p in parts[1:]]

                memd = {f"mem_{mem_header[i]}": mem_counts[i] for i in range(len(mem_counts))}
                used = memd['mem_total'] - memd['mem_available']

                mem_used.setdefault(last_ts, used)

    used_by_system = min(mem_used.values())
    for k in mem_used:
        mem_used[k] -= used_by_system

    return mem_used

def get_stats(datal):
    stats = {
        'count': len(datal),
        'sum': sum(datal),
        'min': min(datal),
        'max': max(datal),
        'mean': mean(datal),
        'median': median(datal),
        'std': std(datal),
        'var': var(datal),
    }
    for p in range(5, 100, 5):
        stats[f'p{p}'] = percentile(datal, p)
    return stats

if __name__ == '__main__':
    sys.exit(main())