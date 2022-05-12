### Benchmarks

This page describes how to reproduce the benchmarks that were run for the
research paper described on the [home page](/). Our benchmark experiments are
split into _microbenchmarks_ and _macrobenchmarks_.

### Host machine

All of the microbenchmark and macrobenchmark experiments were conducted using a
blade server cluster in which each blade contained identical hardware: 256 GiB
of RAM and 2×14 core Intel Xeon E5-2697v3 CPUs (56 total hyper-threads) running
at 2.6 GHz. Each blade machine was running CentOS 7 and Linux kernel version
5.11.6-1, although other versions of Linux should work just as well as long as
it can run docker. We configured our experiments to run in docker containers to
ensure that we were running identical software stacks across the blade machines.

Set these configs on the host machine:

    sudo su
    echo fs.nr_open = 104857600 >> /etc/sysctl.conf
    echo fs.file-max = 104857600 >> /etc/sysctl.conf
    echo vm.max_map_count = 1073741824 >> /etc/sysctl.conf
    echo kernel.pid_max = 4194300 >> /etc/sysctl.conf
    echo kernel.threads-max = 4194300 >> /etc/sysctl.conf
    echo kernel.sched_rt_runtime_us = -1 >> /etc/sysctl.conf
    exit

You may need to log out and back in, or reboot to apply these settings.

The microbenchmarks should consume no more than 5 GiB of RAM, and should
complete within a few minutes. Some of the macrobenchmarks may consume up to 256
GiB of RAM, and should complete within a week.

### Microbenchmarks

The microbenchmarks are presented in our paper in §5.1 and Appendix E.1.

#### Docker setup

