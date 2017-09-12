#!/usr/bin/env python3

#########################################################################
# Author: Hechuan
# Created Time: 2017-04-04 18:00:34
# File Name: csite.py
# Description: 
#########################################################################

import sys
import pickle
import numpy
import argparse
import logging
import csite.trunk_vars
import csite.tree
import re
import os

#handle the error below
#python | head == IOError: [Errno 32] Broken pipe 
from signal import signal, SIGPIPE, SIG_DFL 
signal(SIGPIPE,SIG_DFL) 

#TODO: SNV true_freq
#rewrite the description of the output of SNVs 

__version__='0.8.0'

def check_seed(value=None):
    ivalue=int(value)
#2**32: Must be convertible to 32 bit unsigned integers.
    if not 0<=ivalue<=4294967296: 
        raise argparse.ArgumentTypeError("{} is an invalid value for random seed. ".format(value)+
            "It should be an interger between 0 and 4294967296.")
    return ivalue

def check_prune(value=None):
    ivalue=int(float(value))
    if ivalue<2: 
        raise argparse.ArgumentTypeError("{} is an invalid value for prune. ".format(value)+
            "It should be an interger >=2 and <=the number of leaves of the tree.")
    return ivalue

def check_proportion(value=None):
    fvalue=float(value)
    if not 0<=fvalue<=1: 
        raise argparse.ArgumentTypeError("{} is an invalid value for prune proportion. ".format(value)+
            "It should be an float between 0 and 1.")
    return fvalue

def check_folder(directory=None):
    good_charactors=re.compile('^[0-9a-zA-Z_-]+$') 
    if not good_charactors.match(directory):
        raise argparse.ArgumentTypeError("{} is an invalid string for --genome. ".format(directory)+
            "Please only use number, alphabet, - and _ in the directory name.")
    if os.path.exists(directory):
        raise argparse.ArgumentTypeError("{} is already exist. Delete it or use another name instead.".format(directory))
    return directory
    
def check_max_cnv_length(seq_length=None,max_cnv_length=None):
    if max_cnv_length>seq_length:
         raise argparse.ArgumentTypeError("The value of -L/--cnv_length_max "+
            "({}) should NOT be larger than --length ({}).".format(max_cnv_length,seq_length))

def cn_dist(copy_max=None,copy_parameter=None):
    '''
    When an amplification event happens, it will randomly pick a copy number according to a geometric like distribution,
    Pr(n+1)=p*Pr(n).
    This function returns the configure of the distribution of CNVs' copy number.
    '''
    cn_dist_cfg={}
    cn_dist_cfg['copy']=[x for x in range(1,copy_max+1)]
    w=1/sum([copy_parameter**x for x in range(copy_max)])
    scale=sum([w*copy_parameter**x for x in range(copy_max)])
    cn_dist_cfg['prob']=[(w*copy_parameter**x)/scale for x in range(copy_max)]
    return cn_dist_cfg

#use kernprof -l -v script.py to profile
#@profile
def main():
    parse=argparse.ArgumentParser(
        description='Simulate SNVs/CNVs on a coalescent tree in newick format')
    parse.add_argument('-t','--tree',required=True,
        help='a tree in newick format')
    default='1'
    parse.add_argument('-n','--name',type=str,default=default,
        help='the name of the sequence to be simulated [{}]'.format(default))
    default=300
    parse.add_argument('-r','--snv_rate',type=float,default=default,
        help='the muation rate of SNVs [{}]'.format(default))
    default=3
    parse.add_argument('-R','--cnv_rate',type=float,default=default,
        help='the muation rate of CNVs [{}]'.format(default))
    default=0.5
    parse.add_argument('-d','--del_prob',type=int,default=default,
        help='the probability of being deletion for a CNV mutation [{}]'.format(default))
