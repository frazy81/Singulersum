#!/bin/bash

# 2021-03-26 ph Created

# run_tests.sh
# 2021-03-26 Created by Philipp Hasenfratz
#
# runs all tests in /tests. ALL TESTS SUCCESSFUL! at the end means that all tests
# passed, script ends with exit-code 0. Otherwise a warning is shown and this scripts
# ends with exit-code 1.

regex="^unittest_(.*?)\.py$"
count=0
skipped=""
for f in *
do
    if [[ $f =~ $regex ]]; then
        echo
        echo running test $f

        /usr/bin/python3 "$f";
        test $? -eq 0 || { echo "FAILED!"; exit 1; }

        let count+=1
    else
        if [[ -z "$skipped" ]]; then
            skipped="$f"
        else
            skipped+=", $f"
        fi
        echo
        echo $f is NOT part of test-suite!
    fi
done

echo
echo
echo ALL $count TESTS SUCCESSFUL!
echo files not part of test suite: $skipped
exit 0
