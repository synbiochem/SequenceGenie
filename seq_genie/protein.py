'''
DNA++ (c) DNA++ 2017

All rights reserved.

@author: neilswainston
'''
# pylint: disable=invalid-name
# pylint: disable=no-name-in-module
from collections import defaultdict
from operator import itemgetter
import os
import sys

from Bio.Seq import Seq
from pysal.inequality import gini
from pysam import AlignmentFile

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from seq_genie import utils
from synbiochem.utils import mut_utils


def align(templ_filename, reads_files, filtr=False):
    '''Align sequence files.'''
    align_files = []
    templ_seq = list(utils.parse(templ_filename))[0].seq

    for reads_file in reads_files:
        # Align raw file:
        sam_filename = reads_file + '_raw.sam'
        align_filename = sam_filename
        utils.align(templ_filename, utils.get_reads(reads_file),
                    out=sam_filename,
                    gap_open=12)

        if filtr:
            # Filter indels:
            sam_filt_flename = reads_file + '_filtered.sam'
            align_filename = sam_filt_flename
            utils.reject_indels(sam_filename, templ_seq,
                                out_filename=sam_filt_flename)

        align_files.append(AlignmentFile(align_filename, 'r'))

    return align_files


def analyse_dna_mut(sam_files, templ_seq):
    '''Analyse DNA mutations.'''
    mutations = []

    for sam_file in sam_files:
        vals = []
        mutations.append(vals)

        for read in sam_file:
            if read.alen == len(templ_seq):
                vals.append(len(templ_seq) -
                            sum([(nucl_a == nucl_b)
                                 for (nucl_a, nucl_b)
                                 in zip(read.seq[read.qstart:], templ_seq)]))

    bins = max([val for vals in mutations for val in vals]) - \
        min([val for vals in mutations for val in vals])

    plt.hist(mutations, bins=bins, edgecolor='black',
             label=[os.path.split(sam_file.filename)[1]
                    for sam_file in sam_files])
    plt.title('Mutation counts')
    plt.xlabel('Number of mutations')
    plt.ylabel('Frequency')
    plt.legend()
    plt.show()


def analyse_aa_mut(sam_files, templ_aa_seq):
    '''Analyse amino acid mutations.'''
    muts = [[[] for _ in range(len(templ_aa_seq))]
            for _ in range(len(sam_files))]

    seqs_to_bins = defaultdict(list)

    for sam_idx, sam_file in enumerate(sam_files):
        for read in sam_file:
            mut = _analyse_aa_mut(read, templ_aa_seq)

            if mut:
                if mut[0]:
                    muts[sam_idx][mut[0]].append(mut[1])
                seqs_to_bins[mut[2]].append(sam_idx)

    return muts, seqs_to_bins


def _analyse_aa_mut(read, template_aa):
    '''Analyse amino acid mutations in a single read.'''
    read_dna = Seq(read.seq[read.qstart:read.qend])
    read_aa = read_dna.translate()

    if len(read_aa) == len(template_aa):
        read_muts = {}

        for (pos, aas) in enumerate(zip(read_aa, template_aa)[:-1]):
            if aas[0] != aas[1]:
                read_muts[pos] = aas[0]

        if len(read_muts) == 1:
            return (read_muts.keys()[0], read_muts.values()[0], read_aa)
        elif not read_muts:
            return (None, None, read_aa)

    return None


def plot(data):
    '''Plots mutant counts.'''
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for z, bin_data in enumerate(data):
        xs = np.arange(len(bin_data))
        ys = [len(set(muts)) for muts in bin_data]
        ax.bar(xs, ys, zs=z, zdir='y', alpha=0.8)

    ax.set_xlabel('Residue')
    ax.set_ylabel('Bin number')
    ax.set_zlabel('Number of mutations')

    plt.show()


def get_gini(muts):
    '''Get Gini value for each position.'''
    scores = []
    mut_probs = mut_utils.MutProbs()

    for idx, act_bin in enumerate(muts[1]):
        for mut_res in act_bin:
            if mut_res != '*':
                scores.append(
                    (1 - mut_probs.get_mut_prob(muts[0], mut_res)) * 10**idx)

    return gini.Gini(scores).g if scores else 0


def main(args):
    '''main method.'''
    templ_filename = args[0]
    templ_seq = list(utils.parse(templ_filename))[0].seq
    templ_aa_seq = templ_seq.translate()

    # Align:
    sam_files = align(templ_filename, args[1:], filtr=True)

    # Analyse:
    muts, seqs_to_bins = analyse_aa_mut(sam_files, templ_aa_seq)

    for seq, bins in seqs_to_bins.iteritems():
        seqs_to_bins[seq] = [seq,
                             mut_utils.get_mutations(templ_aa_seq, seq),
                             bins,
                             len(bins),
                             np.mean(bins),
                             np.std(bins)]

    with open('seqs_to_bins.txt', 'w') as outfile:
        for vals in sorted(seqs_to_bins.values(), key=itemgetter(1)):
            outfile.write('\t'.join([str(val) for val in vals]) + '\n')

    with open('mutations_by_pos.txt', 'w') as outfile:
        for idx, vals in enumerate(zip(templ_aa_seq, zip(*muts))):
            outfile.write('\t'.join([str(val)
                                     for val in [idx + 1, vals[0],
                                                 get_gini(vals)] +
                                     list(vals[1])]) + '\n')
    plot(muts)


if __name__ == '__main__':
    main(sys.argv[1:])
