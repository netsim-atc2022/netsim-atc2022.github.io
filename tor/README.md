### Benchmarks

This page describes how to reproduce the Tor simulations that were run for the
research paper described on the [home page](/).

The Tor results are presented in our paper in §5.3 and Appendix E.3.2.

### Host machine

We run the Tor network accuracy verification using a blade server cluster in
which each blade contained identical hardware: 1.25 TiB of RAM and 4×8 core
Intel Xeon E5-4627v2 CPUs (without hyper-threading support) running at 3.30 GHz.
The servers were running CentOS 7 with Linux kernel version 5.11.6-1. We
configured our experiments to run in Docker containers (based off of Ubuntu
v20.04) to ensure that we were running identical software stacks across the
blade machines.

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

### Resource requirements

Our Tor evaluation consists of simulations of networks of different sizes. We
generated 6 different Tor networks at the following scales: 5%, 10%, 15%, 20%,
25%, and 30% of the size of the public network (in terms of nodes and traffic).
The simulations used 178, 357, 540, 727, 919, and 1116 GiB of RAM at Tor network
scales of 5%, 10%, 15%, 20%, 25%, and 30%, respectively.

We ran 10 simulation trials in each of the above 6 networks, and we did this for
both Shadow and Phantom, for a total of 120 simulations. In total, these
experiments required more than a month of computation time on our machines even
when distributed across a 5-machine cluster.

Due to the large resource requirements, we do not expect that it will be easy
to reproduce our results. We provide instructions on how to run the experiments
in case they are useful. Additionally, we publish some simulation outputs that
we used to produce plots for the paper for additional utility.

If you are not going to run the experiments, you can skip ahead to the "plot
results" section to learn how to reproduce our plots from our data.

### Docker setup

Make sure to [install Docker](https://docs.docker.com/get-docker/) and `git`.
and then run the following commands. This process may take up to 15 minutes:

    git clone https://github.com/netsim-atc2022/netsim-atc2022.github.io.git
    cd netsim-atc2022.github.io/setup
    bash build_tor.sh

Once the above commands complete successfully, you should be able to run the
`netsim:tor` image in a container and get a shell:

    docker run \
        --privileged \
        --tmpfs /dev/shm:rw,nosuid,nodev,exec,size=10g \
        -it netsim:tor \
        bash

Once inside the container, you can check that the installation is working:

    /classic/bin/shadow --help
    /phantom/bin/shadow --help

Type `exit` to leave the container.

### Run experiments

The experiments can be run using the following commands, starting from the
artifact base directory `netsim-atc2022.github.io/`:

    cd tor
    mv configs exps
    cd exps

    for f in shadowtor* ; do tar xaf ${f} ; rm ${f} ; done

    for d in shadowtor*phantom*
    do
        cd ${d}
        cp ../../launch.sh .
        cp ../../run_phantom.sh run.sh
        bash launch.sh
        cd ..
    done

    for d in shadowtor*classic
    do
        cd ${d}
        cp ../../launch.sh .
        cp ../../run_classic.sh run.sh
        bash launch.sh
        cd ..
    done

The `launch.sh` script will launch docker and cause it to execute the `run.sh`
script to run all of the experiment configs in serial. This probably isn't
exactly what you want: you may want to distribute the experiments, or you may
want to only run some of the smaller experiments and skip running the larger
ones. However, the scripts provide an illustrative example and can be used
as a starting point from which you can modify to suit your needs.

### Plot results

The output of our own execution of the experiments described above are provided
in the `data` directory. Our plot script will plot this data. If you want the
plot script to plot your own data, you need to move the results from your
`exps/shadowtor*/plot.data` directories into a file structure similar to our
provided data directory.

Set up the analysis environment, starting from the artifact base directory
`netsim-atc2022.github.io/`:

    cd tor
    python3 -m venv pyenv
    source pyenv/bin/activate
    pip install -U pip
    pip install -r requirements.txt

Generate the plots:

    python3 plot.py > stats.txt

This scripts will produce several PDF plots, including those we show in the paper
in Figures
[22a](plots/tor_abs_run_time.pdf),
[22b](plots/tor_rel_run_time.pdf), and
[22c](plots/tor_rel_ram_used.pdf).
