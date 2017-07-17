# Coalescent Simulator for Tumor Evolution (CSiTE)

CSiTE is a Python program for jointly simulating Single Nucleotide Variants (SNVs) and Copy Number Variants (CNVs) for a sample of tumor cells. It takes a coalescent tree (in the newick format) and simulates both types of somatic mutations along the history of the genealogy. At the end of the simulation, the program can output simulated variants (in the setting of a bulk tumor). The program also allows for simulating genotypes of individual tumor cells (i.e. single cell data). 

## Installing

CSiTE is written in Python3 and requires numpy.

CSiTE can be downloaded from github:

    git clone https://github.com/hchyang/CSiTE.git

## Running CSiTE

To run the program, a coalescent tree which captures the ancestral relationships of the tumor cells in a sample is required. The input tree file should be in the newick format, which can be generated by the [ms program](http://home.uchicago.edu/rhudson1/source/mksamples.html) with the `-T` option. ms program has the full-assemblage of the options needed to generate complex demographic histories of the sample. 

The two most important parameters in the simulation is the mutation rate of SNVs (`--snv_rate`) and CNVs (`--cnv_rate`). The mutational events in CSiTE are simulated according to the Poisson process with user specified parameters [see notes for extra discussions].  

Other than the rate of CNVs, there are six other parameters guiding CNVs simulation. 

`--cnv_length_beta` can be used to specify the beta/mean parameter of the exponential distribution (We assume the length of CNVs follows an exponential distribution. This parameter specifies the mean length of the CNV events).

`--cnv_length_max` can be used to set the upper limit of CNVs' length (This will effectively truncate the exponential distribution at this limit). 

`--del_prob` A CNV event can be a deletion or an amplification. Using this parameter, we can specify the probability that a CNV event is a deletion.

`--copy_max` can be used to set the upper bound of an amplification event. When an amplification event happens, it will randomly pick a copy number according to a geometric like distribution with Pr(n+1)=p\*Pr(n). The p parameter can be specified by `-c/--copy_parameter`. The overall distribution will be normalized s.t. the total probability is 1. 

The coalescent tree only describes the polymorphic part of the sample. You can also simulate the truncal part of the tumor evolution (tumorigenesis) through two different approaches: 
a) specify the trunk length e.g. using `--trunk_length`. `--trunk_length` accepts a single float number that can be used as the branch length leading to the root of the coalescent tree.
b) specify the events on the trunk explicitly in a file through `--trunk_vars filename`. The format of the trunk variants file is described in the later section.

When the number of simulated cells is very large, the computational load can become very heavy. Given the fact that most of the mutational events are extremely rare, we implemented a pruning algorithm to trim the tree using `--prune` and `--prune_proportion` options. For example, if you want to simulate the somatic variants of a population containing 1000000 cells, after you setting `--prune 100` or `--prune_proportion 0.0001`, all subtrees with <=100 tips will be trimmed into a tip node, which means there will be no polymorphic variants on those subtrees with <=100 tips. So the tips belonging to the same subtree (with <=100 tips) will show the same genotypes.

Other convenient options including:
- -D/--depth to simulate the variants under different sequencing coverage (i.e. given the specified coverage d, we will simulate a sequence coverage of x, where x is sampled from Poission(d)). 
- -p/--ploidy to set the ploidy of tumor cells to simulate
- -P/--purity to set the purity of tumor sample
- --length to set the length of sequence to simulate

**Note:** By default, the branch length from the ms program is measured in 4N generations. CSiTE will simulate SNVs/CNVs events following the Poisson process. For example, if we set -r 100, this is equivalent to set the population rescaled parameter θ=4Nu as 100 (see ms manual for details). 

### Input files

#### Tree file (-t/--tree)

Tree file should be in newick format, for example:

    ((2:0.083,4:0.083):0.345,(5:0.322,(1:0.030,3:0.030):0.292):0.105);

#### Trunk variants file (--trunk\_vars)

You can simulate truncal variants by specify `--trunk_length`, or import trunk variants directly using `--trunk_vars` option.
The file format of truncal variants is like:
    
    #chr start end copy
    0 1 1 0
    1 12 123 +3
    0 12 123 -1

