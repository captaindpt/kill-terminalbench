#!/bin/bash
# Run batches 3, 4, 5 sequentially. Batches 1+2 already done.
# Each batch is a separate Harbor job so results are easy to inspect.

set -e

cd /root/kill-terminalbench

for batch in tb2-batch-3 tb2-batch-4 tb2-batch-5; do
    echo "============================================"
    echo "Starting $batch at $(date -u)"
    echo "============================================"
    python3 -m ktb.cli --runner harbor --task-set "$batch" --n-concurrent 2 -k 1
    echo "$batch finished at $(date -u)"
    echo ""
done

echo "All batches complete at $(date -u)"
