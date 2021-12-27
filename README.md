# voyager-analysis
Analysis of the Voyager data prefetcher model, and SPEC-06 / GAP traces.

> Zhan Shi, Akanksha Jain, Kevin Swersky, Milad Hashemi, Parthasarathy Ranganathan, and Calvin Lin. 2021. A hierarchical neural model of data prefetching. In Proceedings of the 26th ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS 2021). Association for Computing Machinery, New York, NY, USA, 861–873. DOI:https://doi.org/10.1145/3445814.3446752

> John L. Henning. 2006. SPEC CPU2006 benchmark descriptions. ACM SIGARCH Computer Architecture News 34.4, 1-17.

> Scott Beamer, Krste Asanović, and David Patterson. 2015. The GAP benchmark suite. arXiv preprint arXiv:1508.03619. https://arxiv.org/abs/1508.03619



## Notebooks
Jupyter notebooks to analyze results collected from ChampSim and trace analysis.

## data
Collected data so far.

## corr
Scripts to determine correlelations with the next address.
- `correlation_load`: Given an LLC load trace, determine the correlation between triggers (i.e. a history of PC-localized load addresses) and the next PC-localized load address. A good trigger will have high separability, i.e. for that trigger, most (or all) of the following loads are to one address.

## prefetch
Scripts to generate and analyze prefetch traces.
- `bo`: Build a prefetch trace for an LLC BO prefetcher. (*Note*: Not currently accurate, as this BO runs on all LLC loads instead of just misses/prefetched hits.)
- `sisb`: Build a prefetch trace for an idealized ISB prefetcher.
- `pc_sisb`: Build a prefetch trace for a PC-localized, idealized ISB prefethcer.
- `generate_pc`: Build a prefetch trace for an optimal next-load prefetcher.
- `diff`: Calculate the differences between two prefetch traces. Unified accuracy-coverage can be calculated as `(1 - diff12) * 100` %.
- `diff_sweep`: Calculate the differences between an optimal next-load prefetcher and several prefetchers, on one machine (using multiple processes).

## trace
Scripts to parse, build, and verify traces.
- `loadbranch_trace`: Build a *load-branch* trace, which is an LLC load trace with each load's *n* prior branch PCs and decisions attached.
- `match_traces`: Verify that all instructions in LLC load trace appear in a ChampSim trace and match correctly.
- `match_traces_branch`: Verify that all instructions in LLC load trace appear in a ChampSim trace and match correctly, while also reporting each load's *n* prior branch PCs and decisions.
- `parse_champsim_trace`: Decode the first *m* instructions of a ChampSim trace, and print them to the terminal.

## utils
- Helper functions to assist other scripts/notebooks.