Make sure to [install Docker](https://docs.docker.com/get-docker/) and `git`.
and then run the following commands. This process should only take a few minutes:


    git clone https://github.com/netsim-atc2022/netsim-atc2022.github.io.git
    cd netsim-atc2022.github.io/setup
    bash build_benchmark.sh

Once the above commands complete successfully, you should be able to run the
`netsim:benchmark` image in a container and get a shell:

    docker run \
        --privileged \
        --tmpfs /dev/shm:rw,nosuid,nodev,exec,size=10g \
        -it netsim:benchmark \
        bash

Once inside the container, you can check that the installation is working:

    /classic/bin/shadow --help
    /phantom/bin/shadow --help
    /phantom-nopreload/bin/shadow --help

Type `exit` to leave the container.

#### Run experiments

The microbenchmark experiments should consume no more than 5 GiB of RAM. They
require 100 GiB of storage space and should complete within 15 minutes. The
experiments can be run using the following commands, starting from the artifact
base directory `netsim-atc2022.github.io/`:

    cd benchmarks/micro
    tar xJf configs.tar.xz
    mv configs exps
    bash launch.sh

The `launch.sh` script will launch docker and cause it to execute the `run.sh`
script to run all of the experiment configs. This process internally runs the
correct number of trials of each experiment.

#### Plot results

Set up the analysis environment, starting from the artifact base directory
`netsim-atc2022.github.io/`:

    cd benchmarks/micro
    python3 -m venv pyenv
    source pyenv/bin/activate
    pip install -U pip
    pip install -r requirements.txt

Collect the data from the experiments you just ran, which should be located in
the `exps` dir. This process will take a minute or two to parse the results:

    python3 collect.py

The above command should produce a `results.json` file in the current directory.
(We provide the results we collected from our own execution of these experiments
in the `data/results.json` file.)
Once you have a `results.json` in your CWD, you can reproduce the plots with:

    python3 plot.py

We provide in the `plots` subdirectory the output from running the above command
on our `data/results.json` file; these plots are shown in our paper in Figures
[4](plots/interpose.pdf), [5](plots/memmgr.pdf),
[6](plots/cpusched-seccomp.pdf), [16](plots/cpusched-ptrace.pdf), and
[17](plots/cpusched-classic.pdf).

### Macrobenchmarks

The macrobenchmarks are presented in our paper in §5.2 and Appendix E.2.

#### Docker setup

The macrobenchmarks use the same docker image that was built above for the
microbenchmarks, and no additional setup is required.

#### Analysis environment

Set up the analysis environment that you will need to process and plot the
results, starting from the artifact base directory `netsim-atc2022.github.io/`:

    cd benchmarks/macro
    python3 -m venv pyenv
    source pyenv/bin/activate
    pip install -U pip
    pip install -r requirements.txt

#### Run experiments

Some of the macrobenchmarks may consume up to 256 GiB of RAM at once. Running
them all will collectively require 100-200 GiB of storage space a week or two
when running them serially. 

We understand that it may not be feasible for everyone to re-run our experiments
due to the resource requirements. For those unable to run the experiments, we
also provide the output of our own execution and you can use that output to
reproduce the plots in our paper instead. If you are unable to run the
experiments, please skip ahead to the "plot results" section below.

The experiments can be run using the following commands, starting from the
artifact base directory `netsim-atc2022.github.io/`:

    cd benchmarks/macro

To run a single trial:

    tar xJf configs.tar.xz
    mv configs exps
    bash launch.sh

The `launch.sh` script will launch docker and cause it to execute the `run.sh`
script to run all of the experiment configs. Each execution of the launch script
runs a single trial, which should finish in a day or two.

To run multiple trials (e.g., 3):

    for trial in 1 2 3
    do
        tar xJf configs.tar.xz
        mv configs exps
        bash launch.sh
        mv exps exps{$trial}
    done

We ran 10 trials for our paper, manually parallelizing the trials across
multiple machines with identical hardware, but you may be able to reproduce our
general conclusions with a single or just a few trials.

#### Process results

This step parses the raw simulation output into json data files that are more
suitable for plotting.

We understand that it may not be feasible for everyone to re-run our experiments
due to the resource requirements. If you were unable to run our experiments in the previous section, then you should skip ahead to the "plot results" section.

If you are able to run our experiments, then the next step is to collect the
results from each trial we just ran. This process should take about 1-2 minutes
per trial to run.

To parse and then collapse data from a single trial:

    for phase in 1 2 3 4 5 6
    do
        python3 collect.py -i exps/phase${phase} -o phase${phase}-1
    done

To parse data from multiple trials (e.g., 3):

    for trial in 1 2 3
    do
        for phase in 1 2 3 4 5 6
        do
            python3 collect.py -i exps${trial}/phase${phase} -o phase${phase}-${trial}
        done
    done

Finally, we merge/collapse the results across all trials into a single json file
for each of 6 phases. If you ran your own experiments:

    for phase in 1 2 3 4 5 6
    do
        python3 combine.py --data_dir . phase${phase}
    done

This produces 6 json data files, named `phase[1-6].json`.

#### Plot results

Make sure you're in the macro directory and activate the pyenv environment from
the process step above:

    cd benchmarks/macro
    source pyenv/bin/activate

If you were unable to run the experiments above, you can use our data instead.
We have placed the json files that the processing step produced from running our
10 trials into the `data` subdirectory. To use this data for plotting, you first
need to get our json data files in your CWD. (If you already have your own data
following the steps in the previous section, skip this command.)

    cp data/* .

Run all of the plotting scripts. Note you will need `latex` tools installed
because the plots that we generate uses latex to format some text:

    bash plot_all.sh

Several PDFs should be generated in the current directory as well as in several
`phase[1-6]_metrics` subdirectories. We provide the plots that appeared in the
paper in the `plots` subdirectory; these plots are shown in our paper in Figures
[7](plots/phold-phase1-perf-duration-time-sec-skewed.pdf),
[8](plots/phold-phase2-cpusched-bar.pdf),
[9](plots/phold-phase3-memmgr-bar-seccomp.pdf),
[10](plots/phold-phase4-sched-bar-seccomp.pdf),
[11a](plots/phold-phase6-perf-duration-time-sec-28.pdf),
[11b](plots/phold-phase6-seconds-to-init-28.pdf),
[11c](plots/phold-phase6-mem-used-gib-28.pdf),
[18](plots/phold-phase1-seconds-to-init-skewed.pdf),
[19](plots/phold-phase3-memmgr-bar-ptrace.pdf),
[20](plots/phold-phase4-sched-bar-ptrace.pdf),
[21a](plots/phold-phase5-cpuload-bar.pdf),
[21b](plots/phold-phase5-msgload-bar.pdf), and
[21c](plots/phold-phase5-weights-bar.pdf).
