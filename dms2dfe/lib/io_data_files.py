#!usr/bin/python

# Copyright 2016, Rohan Dandage <rraadd_8@hotmail.com,rohan@igib.in>
# This program is distributed under General Public License v. 3.  

"""
================================
``io_data_files``
================================
"""
import sys
import pandas as pd
from os.path import exists,basename,abspath,dirname
import logging
from glob import glob  
logging.basicConfig(format='[%(asctime)s] %(levelname)s\tfrom %(filename)s in %(funcName)s(..): %(message)s',level=logging.DEBUG) # filename=cfg_xls_fh+'.log'

## DEFS
def is_cfg_ok(cfg_dh,cfgs) :
    """
    Checks if the required files are present in given directory.
    
    :param cfg_dh: path to directory.
    :param cfgs: list of names of files.
    """
    cfg_dh_cfgs=glob(cfg_dh+"/*")
    cfg_dh_cfgs=[basename(cfg_dh_cfg) for cfg_dh_cfg in cfg_dh_cfgs]
    for cfg in cfgs :   # check if required sheets are present
        if not cfg in cfg_dh_cfgs :
            logging.error("%s does not exist" % cfg)    
            return False
            break
    return True

def info2src(prj_dh):
    """
    This converts `.csv` configuration file to `.py` source file saved in `/tmp/`.
    
    :param prj_dh: path to project directory
    """        
    info=pd.read_csv(prj_dh+"/cfg/info")
    info_path_vars=[varn for varn in info['varname'] if ("_fh" in varn) or ("_dh" in varn)]
    info=info.set_index("varname")
    #find pdb_fh and fsta_fh in prj_dh
    if pd.isnull(info.loc["pdb_fh","input"]):
        try:
            info.loc["pdb_fh","input"]=glob("%s/*.pdb" % prj_dh)[0]
        except:
            logging.error("can not find .pdb file")
    if pd.isnull(info.loc["fsta_fh","input"]):
        try:
            info.loc["fsta_fh","input"]=glob("%s/*.fasta" % prj_dh)[0]
        except:
            logging.error("could not find .fasta file")     
    info_paths=[info.loc[info_path_var,"input"] for info_path_var in info_path_vars]
    for info_path in info_paths:
        if not pd.isnull(info_path):
            if not exists(info_path):                
                logging.error('Path to files do not exist %s : %s' % (info_path_vars[info_paths.index(info_path)],info_path))
                from dms2dfe import configure
                configure.main(prj_dh,"deps")
    info.reset_index().to_csv(prj_dh+"/cfg/info",index=False)
    csv2src(prj_dh+"/cfg/info","%s/../tmp/info.py" % (abspath(dirname(__file__))))
    logging.info("configuration compiled: %s/cfg/info" % prj_dh)

def csv2src(csv_fh,src_fh):
    """
    This writes `.csv` to `.py` source file.
    
    :param csv_fh: path to input `.csv` file.
    :param src_fh: path to output `.py` source file.
    """
    info=pd.read_csv(csv_fh)
    info=info.set_index('varname')    
    src_f=open(src_fh,'w')
    src_f.write("#!usr/bin/python\n")
    src_f.write("\n")
    src_f.write("# source file for dms2dfe's configuration \n")
    src_f.write("\n")

    for var in info.iterrows() :
        val=info['input'][var[0]]
        if pd.isnull(val):
            val=info['default'][var[0]]
        src_f.write("%s='%s' #%s\n" % (var[0],val,info["description"][var[0]]))
    src_f.close()

def raw_input2info(prj_dh,inputORdefault):     
    """
    This writes configuration `.csv` file from `raw_input` from prompt.
    
    :param prj_dh: path to project directory.
    :param inputORdefault: column name "input" or "default". 
    """
    info=pd.read_csv(prj_dh+"/cfg/info")
    info=info.set_index("varname",drop=True)
    for var in info.index.values:
        val=raw_input("%s (default: %s) =" % (info.loc[var, "description"],info.loc[var, "default"]))
        if not val=='':
            info.loc[var, inputORdefault]=val
    info.reset_index().to_csv("%s/cfg/info" % prj_dh, index=False)

