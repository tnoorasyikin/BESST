'''
Created on Jul 25, 2013

@author: ksahlin
'''
import argparse
import os
import subprocess
import sys
import tempfile

import pysam

##
# Converts a sam file to a bam file using pysam.
#
# @param sam_path Path of the .sam file.
# @param bam_path Path of the resulting .bam file.
#
def sam_to_bam(sam_path, bam_path):
    sam_file = pysam.Samfile(sam_path, "r")
    bam_file = pysam.Samfile(bam_path, "wb", template=sam_file)

    for alignment in sam_file:
        bam_file.write(alignment)

##
# Maps the given paired end reads using bwa, and writes a
# sorted .bam file in the given output file.
#
# @param pe1_path Path of the first reads.
# @param pe2_path Path of the second reads.
# @param genome_path Path to the reference genome.
# @param output_path Path of the output file without extension ".bam".
#
def map_paired_reads(pe1_path, pe2_path, genome_path, output_path):
    work_dir = tempfile.mkdtemp()
    genome_db = os.path.join(work_dir, "genome")
    pe1_output = os.path.join(work_dir, "pe1.sai")
    pe2_output = os.path.join(work_dir, "pe2.sai")
    bwa_output = os.path.join(work_dir, "output.sam")

    null = open("/dev/null")
    subprocess.check_call([ "bwa", "index", "-p", genome_db, genome_path ], stderr=null)
    with open(pe1_output, "w") as pe1_file:
        subprocess.check_call([ "bwa", "aln", genome_db, pe1_path ], stdout=pe1_file, stderr=null)

    with open(pe2_output, "w") as pe2_file:
        subprocess.check_call([ "bwa", "aln", genome_db, pe2_path ], stdout=pe2_file, stderr=null)

    with open(bwa_output, "w") as bwa_file:
        subprocess.check_call([ "bwa", "sampe",
                                "-r", "@RG\tID:ILLUMINA\tSM:48_2\tPL:ILLUMINA\tLB:LIB1",
                                genome_db,
                                pe1_output, pe2_output,
                                pe1_path, pe2_path ], stdout=bwa_file, stderr=null)

    sam_to_bam(bwa_output, bwa_output + ".bam")
    pysam.sort(bwa_output + ".bam", output_path)
    pysam.index(output_path + '.bam')

def map_single_reads(pe_path, genome_path, output_path):
    work_dir = tempfile.mkdtemp()
    genome_db = os.path.join(work_dir, "genome")
    pe_output = os.path.join(work_dir, "pe.sai")
    bwa_output = os.path.join(work_dir, "output.sam")

    null = open("/dev/null")
    subprocess.check_call([ "bwa", "index", "-p", genome_db, genome_path ], stderr=null)
    with open(pe_output, "w") as pe_file:
        subprocess.check_call([ "bwa", "aln", genome_db, pe_path ], stdout=pe_file, stderr=null)

    with open(bwa_output, "w") as bwa_file:
        subprocess.check_call([ "bwa", "samse",
                                "-r", "@RG\tID:ILLUMINA\tSM:48_2\tPL:ILLUMINA\tLB:LIB1",
                                genome_db,
                                pe_output,
                                pe_path ], stdout=bwa_file, stderr=null)

    os.popen('mv ' + bwa_output + ' ' + output_path)

    #sam_to_bam( bwa_output, bwa_output + ".bam" )
    #pysam.sort( bwa_output + ".bam", output_path )
    #pysam.index(output_path+'.bam')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Maps the given reads with bwa.")
    parser.add_argument('pe1_path', type=str, help='Path to the first reads in a read pair (if paired reads). Just the reads if single reads')
    parser.add_argument('pe2_path', type=str, nargs='?', default=False, help='Path to the second pairs. Leave unspecified if single reads.')
    parser.add_argument('genome_path', type=str, help='Path to the reference genome/contigs.')
    parser.add_argument('output_path', type=str, help='Output path of resulting .bam and .bai file.')
    args = parser.parse_args()

    if args.pe2_path:
        map_paired_reads(args.pe1_path, args.pe2_path, args.genome_path, args.output_path)
    else:
        map_single_reads(args.pe1_path, args.genome_path, args.output_path)
