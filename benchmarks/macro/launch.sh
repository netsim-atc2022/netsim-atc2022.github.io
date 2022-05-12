docker run \
    --privileged \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp=unconfined \
    --log-driver none \
    --shm-size=512g \
    --pids-limit -1 \
    --ulimit nofile=10485760:10485760 \
    --ulimit nproc=-1:-1 \
    --ulimit sigpending=-1 \
    --ulimit rtprio=99:99 \
    -v "$(pwd)":/root/data:z \
    -v /dev/shm \
    --tmpfs /dev/shm:rw,nosuid,nodev,exec,size=512g \
    --rm \
    --env RUNHOST="$(hostname)" \
    --env RUNUSRGRP="$(id -u):$(id -g)" \
    netsim:benchmark