#https://en.wikipedia.org/wiki/Copy-number_variation
    default=20000000
    parse.add_argument('-l','--cnv_length_beta',type=int,default=default,
        help='the mean of CNVs length [{}]'.format(default))
    default=40000000
    parse.add_argument('-L','--cnv_length_max',type=int,default=default,
        help='the maximium of CNVs length [{}]'.format(default))
    default=0.5
    parse.add_argument('-c','--copy_parameter',type=float,default=default,
        help="the p parameter of CNVs' copy number distribution [{}]".format(default))
    default=5
    parse.add_argument('-C','--copy_max',type=int,default=default,
        help='the maximium ADDITIONAL copy of a CNVs [{}]'.format(default))
    default=2
    parse.add_argument('-p','--ploidy',type=int,default=default,
        help='the ploidy to simulate [{}]'.format(default))
    default=1.0
    parse.add_argument('-P','--purity',type=float,default=default,
        help="the purity of tumor cells in the simulated sample [{}]".format(default))
    default=50
    parse.add_argument('-D','--depth',type=int,default=default,
        help='the mean depth for simulating coverage data [{}]'.format(default))
    default=0
    parse.add_argument('-x','--prune',type=check_prune,default=default,
        help='trim all the children of the nodes with equal or less than this number of tips [{}]'.format(default))
    default=0.0
    parse.add_argument('-X','--prune_proportion',type=check_proportion,default=default,
        help='trim all the children of the nodes with equal or less than this proportion of tips [{}]'.format(default))
    default=None
    parse.add_argument('-s','--random_seed',type=check_seed,
        help='the seed for random number generator [{}]'.format(default))
    default='output.snvs'
    parse.add_argument('-S','--snv',type=str,default=default,
        help='the output file to save SNVs [{}]'.format(default))
    default='output.cnvs'
    parse.add_argument('-V','--cnv',type=str,default=default,
        help='the output file to save CNVs [{}]'.format(default))
    default='output.nodes_vars'
    parse.add_argument('-N','--nodes_vars',type=str,default=default,
        help='the output file to save SNVs/CNVs on each node [{}]'.format(default))
    default='output.named_tree.nhx'
    parse.add_argument('-T','--named_tree',type=str,default=default,
        help='the output file in NHX format to save the tree with all nodes named [{}]'.format(default))
    default='log.txt'
    parse.add_argument('-g','--log',type=str,default=default,
        help='the log file [{}]'.format(default))
    default='INFO'
    parse.add_argument('-G','--loglevel',type=str,default=default,choices=['DEBUG','INFO'],
        help='the logging level [{}]'.format(default))
    default='output.cnv.profile'
    parse.add_argument('--cnv_profile',type=str,default=default,
        help='the file to save CNVs profile [{}]'.format(default))
    parse.add_argument('--snv_genotype',type=str,
        help='the file to save SNV genotypes for each cell')
    parse.add_argument('--ind_cnvs',type=str,
        help='the file to save CNVs for each cell individual')
    parse.add_argument('--parental_copy',type=str,
        help='the file to save parental copy for each SNV')
    parse.add_argument('--trunk_vars',type=str,
        help='the trunk variants file supplied by user')
    default=0
    parse.add_argument('--trunk_length',type=float,
        help='the length of the truncal branch [{}]'.format(default))
    default=None
    parse.add_argument('--expands',type=str,default=default,
        help='the basename of the file to output the snv and segment data for EXPANDS [{}]'.format(default))
    default=100000000
    parse.add_argument('--length',type=int,default=default,
        help='the length of the sequence to simulate [{}]'.format(default))
    default=None
    parse.add_argument('--genome',type=check_folder,default=default,
        help='the directory to output the perturbed genome for each sample [{}]'.format(default))
    parse.add_argument('-v','--version',action='version',version=__version__)
    args=parse.parse_args()

    check_max_cnv_length(args.length,args.cnv_length_max)

    logging.basicConfig(filename=args.log, filemode='w',
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%m-%d %H:%M:%S',level=args.loglevel)
    logging.info(' Command: %s',' '.join(sys.argv))
    if args.random_seed==None:
#2**32: Must be convertible to 32 bit unsigned integers.
        seed=numpy.random.randint(4294967296) 
    else:
        seed=args.random_seed
    logging.info(' Random seed: %s',seed)
    numpy.random.seed(seed)

    with open(args.tree) as input:
        for line in input:
            newick=line.rstrip()
            mytree=csite.tree.newick2tree(newick)
            if args.trunk_length:
                mytree.lens=args.trunk_length
            leaves_number=mytree.leaves_counting()
            leaves_names=sorted(mytree.leaves_naming())
            if args.prune>0:
                if args.prune>leaves_number:
                    raise argparse.ArgumentTypeError("There are only {} leaves on the tree. It's impossible to prune {} leaves.".format(
                        leaves_number,args.prune))
                if args.prune>=2:
                    mytree.prune(tips=args.prune)
            elif args.prune_proportion>0.0:
                trim=leaves_number*args.prune_proportion
                if trim>=2:
                    mytree.prune(tips=trim)
#output the map of tip_node:leaf
            if args.genome:
                tip_leaves=mytree.tip_node_leaves()
                os.mkdir(args.genome,mode=0o755)
                with open(args.genome+'/tip_node_sample.map','w') as tip_leaves_f:
                    tip_leaves_f.write('#tip_node\tsample\n')
                    for tip_node in sorted(tip_leaves.keys()):
                        for leaf in sorted(tip_leaves[tip_node]):
                            tip_leaves_f.write('node{}\t{}\n'.format(tip_node,leaf))
#trunk vars
            trunk_snvs={}
            trunk_cnvs={}
            if args.trunk_vars!=None:
                trunk_snvs,trunk_cnvs=csite.trunk_vars.classify_vars(
                    args.trunk_vars,args.ploidy,args.length,leaves_number,mytree)

            cn_dist_cfg=cn_dist(copy_max=args.copy_max,copy_parameter=args.copy_parameter)
            
            (snvs_freq,cnvs,cnv_profile,nodes_snvs,tree_with_snvs,
                leaf_snv_alts,leaf_snv_refs,leaf_cnvs,
                hap_local_copy_for_all_snvs,
                )=mytree.snvs_freq_cnvs_profile(
                ploidy=args.ploidy,
                snv_rate=args.snv_rate,
                cnv_rate=args.cnv_rate,
                del_prob=args.del_prob,
                cnv_length_beta=args.cnv_length_beta,
                cnv_length_max=args.cnv_length_max,
                cn_dist_cfg=cn_dist_cfg,
                trunk_snvs=trunk_snvs,
                trunk_cnvs=trunk_cnvs,
                purity=args.purity,
                length=args.length,
                genome=args.genome,
                chroms=args.name,
                )

            if args.snv_genotype!=None:
                genotype_file=open(args.snv_genotype,'w')
                genotype_file.write('{}\t{}\n'.format('#positon','\t'.join(leaves_names)))
                for snv in snvs_freq:
                    genotype_file.write('{}\t{}\n'.format(snv[0],
                        '\t'.join([str(leaf_snv_alts[leaf][snv[0]])+':'+str(leaf_snv_refs[leaf][snv[0]]) for leaf in leaves_names])))

            if args.ind_cnvs!=None:
                ind_cnvs_file=open(args.ind_cnvs,'w')
                ind_cnvs_file.write('#cell\tparental\tstart\tend\tcopy\n')
                for leaf in sorted(leaf_cnvs.keys()):
                    for cnv in leaf_cnvs[leaf]:
                        ind_cnvs_file.write('{}\n'.format('\t'.join([str(x) for x in [leaf,cnv['parental'],cnv['start'],cnv['end'],cnv['copy']]])))

            if args.parental_copy!=None:
                parental_copy_file=open(args.parental_copy,'w')
                parental_copy_file.write('#position\t{}\n'.format('\t'.join(['haplotype'+str(x) for x in range(args.ploidy)])))
                for snv in hap_local_copy_for_all_snvs:
                    parental_copy_file.write('\t'.join([str(x) for x in snv])+'\n')

            cnv_file=open(args.cnv,'w')
            for cnv in cnvs:
                cnv_file.write('{}\t{}\t{}\t{}\t{}\t{}\n'.format(cnv['seg'],cnv['start'],cnv['end'],cnv['copy'],cnv['leaves_count'],cnv['pre_snvs']))

            snv_file=open(args.snv,'w')
            snv_file.write('#position\ttrue_freq\ttotal_depth\tsimulated_freq\n')
            for pos,freq in snvs_freq:
                total_dp,b_allele_dp=csite.tree.simulate_sequence_coverage(args.depth,freq)
                b_allele_freq=0
                if total_dp!=0:
                    b_allele_freq=b_allele_dp/total_dp
                snv_file.write('{}\t{}\t{}\t{}\n'.format(pos,freq,total_dp,b_allele_freq))

            cnv_profile_file=open(args.cnv_profile,'w')
            for seg in cnv_profile:
                cnv_profile_file.write('{}\t{}\t{}\n'.format(*seg))

#FIXME: output SNVs/CNVs, not only SNVs
            nodes_snvs_file=open(args.nodes_vars,'w')
            for node in sorted(nodes_snvs.keys()):
                for snv in sorted(nodes_snvs[node]):
                    nodes_snvs_file.write('{}\t{}\n'.format(node,snv))

#TODO: Should we change pickle to json or yaml?
#http://stackoverflow.com/questions/4677012/python-cant-pickle-type-x-attribute-lookup-failed
            tree_data_file=open(args.named_tree,'wb')
            #pickle.dump(tree_with_snvs,tree_data_file)

            if args.expands != None:
#output for expands
                expands_snps_file=open(args.expands+'.snps','w')
                expands_snps_file.write('chr\tstartpos\tAF_Tumor\tPN_B\n')
                chroms=args.name
                for pos,freq in snvs_freq:
                    total_dp,b_allele_dp=csite.tree.simulate_sequence_coverage(args.depth,freq)
                    expands_snps_file.write('{}\t{}\t{}\t{}\n'.format(chroms,pos,b_allele_dp/total_dp,0))

#in the segment input for expands
#CN_Estimate - the copy number estimated for each segment (average value across all subpopulations in the sample)
                expands_segs_file=open(args.expands+'.segs','w')
                expands_segs_file.write("chr\tstartpos\tendpos\tCN_Estimate\n")
                for start,end,copy in cnv_profile:
                    expands_segs_file.write('{}\t{}\t{}\t{}\n'.format(chroms,start,end,copy/leaves_number))

