#!/bin/bash
# Retry ALL failed tasks from batches 1-5.
# Changes since last run:
#   - Adaptive thinking with effort control (max on early episodes + after failures)
#   - 6 CPUs, 16GB RAM per container (was 1 CPU, 2GB)
#   - n=1 (no concurrency — eliminates container contention)
#   - command_timeout=700 (already in code)
#
# Verifier fails first (benefit from new thinking), then errors (benefit from resources).
# 47 tasks total.

set -e
cd /root/kill-terminalbench

echo "============================================"
echo "Retry run: verifier fails (17 tasks)"
echo "Started at $(date -u)"
echo "============================================"

python3 -m ktb.cli \
    --runner harbor \
    --n-concurrent 1 \
    --override-cpus 6 \
    --override-memory-mb 16000 \
    -k 1 \
    --tasks \
    bn-fit-modify \
    build-cython-ext \
    build-pmars \
    configure-git-webserver \
    count-dataset-tokens \
    dna-assembly \
    dna-insert \
    extract-elf \
    feal-linear-cryptanalysis \
    filter-js-from-html \
    git-leak-recovery \
    git-multibranch \
    mteb-leaderboard \
    mteb-retrieve \
    protein-assembly \
    schemelike-metacircular-eval \
    sqlite-with-gcov

echo ""
echo "============================================"
echo "Retry run: errors/timeouts (30 tasks)"
echo "Started at $(date -u)"
echo "============================================"

python3 -m ktb.cli \
    --runner harbor \
    --n-concurrent 1 \
    --override-cpus 6 \
    --override-memory-mb 16000 \
    -k 1 \
    --tasks \
    adaptive-rejection-sampler \
    build-pov-ray \
    caffe-cifar-10 \
    cobol-modernization \
    crack-7z-hash \
    db-wal-recovery \
    extract-moves-from-video \
    fix-ocaml-gc \
    gcode-to-text \
    gpt2-codegolf \
    install-windows-3.11 \
    llm-inference-batching-scheduler \
    make-doom-for-mips \
    merge-diff-arc-agi-task \
    model-extraction-relu-logits \
    password-recovery \
    path-tracing \
    path-tracing-reverse \
    pytorch-model-recovery \
    raman-fitting \
    regex-chess \
    regex-log \
    rstan-to-pystan \
    sam-cell-seg \
    torch-tensor-parallelism \
    train-fasttext \
    tune-mjcf \
    video-processing \
    winning-avg-corewars \
    write-compressor

echo ""
echo "All retries complete at $(date -u)"