- **chr**:    which parental copy the variant locates in (0 means one of the parental copy, 1 means the other copy)
- **start**:  the start position of the variant
- **end**:    the end position of the variant
- **copy**:   an integer. 0: SNV, -1: deletion, +int: amplification

P.S. start and end are 0 based. And the region of each variant is similar to the bed file (inclusive on the left, but exclusive on the right end, i.e.[start,end)).

### Output files

#### SNVs file (-S/--snv)

This file contains the frequency information of simulated SNVs. It contains four columns. 
- **position**:        the position (0-based) of SNVs
- **true\_freq**:      the true frequency of the alternative allele in the sample. 
- **total\_depth**:    the simulated total coverage of tumor and normal cells at the position of SNV. 
- **simulated\_freq**: the observed frequency of alternative allele across tumor and normal cell population.

#### Genotype file (--snv\_genotype)

This file contains the snv\_genotype of each tumor cell at SNV loci. Each SNV has one record. The first column is the coordinate of the SNV. Subsequently, there is one column for each tumor cell. The snv\_genotype is in the form of ‘M:N’. M denotes the number of alternative allele and N denotes the number of reference allele.

#### Individual CNV file (--ind\_cnvs)

This file contains the CNVs on each parental copy of each single cell in the sample. There are five clomns in this file:
    
    #sample parental        start   end     copy
    1       0       7912422 7930111 2
    1       1       43110140        43341629        1
    2       0       2255734 2299608 -1
    2       0       22660687        22788472        -1
    2       1       59756841        61142076        3

- **sample**:   the single cell in the sample
- **parental**: which parental copy the variant locates in (0 means one of the parental copy, 1 means another copy, 2 means another copy if your sample is triploid...)
- **start**:    the start position of the CNV
- **end**:      the end position of the CNV
- **copy**:     an integer. -1: deletion, +int: amplification

P.S. start and end are 0 based. And the region of each variant is similar to the bed file (inclusive on the left, but exclusive on the right end, i.e.\[start,end)).

#### CNV profile file (--cnv\_profile)

This file contains the CNV profile across the whole segment. There are 3 columns in this file. The first column is the start of the CNV region, and the second is the end of the CNV region. Both breakpoints are 0-based, defined CNVs covered on [start, end). The last column is the total copies of each region.

#### parental copy file (--parental\_copy)

This file contains the information of parental copy for each SNV. The first column is the coordinate of the SNV, and followed by N columns if the ploidy is N.

#### Log file (-g/--log)

This file contains logging information, e.g. the command line parameters and the random seed used. You can use these information to replicate the simulation. After setting the `--loglevel` as DEBUG, CSiTE will output detailed information about the simulation process. 

