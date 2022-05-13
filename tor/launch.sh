docker run \
    --privileged \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp=unconfined \
    --log-driver none \
    --shm-size=1t \
    --pids-limit -1 \
    --ulimit nofile=10485760:10485760 \
    --ulimit nproc=-1:-1 \
    --ulimit sigpending=-1 \
    --ulimit rtprio=99:99 \
    -v /storage/rjansen/share:/share:z \
    -v "$(pwd)":/root/data:z \
    -v /dev/shm \
    --tmpfs /dev/shm:rw,nosuid,nodev,exec,size=1t \
    --rm \
    --env RUNHOST="$(hostname)" \
    --env RUNUSRGRP="$(id -u):$(id -g)" \
    netsim:tor
