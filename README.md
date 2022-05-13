### Overview

This page describes research artifacts for the following research publication:

**Co-opting Linux Processes for High-Performance Network Simulation**  
_Proceedings of [the 2022 USENIX Annual Technical Conference](https://www.usenix.org/conference/atc22) (ATC 2022)_  
by [Rob Jansen](https://www.robgjansen.com), [Jim Newsome](https://github.com/sporksmith), and [Ryan Wails](https://ryanwails.com/)  
<!--\[[Conference version](https://www.robgjansen.com/publications/netsim-atc2022.pdf)\]-->

If you reference this paper or use any of the data or code provided on this
site, please cite the paper. Here is a bibtex entry for latex users:

```
@inproceedings{netsim-atc2022,
  author = {Rob Jansen and Jim Newsome and Ryan Wails},
  title = {Co-opting Linux Processes for High-Performance Network Simulation},
  booktitle = {USENIX Annual Technical Conference},
  year = {2022},
  note = {See also \url{https://netsim-atc2022.github.io}},
}
```

### Contents

Our artifact has multiple dimensions. We contribute new **software** (which has
already been merged into an existing open-source project), **simulation inputs**
(configuration files and scripts) that can be used to re-run our experiments,
**simulation outputs** (data files extracted from our simulations), and
**analysis scripts** that can be used to process our simulation data and
reproduce the graphs in our paper.

We have broken our artifact into multiple parts, each of which are described
on its own subpage of this site:

  1. [The simulator page](/simulator) describes an open-source software tool
  2. [The benchmarks page](/benchmarks) describes how to reproduce our benchmark experiments
  3. [The tor page](/tor) describes how to reproduce our Tor network experiments
