cd exps
echo $RUNHOST > runner_hostname.txt
count=0
for phasenum in 1 2 3 4 5 6
do
    echo "Running phase${phasenum}"
    cd phase${phasenum}
    for d in shadow*
    do
        count=$((count+1))
        cd ${d}
        bash ../free_cmd.sh &
        free_pid=$!
        date
        echo "progress = ${count}"
        pwd
        cat shadow_cmd.sh
        bash shadow_cmd.sh
        kill -9 ${free_pid} 1>/dev/null 2>/dev/null
        cd ..
    done
    cd ..
    chown --recursive $RUNUSRGRP phase${phasenum}
done
