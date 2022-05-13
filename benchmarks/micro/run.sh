set -euo pipefail

cd exps
for d in shadow*
do
    cd ${d}
    bash shadow_cmd.sh
    cd ..
done
cd ..
chown --recursive $RUNUSRGRP exps
