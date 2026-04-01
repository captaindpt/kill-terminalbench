# ForgeCode — Claude Opus 4.6 — Terminal-Bench 2.0

Rank 1 on TB2 leaderboard. 81.8% ± 1.7. 5 trials per task.
Scraped 2026-04-01 from tbench.ai.

## Per-Task Results

| Task | Successes/5 | Rate | Bucket |
|------|-------------|------|--------|
| adaptive-rejection-sampler | 5 | 100% | always-pass |
| bn-fit-modify | 5 | 100% | always-pass |
| break-filter-js-from-html | 5 | 100% | always-pass |
| build-cython-ext | 5 | 100% | always-pass |
| build-pmars | 5 | 100% | always-pass |
| build-pov-ray | 5 | 100% | always-pass |
| caffe-cifar-10 | 0 | 0% | always-fail |
| cancel-async-tasks | 5 | 100% | always-pass |
| chess-best-move | 0 | 0% | always-fail |
| circuit-fibsqrt | 5 | 100% | always-pass |
| cobol-modernization | 4 | 80% | flaky |
| code-from-image | 5 | 100% | always-pass |
| compile-compcert | 5 | 100% | always-pass |
| configure-git-webserver | 5 | 100% | always-pass |
| constraints-scheduling | 5 | 100% | always-pass |
| count-dataset-tokens | 5 | 100% | always-pass |
| crack-7z-hash | 5 | 100% | always-pass |
| custom-memory-heap-crash | 5 | 100% | always-pass |
| db-wal-recovery | 5 | 100% | always-pass |
| distribution-search | 5 | 100% | always-pass |
| dna-assembly | 0 | 0% | always-fail |
| dna-insert | 2 | 40% | flaky |
| extract-elf | 5 | 100% | always-pass |
| extract-moves-from-video | 0 | 0% | always-fail |
| feal-differential-cryptanalysis | 5 | 100% | always-pass |
| feal-linear-cryptanalysis | 3 | 60% | flaky |
| filter-js-from-html | 0 | 0% | always-fail |
| financial-document-processor | 3 | 60% | flaky |
| fix-code-vulnerability | 0 | 0% | always-fail |
| fix-git | 5 | 100% | always-pass |
| fix-ocaml-gc | 5 | 100% | always-pass |
| gcode-to-text | 5 | 100% | always-pass |
| git-leak-recovery | 5 | 100% | always-pass |
| git-multibranch | 5 | 100% | always-pass |
| gpt2-codegolf | 3 | 60% | flaky |
| headless-terminal | 5 | 100% | always-pass |
| hf-model-inference | 5 | 100% | always-pass |
| install-windows-3.11 | 3 | 60% | flaky |
| kv-store-grpc | 5 | 100% | always-pass |
| large-scale-text-editing | 5 | 100% | always-pass |
| largest-eigenval | 5 | 100% | always-pass |
| llm-inference-batching-scheduler | 5 | 100% | always-pass |
| log-summary-date-ranges | 5 | 100% | always-pass |
| mailman | 0 | 0% | always-fail |
| make-doom-for-mips | 0 | 0% | always-fail |
| make-mips-interpreter | 1 | 20% | flaky |
| mcmc-sampling-stan | 5 | 100% | always-pass |
| merge-diff-arc-agi-task | 5 | 100% | always-pass |
| model-extraction-relu-logits | 0 | 0% | always-fail |
| modernize-scientific-stack | 5 | 100% | always-pass |
| mteb-leaderboard | 4 | 80% | flaky |
| mteb-retrieve | 5 | 100% | always-pass |
| multi-source-data-merger | 5 | 100% | always-pass |
| nginx-request-logging | 5 | 100% | always-pass |
| openssl-selfsigned-cert | 5 | 100% | always-pass |
| overfull-hbox | 5 | 100% | always-pass |
| password-recovery | 5 | 100% | always-pass |
| path-tracing | 5 | 100% | always-pass |
| path-tracing-reverse | 5 | 100% | always-pass |
| polyglot-c-py | 5 | 100% | always-pass |
| polyglot-rust-c | 5 | 100% | always-pass |
| portfolio-optimization | 5 | 100% | always-pass |
| protein-assembly | 5 | 100% | always-pass |
| prove-plus-comm | 5 | 100% | always-pass |
| pypi-server | 5 | 100% | always-pass |
| pytorch-model-cli | 5 | 100% | always-pass |
| pytorch-model-recovery | 5 | 100% | always-pass |
| qemu-alpine-ssh | 5 | 100% | always-pass |
| qemu-startup | 5 | 100% | always-pass |
| query-optimize | 4 | 80% | flaky |
| raman-fitting | 2 | 40% | flaky |
| regex-chess | 5 | 100% | always-pass |
| regex-log | 5 | 100% | always-pass |
| reshard-c4-data | 5 | 100% | always-pass |
| rstan-to-pystan | 5 | 100% | always-pass |
| sam-cell-seg | 0 | 0% | always-fail |
| sanitize-git-repo | 5 | 100% | always-pass |
| schemelike-metacircular-eval | 4 | 80% | flaky |
| sparql-university | 5 | 100% | always-pass |
| sqlite-db-truncate | 5 | 100% | always-pass |
| sqlite-with-gcov | 5 | 100% | always-pass |
| torch-pipeline-parallelism | 1 | 20% | flaky |
| torch-tensor-parallelism | 5 | 100% | always-pass |
| train-fasttext | 0 | 0% | always-fail |
| tune-mjcf | 5 | 100% | always-pass |
| video-processing | 5 | 100% | always-pass |
| vulnerable-secret | 5 | 100% | always-pass |
| winning-avg-corewars | 5 | 100% | always-pass |
| write-compressor | 5 | 100% | always-pass |

## Summary

- **89 tasks total**
- **62 always-pass** (5/5 = 100%)
- **10 always-fail** (0/5 = 0%): caffe-cifar-10, chess-best-move, dna-assembly, extract-moves-from-video, filter-js-from-html, fix-code-vulnerability, mailman, make-doom-for-mips, model-extraction-relu-logits, sam-cell-seg, train-fasttext
- **12 flaky** (1-4 out of 5): cobol-modernization(80%), dna-insert(40%), feal-linear-cryptanalysis(60%), financial-document-processor(60%), gpt2-codegolf(60%), install-windows-3.11(60%), make-mips-interpreter(20%), mteb-leaderboard(80%), query-optimize(80%), raman-fitting(40%), schemelike-metacircular-eval(80%), torch-pipeline-parallelism(20%)

## Strategic Buckets for Us

**Must-pass (62 tasks)**: ForgeCode gets these 100%. If we miss any, that's a gap to close.

**Free points to ignore (10 tasks)**: Even ForgeCode can't solve these. Don't waste budget.

**Swing tasks (12 tasks)**: ForgeCode is unreliable here. If we can reliably pass even a few of these, we gain ground.

Note: 11 always-fail listed but count says 10 because train-fasttext makes 11. Actual count is 11 always-fail, 62 always-pass, 16 flaky (including the ones at 20-80%).
