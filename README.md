# PhyloVars

PhyloVars is a Python program for simulating somatic mutations in a population of tumor cells. By being fed with a phylogenetic tree in newick format, it can simulate both SNVs and CNVs on it, and reports the coordinates and frequency of each variant.

## Installing

PhyloVars is written in Python3, and numpy is the only pakage which is not included in the standard library of Python3.

PhyloVars can be downloaded from github:

    git clone git@github.com:hchyang/phyloVars.git

## Running PhyloVars

PhyloVar is easy to use. To run the program, a coalescent tree, which illustrates the phylogenetic relationship of the tumor cells in your sample and the the coalescent time leading to each node, is required.
The input tree file should be in newick format, which can be generated by [ms](http://home.uchicago.edu/rhudson1/source/mksamples.html) program using `-T` option. ms is a very powerful tool used in population genetics. Different population history can be simulated using its abundant parameters. Leveraging the power of ms, PhyloVars can provide two main somatic variants (SNVs and CNVs) generated under different tumor growth history.

According to the mutation rate of SNVs(`--snv_rate`)/CNVs(`--cnv_rate`) and the length of each branch of the given tree, PhyloVar simulates SNVs/CNVs events randomly under possion process. Like the theta parameter in ms (`-t`), the mutation rate of SNVs and CNVs are specified in the form of θ = (4Nμ) , where N is the diploid population size and μ is the SNVs/CNVs mutation rate for the entire sequence.

There are also four other parameters for CNVs simulation. We suppose the length of CNVs are under exponential distribution. `--cnv_length_beta` can be used to specify the beta/scale parameter of that exponential distribution. `--cnv_length_max` can be used to set the upper limit of CNVs' length. A CNV event can be a deletion or an amplification. Using the `--del_prob` parameter, you can specify the expected proportion of deletions in CNVs. The last parameter of CNV simulation, `--copy_max`,  can be used to set the upper boundary of a uniform distribution of amplifications' additional copies.

Because there are no branch leading to the root of coalescent trees, by default, all mutations are intratumor variants. If you want to simulate trunk mutations, you can try `--trunk_length` and `--trunk_vars` parameters. `--trunk_length` accepts a float number that can be used as the branch length leading to the root of the coalescent tree. Another way, you can specify trunk CNVs/SNVs explicity in a file, and then supply it to `--trunk_vars`. The format of the trunk variants file can be found in later section.

In PhyloVar, for each new copy of an amplification, the program will create a new subtree to simulate the varaints on it. This operation is heavy when the tree gets bigger. But most of the time, we only care about the variants with a frequency higher than a basline cutoff in that situation. So we implement two options, `--prune` and `--prune_proportion`, to prune the larger tree.

### Input files

#### Tree file (-t/--tree)

Tree file should be in newick format:

    ((2:0.083,4:0.083):0.345,(5:0.322,(1:0.030,3:0.030):0.292):0.105);

#### Trunk variants file (--trunk_vars)

You can simulate trunk variants by specify `--trunk_length`, or import trunk variants directly (`--trunk_vars`).
The file format of trunk variants is like:
    
    #chr start end copy
    0 1 1 0
    1 12 123 +3
    0 12 123 -1

- **chr**:    which copy of chrs the var locates in (0 based)
- **start**:  the start of the var
- **end**:    the end of the var
- **copy**:   an interger. 0: SNV, -1: deletion, +int: amplification

P.S. start and end are 0 based. And the region of each var is like in bed: [start,end).

### Output files

#### SNVs file (-S/--snv)

This file saves the frequency information of simulated SNVs. It contains two columns. The first column is the SNV position (0-based), and the second one is the observed frequency across tumor cell population.

#### CNV profile file (-p/--cnv_profile)

This file contains the CNV profile across the whole sequence. There are 3 columns in this file. The first column is the start of CNV regions, and the second is the end of CNV regions. Both breakpoints are 0-based, defined CNVs covered on [start, end). The last column is the total copies of each region.

#### Log file (-g/--log)

This file contains logging information, e.g. the command line information and the random seed used. After setting the `--loglevel` as DEBUG, PhyloVar will output lots of detailed information during the simulation process. 

### All options

    usage: simulate_somatic_vars.py [-h] -t TREE [-r SNV_RATE] [-R CNV_RATE]
                                    [-d DEL_PROB] [-l CNV_LENGTH_BETA]
                                    [-L CNV_LENGTH_MAX] [-c COPY_MAX] [-p PLOID]
                                    [-x PRUNE] [-X PRUNE_PROPORTION] [-D DEPTH]
                                    [-s RANDOM_SEED] [-V CNV] [-S SNV]
                                    [-P CNV_PROFILE] [-n NODES_SNVS] [-g LOG]
                                    [--loglevel {DEBUG,INFO}]
                                    [--trunk_vars TRUNK_VARS]
                                    [--trunk_length TRUNK_LENGTH]
                                    [--tree_data TREE_DATA] [--expands EXPANDS]
                                    [--length LENGTH]

    Simulate SNVs/CNVs on a coalescent tree in newick format

    optional arguments:
      -h, --help            show this help message and exit
      -t TREE, --tree TREE  a tree in newick format
      -r SNV_RATE, --snv_rate SNV_RATE
                            the muation rate of SNVs [300]
      -R CNV_RATE, --cnv_rate CNV_RATE
                            the muation rate of CNVs [3]
      -d DEL_PROB, --del_prob DEL_PROB
                            the probability of being deletion for a CNV mutation
                            [0.5]
      -l CNV_LENGTH_BETA, --cnv_length_beta CNV_LENGTH_BETA
                            the mean of CNVs length [4000000]
      -L CNV_LENGTH_MAX, --cnv_length_max CNV_LENGTH_MAX
                            the maximium of CNVs length [20000000]
      -c COPY_MAX, --copy_max COPY_MAX
                            the maximium ADDITIONAL copy of a CNVs [5]
      -p PLOID, --ploid PLOID
                            the ploid to simulate [2]
      -x PRUNE, --prune PRUNE
                            trim all their children for the branches with equal or
                            less than this number of tips [0]
      -X PRUNE_PROPORTION, --prune_proportion PRUNE_PROPORTION
                            trim all their children for the branches with equal or
                            less than this proportion of tips [0.0]
      -D DEPTH, --depth DEPTH
                            the mean depth for simulating coverage data [50]
      -s RANDOM_SEED, --random_seed RANDOM_SEED
                            the seed for random number generator [None]
      -V CNV, --cnv CNV     the output file to save CNVs [raw.cnvs]
      -S SNV, --snv SNV     the output file to save SNVs [raw.snvs]
      -P CNV_PROFILE, --cnv_profile CNV_PROFILE
                            the file to save CNVs profile [cnv.profile]
      -n NODES_SNVS, --nodes_snvs NODES_SNVS
                            the file to save SNVs on each nodes [nodes.snvs]
      -g LOG, --log LOG     the log file [log.txt]
      --loglevel {DEBUG,INFO}
                            the logging level [DEBUG]
      --trunk_vars TRUNK_VARS
                            the trunk variants file
      --trunk_length TRUNK_LENGTH
                            the trunk length [0]
      --tree_data TREE_DATA
                            the file to dump the tree data [tree.dat]
      --expands EXPANDS     the basename of the file to output the snv and segment
                            data for EXPANDS [None]
      --length LENGTH       the length of the sequence to simulate [100000000]

## Authors

* [Hechuan Yang](https://github.com/hchyang)

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
