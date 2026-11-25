#!/bin/bash
# usage: bench.sh name cmd...  -> median wall ms and max RSS KB over 10 runs of `cmd --version`
n=$1; shift
for i in 1 2 3 4 5 6 7 8 9 10; do /usr/bin/time -f "%e %M" "$@" --version 2>&1 >/dev/null | tail -1; done | sort -n | awk -v n=$n '{a[NR]=$1;r[NR]=$2} END{print n, "median_s="a[int((NR+1)/2)], "min_s="a[1], "max_rss_kb="r[NR]}'
