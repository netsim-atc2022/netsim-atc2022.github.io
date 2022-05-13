echo "${RUNHOST}" > runner_hostname.txt

tornettools simulate \
    --shadow "/phantom/bin/shadow" \
    --args "--parallelism=32 --interpose-method=preload --template-directory=shadow.data.template" \
    --filename "shadow.config.yaml" \
    .

tornettools parse .
tornettools archive .
chown --recursive $RUNUSRGRP .
