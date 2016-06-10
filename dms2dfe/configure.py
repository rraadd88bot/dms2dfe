#!usr/bin/python

# Copyright 2016, Rohan Dandage <rraadd_8@hotmail.com,rohan@igib.in>
# This program is distributed under General Public License v. 3.  


import sys
from os.path import exists,splitext,abspath,dirname
from os import makedirs
from glob import glob
import pandas as pd
import subprocess
import logging
logging.basicConfig(format='[%(asctime)s] %(levelname)s\tfrom %(filename)s in %(funcName)s(..): %(message)s',level=logging.DEBUG) # filename=cfg_dh+'.log'
from dms2dfe.lib.io_data_files import is_cfg_ok,info2src,raw_input2info
    
# GET INPTS    
def main(prj_dh,inputs=None):
    """
    Generates and compiles configurations.
    
    Firstly, to create a new project directory (`prj_dh`) in current directory, 

    .. code-block:: text

        from dms2dfe import configure
        configure.main("path/to/project_directory")

    Editing configuration files (`path/to/project_directory/cfg/info`)

    Input parameters can be fed manually in csv file located here `project_directory/cfg/info`.
    
    Optionally they can be entered using command prompt,

    .. code-block:: text

        from dms2dfe import configure
        configure.main("path/to/project_directory","inputs")

    Optionally to feed default parameters use

    .. code-block:: text

        from dms2dfe import configure
        configure.main("defaults")

    :param prj_dh: path to project directory.

    """
    #SET VARS
    cfgs=['lbls', 'fit', 'comparison', 'info', 'repli','feats','barcodes']
    cfg_dh=prj_dh+"/cfg"

    if inputs=="inputs":
        raw_input2info(prj_dh,"input")        
        logging.info("configuration inputs modified!")
    elif prj_dh=="defaults":
        raw_input2info((abspath(dirname(__file__))),"default")
        logging.info("configuration defaults modified!")
    elif inputs=="dependencies" or inputs=="deps":
        if not exists("dms2dfe_dependencies"):
            makedirs("dms2dfe_dependencies")
        #dssp
        dssp_fh="dms2dfe_dependencies/dssp-2.0.4-linux-amd64"
        if not exists(dssp_fh):
            logging.info("configuring: dssp")
            dssp_lnk="ftp://ftp.cmbi.ru.nl/pub/software/dssp/dssp-2.0.4-linux-amd64"
            com="wget -q %s --directory-prefix=dms2dfe_dependencies" % dssp_lnk
            subprocess.call(com,shell=True)
            subprocess.call("chmod +x %s" % dssp_fh,shell=True)            
        #bowtie2
        bowtie2_fh="dms2dfe_dependencies/bowtie2-2.2.1/bowtie2"   
        if not exists(dirname(bowtie2_fh)):
            logging.info("configuring: bowtie2")
            bowtie2_lnk="http://sourceforge.net/projects/bowtie-bio/files/bowtie2/2.2.1/bowtie2-2.2.1-linux-x86_64.zip"
            com="wget -q %s --directory-prefix=dms2dfe_dependencies" % bowtie2_lnk
            subprocess.call(com,shell=True)
            subprocess.call("unzip dms2dfe_dependencies/bowtie2-2.2.1-linux-x86_64.zip -d dms2dfe_dependencies",shell=True)
            subprocess.call("chmod +x %s" % bowtie2_fh,shell=True) 
        #samtools
        samtools_fh="dms2dfe_dependencies/samtools-0.1.18/samtools"        
        if not exists(dirname(samtools_fh)):
            logging.info("configuring: samtools")
            samtools_lnk="https://sourceforge.net/projects/samtools/files/samtools/0.1.18/samtools-0.1.18.tar.bz2"
            com="wget -q %s --directory-prefix=dms2dfe_dependencies" % samtools_lnk
            subprocess.call(com,shell=True)
            subprocess.call("bzip2 -dc dms2dfe_dependencies/samtools-0.1.18.tar.bz2 | tar xvf - -C dms2dfe_dependencies",shell=True)
        if not exists(samtools_fh):            
            std=subprocess.Popen("cd dms2dfe_dependencies/samtools-0.1.18; make",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if "fatal error: zlib.h" in std.stderr.read():
                print "\n###   TROUBLESHOOT   ###\nFor interference issues (with htslib) installation of samtools dependency gave following error,\n.. zlib.h: No such file or directory\nPlease use following command before installing samtools. i.e.\nsudo apt-get install zlib1g-dev libncurses5-dev\nsudo apt-get update\ndms2dfe_dependencies/samtools-0.1.18/make\n\nAfter that rerun this command (configure.main(prj_dh,'deps'))\n"
            else:
                subprocess.call("chmod +x %s" % samtools_fh,shell=True)
        #trimmomatic
        trimmomatic_fh="dms2dfe_dependencies/Trimmomatic-0.33/trimmomatic-0.33.jar"
        if not exists(trimmomatic_fh):
            logging.info("configuring: trimmomatic")
            trimmomatic_lnk="http://www.usadellab.org/cms/uploads/supplementary/Trimmomatic/Trimmomatic-0.33.zip"
            com="wget -q %s --directory-prefix=dms2dfe_dependencies" % trimmomatic_lnk
            subprocess.call(com,shell=True)
            subprocess.call("unzip dms2dfe_dependencies/Trimmomatic-0.33.zip -d dms2dfe_dependencies/",shell=True)

        std=subprocess.Popen("which java",shell=True,stdout=subprocess.PIPE)
        if not std.stdout.read():
            print "\n###   TROUBLESHOOT   ###\njava environment isn't installed on the system.\nIt would be required for running Trimmomatic through fast2qcd module. Please install it by following command,\nsudo apt-get install openjdk-7-jre-headless\nsudo apt-get update\n"
        std=subprocess.Popen("which glxinfo",shell=True,stdout=subprocess.PIPE)
        if not std.stdout.read():
            print "\n###   TROUBLESHOOT   ###\nTo generate images from PDB structures using UCSF-Chimera, essential graphics drivers are required.\n In case of the hardware already present on system please install following drivers.\nsudo apt-get install mesa-utils\nsudo apt-get update\n"

        #add to defaults
        info=pd.read_csv("%s/cfg/info" % (prj_dh))
        info=info.set_index("varname",drop=True)
        info.loc["trimmomatic_fh","input"]=trimmomatic_fh
        info.loc["dssp_fh","input"]=dssp_fh
        info.loc["bowtie2_fh","input"]=bowtie2_fh
        info.loc["samtools_fh","input"]=samtools_fh
        info.reset_index().to_csv("%s/cfg/info" % (prj_dh), index=False)
        logging.info("dependencies installed!")
    elif not exists(cfg_dh) :
        makedirs(cfg_dh)
        subprocess.call("cp -r %s/cfg %s"% (abspath(dirname(__file__)),prj_dh) ,shell=True)
        logging.info("new project directory created!: %s " % prj_dh)
        logging.info("modify configurations in %s" % cfg_dh)
    else :
        if is_cfg_ok(cfg_dh,cfgs) :
            info2src(prj_dh)
        else:
            logging.info("check the configuration again.")
            sys.exit()
    logging.shutdown()
                        
if __name__ == '__main__':
    
    if len(sys.argv)==2:
        main(sys.argv[1])
    elif len(sys.argv)==3:
        main(sys.argv[1],sys.argv[2])