import sys
import os
import argparse
import json

from numpy import mean, median, std, var, percentile

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("phase_number", type=int,)
    parser.add_argument("--data_dir", default="data")
    args = parser.parse_args()
    run(args)

def run(args):
    paths = []

    for name in os.listdir(args.data_dir):
        path = os.path.join(args.data_dir, name)
        if f'phase{args.phase_number}-' in name:
            paths.append(path)

    combined_results = combine(paths)

    outname = f'phase{args.phase_number}.json'
    print(f"Saving combined results to {outname}")
    with open(outname, 'w') as outf:
        json.dump(combined_results, outf, sort_keys=True, indent=2)

def combine(paths):
    trials = [load(path) for path in paths]
    return merge(trials)

def load(path):
    with open(path, 'r') as inf:
        return json.load(inf)

def merge(trials):
    combined_exps = []

    for trial in trials:
        for exp in trial:
            filter_keys = ['args', 'cmd', 'label', 'seed']
            delete_keys(exp, filter_keys)
            delete_keys(exp['exe'], filter_keys)
            if select(combined_exps, exp) == None:
                combined_exps.append(copy_exp_metadata(exp))

    for exp in combined_exps:
        all_results = [select(trial, exp)['~results'] for trial in trials]
        exp['~results'] = merge_results(all_results)

    return combined_exps

def merge_results(results):
    merged = {
        'packets': get_stats([r['packets_per_second']['sum'] for r in results]),
        'payload_gib': get_stats([r['bytes_per_second']['sum']/2**30 for r in results]),
        'mem_used_gib': get_stats([max(r['mem_used'].values())/2**30 for r in results]),
        'object_events': get_stats([get_value(r['objects'], "Event", "event_new") for r in results]),
        'object_payloads': get_stats([get_value(r['objects'], "Payload", "payload_new") for r in results]),
        'seconds_to_init': get_stats([r['seconds_to_init'] for r in results]),
        'seconds_post_init': get_stats([r['perf']['duration-time-nanos']/10.0**9 - r['seconds_to_init'] for r in results]),
        'syscalls': get_stats([sum(r['syscalls'].values()) for r in results]),
    }

    for key in results[0]['perf'].keys():
        if 'duration-time-nanos' in key:
            merged[f'perf_duration-time-sec'] = get_stats([r['perf'][key]/10.0**9 for r in results])
        else:
            merged[f'perf_{key}'] = get_stats([r['perf'][key] for r in results])

    return merged

def get_value(d, key1, key2):
    if key1 in d:
        return d[key1]
    else:
        return d[key2]

def delete_keys(d, keys):
    for key in keys:
        del d[key]

def select(exp_list, exp_find):
    matched = []
    for exp in exp_list:
        keys_cmp = [k for k in exp if k != 'exe' and k != "~results"]
        if match(exp, exp_find, keys_cmp) and \
                match(exp['exe'], exp_find['exe'], exp['exe'].keys()):
            matched.append(exp)
    if len(matched) == 0:
        return None
    assert len(matched) == 1
    return matched[0]
    
def match(da, db, keys):
    for key in keys:
        if da[key] != db[key]:
            return False
    return True

def copy_exp_metadata(exp):
    d = {k: exp[k] for k in exp if k != 'exe' and k != "~results"}
    d['exe'] = {k: exp['exe'][k] for k in exp['exe']}
    return d

def get_stats(datal):
    stats = {
        'count': len(datal),
        #'sum': sum(datal),
        'min': min(datal),
        'max': max(datal),
        'mean': mean(datal),
        'median': median(datal),
        'std': std(datal),
        'var': var(datal),
        #'values': datal,
    }
    #for p in range(5, 100, 5):
    #    stats[f'p{p}'] = percentile(datal, p)
    return stats

if __name__ == '__main__':
    sys.exit(main())