### All options

    usage: csite.py [-h] -t TREE [-r SNV_RATE] [-R CNV_RATE] [-d DEL_PROB]
                    [-l CNV_LENGTH_BETA] [-L CNV_LENGTH_MAX] [-c COPY_PARAMETER]
                    [-C COPY_MAX] [-p PLOIDY] [-P PURITY] [-D DEPTH] [-x PRUNE]
                    [-X PRUNE_PROPORTION] [-s RANDOM_SEED] [-S SNV] [-V CNV]
                    [-n NODES_SNVS] [-g LOG] [-G {DEBUG,INFO}]
                    [--cnv_profile CNV_PROFILE] [--snv_genotype SNV_GENOTYPE]
                    [--ind_cnvs IND_CNVS] [--trunk_vars TRUNK_VARS]
                    [--trunk_length TRUNK_LENGTH] [--tree_data TREE_DATA]
                    [--expands EXPANDS] [--length LENGTH] [-v]

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
                            the mean of CNVs length [120000]
      -L CNV_LENGTH_MAX, --cnv_length_max CNV_LENGTH_MAX
                            the maximium of CNVs length [20000000]
      -c COPY_PARAMETER, --copy_parameter COPY_PARAMETER
                            the p parameter of CNVs' copy number distribution
                            [0.5]
      -C COPY_MAX, --copy_max COPY_MAX
                            the maximium ADDITIONAL copy of a CNVs [5]
      -p PLOIDY, --ploidy PLOIDY
                            the ploidy to simulate [2]
      -P PURITY, --purity PURITY
                            the purity of tumor cells in the simulated sample
                            [1.0]
      -D DEPTH, --depth DEPTH
                            the mean depth for simulating coverage data [50]
      -x PRUNE, --prune PRUNE
                            trim all their children for the branches with equal or
                            less than this number of tips [0]
      -X PRUNE_PROPORTION, --prune_proportion PRUNE_PROPORTION
                            trim all their children for the branches with equal or
                            less than this proportion of tips [0.0]
      -s RANDOM_SEED, --random_seed RANDOM_SEED
                            the seed for random number generator [None]
      -S SNV, --snv SNV     the output file to save SNVs [output.snvs]
      -V CNV, --cnv CNV     the output file to save CNVs [output.cnvs]
      -n NODES_SNVS, --nodes_snvs NODES_SNVS
                            the file to save SNVs on each nodes
                            [output.nodes.snvs]
      -g LOG, --log LOG     the log file [log.txt]
      -G {DEBUG,INFO}, --loglevel {DEBUG,INFO}
                            the logging level [DEBUG]
      --cnv_profile CNV_PROFILE
                            the file to save CNVs profile [output.cnv.profile]
      --snv_genotype SNV_GENOTYPE
                            the file to save SNV genotypes for each sample
      --ind_cnvs IND_CNVS   the file to save CNVs for each sample individual
      --trunk_vars TRUNK_VARS
                            the trunk variants file supplied by user
      --trunk_length TRUNK_LENGTH
                            the length of the truncal branch [0]
      --tree_data TREE_DATA
                            the file to dump the tree data [tree.dat]
      --expands EXPANDS     the basename of the file to output the snv and segment
                            data for EXPANDS [None]
      --length LENGTH       the length of the sequence to simulate [100000000]
      -v, --version         show program's version number and exit

### Examples

* Simulate the coalescent tree of a sample of 1000 tumor cells, which are sampled from a exponetially growing tumor. 
(consult the manual of ms for more information)

    `ms 1000 1 -T -G 1 |tail -n1 > ms_tree.txt`

* Simulate the somatic SNVs of these samples. We assume the sequencing depth is 60, and the purity of the sample is 0.8, which means there are 250 normal cells other than these 1000 tumor cells. Other settings are: a) the mutation rate of SNVs and CNVs are 10 and 0.1 respectively; b) the sequence length is 135534747 (chr10 of hg19); c) the cells of the sample are diploid. We save the frequncy of the simulated SNVs to file 'snvs\_freq.txt'.

    `csite.py -t ms_tree.txt -P 0.8 --length 135534747 -r 10 -R 0.1 -D 60 -S snvs_freq.txt`

* There are no truncal muations in the simulation above. If you want to simulate truncal muations, use the option `--trunk_length`.

    `csite.py -t ms_tree.txt -P 0.8 --length 135534747 -r 10 -R 0.1 -D 60 -S snvs_freq.txt --trunk_length 2.0`

* If you want to ignore the variants with the frequency <=0.01, you can use `--prune 20` or `--prune_proportion 0.02` (we use `--prune 20` instead of `--prune 10` for the cells are diploid in the our simulation). These two options can be used to accelerate the simulation when your tree is huge.

    `csite.py -t ms_tree.txt -P 0.8 --length 135534747 -r 10 -R 0.1 -D 60 -S snvs_freq.txt --trunk_length 2.0 --prune 20`

    or

    `csite.py -t ms_tree.txt -P 0.8 --length 135534747 -r 10 -R 0.1 -D 60 -S snvs_freq.txt --trunk_length 2.0 --prune_proportion 0.02`

* If you want to save the SNVs genotypes for each single cell for exactly the same simulation as above, use the options `--snv_genotype` and `--random_seed`.

    `csite.py -t ms_tree.txt -P 0.8 --length 135534747 -r 10 -R 0.1 -D 60 -S snvs_freq.txt --trunk_length 2.0 --prune_proportion 0.02 --snv_geneotype snvs_genotype.txt --random_seed xxxx`

    P.S. The random seed xxxx can be found in the log file of the previous simulation.

## Authors

* [Hechuan Yang](https://github.com/hchyang)

## License

This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details.

