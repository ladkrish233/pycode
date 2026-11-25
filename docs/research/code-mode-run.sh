for p in "$@"; do
 for i in 1 2 3 4 5 6 7; do ANTHROPIC_API_KEY=x OPENAI_API_KEY=x PYDANTIC_AI_NO_BANNER=1 v/bin/python -I probes/$p.py 2>&1 | tail -1; done | sort -n | awk -v n=$p '{a[NR]=$1;r[NR]=$2;h[NR]=$3;m=$4} END{print n, "ms="a[4], "rss_kb="r[4], "hwm_kb="h[4], "mods="m}'
done