def is_xls_ok(cfg_xls,cfg_xls_sheetnames_required) :
    """
    Checks if the required sheets are present in the configuration excel file.
    Input/s : path to configuration excel file 
    """
    cfg_xls_sheetnames=cfg_xls.sheet_names
    cfg_xls_sheetnames= [str(x) for x in cfg_xls_sheetnames]# unicode to str

    for qry_sheet_namei in cfg_xls_sheetnames_required :   # check if required sheets are present
        #qry_sheet_namei=str(qry_sheet_namei)
        if not qry_sheet_namei in cfg_xls_sheetnames :
            logging.error("pipeline : sheetname '%s' does not exist" % qry_sheet_namei)    
            return False
            break
    return True

def is_info_ok(xls_fh):
    """
    This checks the sanity of info sheet in the configuration excel file.
    For example if the files exists or not.
    """
    info=pd.read_excel(xls_fh,'info')
    info_path_vars=[varn for varn in info['varname'] if ("_fh" in varn) or ("_dh" in varn)]
    info=info.set_index("varname")
    info_paths=[info.loc[info_path_var,"input"] for info_path_var in info_path_vars]
    for info_path in info_paths:
        if not pd.isnull(info_path): 
            if not exists(info_path):                
                return False #(info_path_vars[info_paths.index(info_path)],info_path)
                break
    return True    

def xls2h5(cfg_xls,cfg_h5,cfg_xls_sheetnames_required) :
    """
    Converts configuration excel file to HDF5(h5) file.
    Here sheets in excel files are converted to groups in HDF5 file.
    Input/s : (path to configuration excel file, path to output HDF5 file)
    """
    for qry_sheet_namei in  cfg_xls_sheetnames_required:  
        qry_sheet_df=cfg_xls.parse(qry_sheet_namei)
        qry_sheet_df=qry_sheet_df.astype(str) # suppress unicode error
        qry_sheet_df.columns=[col.replace(" ","_") for col in qry_sheet_df.columns]
        cfg_h5.put("cfg/"+qry_sheet_namei,convert2h5form(qry_sheet_df), format='table', data_columns=True)
    return cfg_h5

def xls2csvs(cfg_xls,cfg_xls_sheetnames_required,output_dh):
    """
    Converts configuration excel file to HDF5(h5) file.
    Here sheets in excel files are converted to groups in HDF5 file.
    Input/s : (path to configuration excel file, path to output HDF5 file)
    """
    for qry_sheet_namei in  cfg_xls_sheetnames_required:  
        qry_sheet_df=cfg_xls.parse(qry_sheet_namei)
        qry_sheet_df=qry_sheet_df.astype(str) # suppress unicode error
        qry_sheet_df.to_csv("%s/%s" % (output_dh,qry_sheet_namei))
#         print "%s/%s" % (output_dh,qry_sheet_namei)

def convert2h5form(df):
    from dms2dfe.lib.io_strs import convertstr2format 
    df.columns=[convertstr2format(col,"^[a-zA-Z0-9_]*$") for col in df.columns.tolist()]
    return df

def csvs2h5(dh,sub_dh_list,fn_list,output_dh,cfg_h5):
    """
    This converts the csv files to tables in HDF5.
    """
    for fn in fn_list:
        for sub_dh in sub_dh_list : # get aas or cds  
            fh=output_dh+"/"+dh+"/"+sub_dh+"/"+fn+""
            df=pd.read_csv(fh) # get mat to df
            df=df.loc[:,[col.replace(" ","_") for col in list(df.columns) if not (('index' in col) or ('Unnamed' in col)) ]]
            exec("cfg_h5.put('%s/%s/%s',df, format='table', data_columns=True)" % (dh,sub_dh,str(fn)),locals(), globals()) # store the otpts in h5 eg. cds/N/lbl        
            # print("cfg_h5.put('%s/%s/%s',df.convert_objects(), format='table', data_columns=True)" % (dh,sub_dh,str(fn))) # store the otpts in h5 eg. cds/N/lbl        

def csvs2h5(dh,sub_dh_list,fn_list):
    """
    This converts csvs into HDF5 tables.
    """
    for fn in fn_list:
        for sub_dh in sub_dh_list : # get aas or cds  
            fh=output_dh+"/"+dh+"/"+sub_dh+"/"+fn+""
            key=dh+"/"+sub_dh+"/"+fn
            if (exists(fh)) and (key in cfg_h5):
                df=pd.read_csv(fh) # get mat to df
                key=key+"2"
                cfg_h5.put(key,df.convert_objects(), format='table', data_columns=True) # store the otpts in h5 eg. cds/N/lbl        
