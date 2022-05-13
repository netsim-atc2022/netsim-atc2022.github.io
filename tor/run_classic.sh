echo "${RUNHOST}" > runner_hostname.txt

numhosts=$(cat shadow.config.xml | grep 'host id' | wc -l)

tornettools simulate \
    --shadow "/classic/bin/shadow" \
    --args "--workers=${numhosts} --max-concurrency=32 --scheduler-policy=host --pin-cpus" \
    --filename "shadow.config.xml" \
    .

tornettools parse .
tornettools archive .
chown --recursive $RUNUSRGRP .