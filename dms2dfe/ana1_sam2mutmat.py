#!usr/bin/python

# Copyright 2016, Rohan Dandage <rraadd_8@hotmail.com,rohan@igib.in>
# This program is distributed under General Public License v. 3.  

import sys
from os.path import splitext, exists,basename
from Bio import SeqIO
import pandas as pd
from multiprocessing import Pool
from dms2dfe import configure
from dms2dfe.lib.variant_caller import getusablesbams_list,sam2mutmat #is_qry_alind_useful,qual_chars2nums,get_mut_cds
import logging
logging.basicConfig(format='[%(asctime)s] %(levelname)s\tfrom %(filename)s in %(funcName)s(..): %(message)s',level=logging.DEBUG) # filename=cfg_xls_fh+'.log'


def main(prj_dh):
    """
    This module processes alignment (.sam file)  and produces codon level mutation matrix of frequencies of mutations in the respective sample.
    
    :param prj_dh: path to project directory.
    """
    logging.info("start")

    # SET global variables
    global fsta_id,fsta_seqlen,fsta_seq,cds_ref,Q_cutoff

    if not exists(prj_dh) :
        logging.error("Could not find '%s'\n" % prj_dh)
        sys.exit()
    configure.main(prj_dh)
    from dms2dfe.tmp import info
    fsta_fh=info.fsta_fh
    Q_cutoff=int(info.Q_cutoff)
    cores=int(info.cores)

    with open(fsta_fh,'r') as fsta_data:
        for fsta_record in SeqIO.parse(fsta_data, "fasta") :
            fsta_id=fsta_record.id
            fsta_seq=str(fsta_record.seq) 
            fsta_seqlen=len(fsta_seq)
            logging.info("ref name : '%s', length : '%d' " % (fsta_record.id, fsta_seqlen))
    cds_ref=[]
    for cdi in range(len(fsta_seq)/3) :
        cds_ref.append(str(fsta_seq[cdi*3:cdi*3+3]))

    sbam_fhs=getusablesbams_list(prj_dh)
    if len(sbam_fhs)!=0:
        # pooled(sbam_fhs[0])
        pool=Pool(processes=int(cores)) # TODO : get it from xls
        pool.map(pooled, sbam_fhs)
        pool.close(); pool.join()                
    else:
        logging.info("already processed")  
    logging.shutdown()

def pooled(sbam_fh):
    """
    This module makes use of muti threading to speed up `dms2dfe.lib.variant_caller.sam2mutmat`.     
    
    :param sbam_fh: path to sorted bam file.
    """
    logging.info("processing: %s" % (basename(sbam_fh)))
    sam2mutmat(sbam_fh,fsta_id,fsta_seqlen,fsta_seq,cds_ref,Q_cutoff)    

if __name__ == '__main__':
    main(sys.argv[1])