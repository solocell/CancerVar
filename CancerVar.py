##################################################################################
# Author: Li Quan (leequan@gmail.com)
# Created Time: 2017-01-13 20:38:23 Friday 
# File Name: CancerVar.py File type: python
# Last Change:.
# Description: python script for Interpretation of Pathogenetic of Cancer Variants
##################################################################################
#!/usr/bin/env python

import string,copy,logging,os,io,re,time,sys,platform,optparse,gzip,csv

prog="CancerVar"

version = """%prog 0.1
Copyright (C) 2017 Wang Genomic Lab
CancerVar is free for non-commercial use without warranty.
Please contact the authors for commercial use.
Written by Quan LI,leequan@gmail.com.
============================================================================
"""

usage = """Usage: %prog [OPTION] -i  INPUT -o  OUTPUT ...
       %prog  --config=config.ini ...
"""

description = """=============================================================================
CancerVar
Interpretation of Pathogenic/Benign for cancer variants using python script.
=============================================================================
"""
end = """=============================================================================
Thanks for using CancerVar!
Report bugs to leequan@gmail.com;
CancerVar homepage: <https://CancerVar.wglab.org>
=============================================================================
"""



if platform.python_version()< '3.0.0' :
    import ConfigParser
else:
    import configparser

paras = {}

def ConfigSectionMap(config,section):
    global paras
    options = config.options(section)
    for option in options:
        try:
            paras[option] = config.get(section, option)
            if paras[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            paras[option] = None
    return

user_evidence_dict={}


class myGzipFile(gzip.GzipFile):
    def __enter__(self):
        if self.fileobj is None:
            raise ValueError("I/O operation on closed GzipFile object")
        return self

    def __exit__(self, *args):
        self.close()


#begin read some important datsets/list firstly;
lof_genes_dict={}
aa_changes_dict={}
domain_benign_dict={}
mim2gene_dict={}
mim2gene_dict2={}
morbidmap_dict={}
morbidmap_dict2={}
PP2_genes_dict={}
BP1_genes_dict={}
PS4_snps_dict={}
exclude_snps_dict={}
mim_recessive_dict={}
mim_domin_dict={}
mim_adultonset_dict={}
mim_pheno_dict={}
mim_orpha_dict={}
orpha_dict={}
BS2_snps_recess_dict={}
BS2_snps_domin_dict={}
knownGeneCanonical_dict={}
knownGeneCanonical_st_dict={}
knownGeneCanonical_ed_dict={}

add_markers_dict={}
cgi_markers_dict={}
cancer_pathway_dict={}
cancers_gene_dict={}

add_d=[]
cgi_d=[]

def flip_ACGT(acgt):
    nt="";
    if acgt=="A":
        nt="T"
    if acgt=="T":
        nt="A"
    if acgt=="C":
        nt="G"
    if acgt=="G":
        nt="C"
    if acgt=="N":
        nt="N"
    if acgt=="X":
        nt="X"
    return(nt)

def read_datasets():
#0. read the user specified evidence file
    if os.path.isfile(paras['evidence_file']):
        try:
            fh=open(paras['evidence_file'], "r")
            strs = fh.read()
            for line2 in strs.split('\n'):
                cls2=line2.split('\t')
                if len(cls2)>1:
                    keys=cls2[0]+"_"+cls2[1]+"_"+cls2[2]+"_"+cls2[3]
                    keys=re.sub("[Cc][Hh][Rr]","",keys)
                    #print("%s" %keys)
                    user_evidence_dict[keys]=cls2[4].upper()
        except IOError:
            print("Error: can\'t read the user specified evidence file %s" % paras['evidence_file'])
        else:
            fh.close()

#1.LOF gene list
    try:
        fh = open(paras['lof_genes'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split('\t')
            if len(cls2[0])>1:
                lof_genes_dict[cls2[0]]='1'
    except IOError:
        print("Error: can\'t read the LOF genes file %s" % paras['lof_genes'])
        print("Error: Please download it from the source website")
        sys.exit()
        return
    else:
        fh.close()


#1. cgi_markers
    global cgi_d
    try:
        with open(paras['cgi_markers']) as fh:
            reader = csv.reader(fh, delimiter="\t")
            cgi_d = list(reader)
        print cgi_d[0] # 248
        print cgi_d[3] # 248
        print len(cgi_d) # 248
        print len(cgi_d[0]) # 248
#['Biomarker', 'Gene', 'Alteration type', 'Alteration', "'Primary Tumor type'", 'Targeting', 'Drug status', 'Drug family', 'Drug', 'Association', 'Evidence level', 'Assay type', 'Source', 'Curator', 'Curation date', 'Primary Tumor type', 'Metastatic Tumor Type', 'TCGI included', 'Comments', 'Drug full name']
# Biomarker', 'Gene', 'Alteration type', 'Alteration', "'Primary Tumor type'",'Drug status','Drug full name','Association','Evidence level','Source','Tumor Codes'
    except IOError:
        print("Error: can\'t read the cgi_markers file %s" % paras['cgi_markers'])
        print("Error: Please download it from the source website")
        sys.exit()
        return
    else:
        fh.close()

        
        for ii in range(0,len(cgi_d)):
            gene=cgi_d[ii][1]
            mut_type=cgi_d[ii][2]
            mut=cgi_d[ii][3]
            mut_types=mut_type.split(';');  # BIA CNA EXPR FUS MUT
            list_mut_size=len(mut_types)
            mut_alts=mut.split(';');
            for jj in range(0,list_mut_size):
                mut_list=mut_alts[jj].split(':')
                if(len(mut_list)>1):
                    gene1=mut_list[0]
                    mutb=mut_list[1]
                else:
                    gene1=gene
                    mutb=mut_alts[jj]
                    
                if(mut_types[jj]=="FUS"):                    
                    mutt="fus_"+re.sub('__','-',mut_alts[jj])
                    key=mutt
                    default_s=''
                    cgi_markers_dict[key]=str(ii)+","+cgi_markers_dict.get(key,default_s)
                    #print key,ii,cgi_markers_dict[key]
                elif(mut_types[jj]=="EXPR"):                    
                    mutt=gene1+"_"+"expr_"+mutb
                    key=mutt
                    default_s=''
                    cgi_markers_dict[key]=str(ii)+","+cgi_markers_dict.get(key,default_s)
                    #print key,ii,cgi_markers_dict[key]
                elif(mut_types[jj]=="CNA"):                    
                    mutt=gene1+"_"+"cna_"+mutb
                    key=mutt
                    default_s=''
                    cgi_markers_dict[key]=str(ii)+","+cgi_markers_dict.get(key,default_s)
                    #print key,ii,cgi_markers_dict[key]
                elif(mut_types[jj]=="BIA"):                    
                    mutt=gene1+"_"+"bia_"+mutb
                    key=mutt
                    default_s=''
                    cgi_markers_dict[key]=str(ii)+","+cgi_markers_dict.get(key,default_s)
                    #print key,ii,cgi_markers_dict[key]
                elif(mut_types[jj]=="MUT"):                    
                    #mutt=gene1+"_"+"bia_"+mutb
                    for mutt_s in mutb.split(','):
                        mutt=gene1+"_"+mutt_s
                        key=mutt
                        default_s=''
                        cgi_markers_dict[key]=str(ii)+","+cgi_markers_dict.get(key,default_s)
                        #print key,ii,cgi_markers_dict[key]
                else:
                    key=gene1+"_"+mutb
                    default_s=''
                    cgi_markers_dict[key]=str(ii)+","+cgi_markers_dict.get(key,default_s)
                    #print key,ii,cgi_markers_dict[key]
                    
                    
                    



#        print cgi_markers_dict
# end deal with cgi_markers




#2. add_markers from pmkb
    global add_d
    try:
        with open(paras['add_markers']) as fh:
            reader = csv.reader(fh, delimiter="\t")
            add_d = list(reader)
#['Gene', 'Variants', 'Tumor(s)', 'Publications']

    except IOError:
        print("Error: can\'t read the additional markers file %s" % paras['add_markers'])
        print("Error: Please download it from the source website")
        sys.exit()
        return
    else:
        fh.close()
        
        #print add_d[0] # 248
        #print add_d[3] # 248
        #print len(add_d[0])
#['Gene', 'Variants', 'Tumor(s)', 'Publications']
        for ii in range(0,len(add_d)):
            gene=add_d[ii][0]
            mut=add_d[ii][1]
            mut=re.sub('"','',mut)
            if(  re.findall('any ', mut, flags=re.IGNORECASE)):
                if(mut=="any mutation"): mut="mut_any"
                if(mut=="any insertion"): mut="insertion_any"
                if(mut=="any deletion"): mut="deletion_any"
                if(mut=="any frameshift"): mut="frameshift_any"
                if(mut=="any indel"): mut="indel_any"
                if(mut=="any missense"): mut="missense_any"
                if(mut=="any nonsense"): mut="nonsense_any"
                key=gene+'_'+mut
                default_s=''
                add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                #print key,ii,add_markers_dict[key]
            elif(  re.findall('rearrangement', mut, flags=re.IGNORECASE)):
                #print("rearrangement ");
                mut="fus_"+gene
                key=mut
                default_s=''
                add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                #print key,ii,add_markers_dict[key]
            elif(  re.findall('copy number', mut, flags=re.IGNORECASE)):
                #print("copy number CNA ");
                poss,mutb=mut.split('copy number ',1);
                muts="cna_"+mutb
                key=gene+'_'+muts
                default_s=''
                add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                #print key,ii,add_markers_dict[key]
                
            # format as " exon(s) 10, 20, 21 any"
            elif(  re.findall('exon\(s\) ', mut, flags=re.IGNORECASE)):
                #print("exon(s) ");
                str1,str2=mut.split('exon(s) ',1);
                if( not  re.findall(',', mut, flags=re.IGNORECASE)): # for single position
                    poss,mutb=str2.split(' ',1);
                    #mut0=re.sub('"','',mutb)
                    poss_t=int(poss)
                    muts="exon_"+str(poss_t)+"_"+mutb
                    key=gene+'_'+muts
                    default_s=''
                    add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                    #print key,ii,add_markers_dict[key]
                else: # for multiple positions
                    list_pos=str2.split(',');
                    list_pos_size=len(list_pos)

                    list_tt=list_pos[list_pos_size-1].split(' ')
                    list_tt_size=len(list_tt)

                    mutb=list_tt[list_tt_size-1]
                    pos_end=str(int(list_tt[list_tt_size-2]))
                    muts="exon_"+pos_end+"_"+mutb
                    key=gene+'_'+muts
                    default_s=''
                    add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                    #print key,ii,add_markers_dict[key]
                    for jj in range(0,list_pos_size-1):
                        pos_be=str(int(list_pos[jj]))
                        muts="exon_"+pos_be+"_"+mutb
                        key=gene+'_'+muts
                        default_s=''
                        add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                        #print key,ii,add_markers_dict[key]
            # " codon(s) 289, 596, 598 any"   codon(s) 132 any
            elif(  re.findall('codon\(s\) ', mut, flags=re.IGNORECASE)):
                #print("codon(s) ");
                str1,str2=mut.split('codon(s) ',1);
                if( not  re.findall(',', mut, flags=re.IGNORECASE)): # for single position
                    poss,mutb=str2.split(' ',1);
                    #mut0=re.sub('"','',mutb)
                    poss_t=int(poss)
                    muts="codon_"+str(poss_t)+"_"+mutb
                    key=gene+'_'+muts
                    default_s=''
                    add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                    #print key,ii,add_markers_dict[key]
                else: # for multiple positions
                    list_pos=str2.split(',');
                    list_pos_size=len(list_pos)

                    list_tt=list_pos[list_pos_size-1].split(' ')
                    list_tt_size=len(list_tt)

                    mutb=list_tt[list_tt_size-1]
                    pos_end=str(int(list_tt[list_tt_size-2]))
                    muts="codon_"+pos_end+"_"+mutb
                    key=gene+'_'+muts
                    default_s=''
                    add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                    #print key,ii,add_markers_dict[key]
                    for jj in range(0,list_pos_size-1):
                        pos_be=str(int(list_pos[jj]))
                        muts="codon_"+pos_be+"_"+mutb
                        key=gene+'_'+muts
                        default_s=''
                        add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                        #print key,ii,add_markers_dict[key]
            else:
                key=gene+'_'+mut
                default_s=''
                add_markers_dict[key]=str(ii)+","+add_markers_dict.get(key,default_s)
                #print key,ii,add_markers_dict[key]
            '''
            try:
                value = str(add_markers_dict[key])+","+str(ii)
                add_markers_dict[key]=value
            except KeyError:
                add_markers_dict[key]=ii
            else:
                pass
            '''
        #print add_markers_dict
# end deal with add_markers from pmkb



#3. OMIM mim2gene.txt file
    try:
        fh = open(paras['mim2gene'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split('\t')
            if len(cls2)>1:
                cls0=cls2[4].split(',')
                keys=cls0[0]
                mim2gene_dict[keys]=cls2[0]
                keys1=cls2[3]
                keys=keys1.upper()
                mim2gene_dict2[keys]=cls2[0]
    except IOError:
        print("Error: can\'t read the OMIM  file %s" % paras['mim2gene'])
        print("Error: Please download it from http://www.omim.org/downloads")
        sys.exit()
    else:
        fh.close()


#4.morbidmap from OMIM  for BP5 ,  multifactorial disorders  list
    try:
        fh = open(paras['morbidmap'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split('\t')
            #print("%s %s %d" % (cls2[0], cls[Funcanno_flgs['Gene']], len(cls2[0])) )
            #{Tuberculosis, protection against}, 607948 (3)|TIRAP, BACTS1|606252|11q24.2
            if len(cls2[0])>1 and cls2[0].find('{')==0:  # disorder start with "{"
                morbidmap_dict2[ cls2[2] ]='1'  # key as mim number
                for cls3 in cls2[1].split(', '):
                    keys=cls3.upper()
                    morbidmap_dict[ keys ]='1'  # key as gene name
    except IOError:
        print("Error: can\'t read the OMIM morbidmap disorder file %s" % paras['morbidmap'])
        print("Error: Please download it from http://www.omim.org/downloads")
        sys.exit()
    else:
        fh.close()


#5. read the user specified SNP list, the variants will pass the frequency check.
    if os.path.isfile(paras['exclude_snps']):
        try:
            fh=open(paras['exclude_snps'], "r")
            strs = fh.read()
            for line2 in strs.split('\n'):
                cls2=line2.split('\t')
                if len(cls2)>1:
                    keys=cls2[0]+"_"+cls2[1]+"_"+cls2[2]+"_"+cls2[3]
                    keys=re.sub("[Cc][Hh][Rr]","",keys)
                    exclude_snps_dict[keys]="1"
        except IOError:
            print("Error: can\'t read the user specified SNP list file %s" % paras['exclude_snps'])
        else:
            fh.close()


#6. knownGeneCanonical exon file  # caution the build ver, now it is hg19
    try:
        fh = open(paras['knowngenecanonical'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split(' ')
            if len(cls2)>1:
                keys=cls2[0]
                knownGeneCanonical_dict[keys]=cls2[1]
                knownGeneCanonical_st_dict[keys]=cls2[2]
                knownGeneCanonical_ed_dict[keys]=cls2[3]
                #print("%s %s" %(keys,knownGeneCanonical_dict[keys]))
    except IOError:
        print("Error: can\'t read the knownGeneCanonical  file %s" % paras['knowngenecanonical'])
        print("Error: Please download it from the source website")
        sys.exit()
    else:
        fh.close()


#7. OMIM mim_pheno.txt file

    try:
        fh = open(paras['mim_pheno'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split(' ')
            if len(cls2)>1:
                keys=cls2[0]
                mim_pheno_dict[keys]=cls2[1]
                #print("%s %s" %(keys,mim_pheno_dict[keys]))
    except IOError:
        print("Error: can\'t read the MIM  file %s" % paras['mim_pheno'])
        print("Error: Please download it from CancerVar source website")
        sys.exit()
    else:
        fh.close()




#8. OMIM mim_orpha.txt file
    try:
        fh = open(paras['mim_orpha'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split(' ')
            if len(cls2)>1:
                keys=cls2[0]
                mim_orpha_dict[keys]=cls2[1]
                #print("%s %s" %(keys,mim_orpha_dict[keys]))
    except IOError:
        print("Error: can\'t read the MIM  file %s" % paras['mim_orpha'])
        print("Error: Please download it from CancerVar source website")
        sys.exit()
    else:
        fh.close()

#9.  orpha.txt file
    try:
        fh = open(paras['orpha'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split('\t')
            if len(cls2)>1:
                keys=cls2[0]
                orpha_dict[keys]=cls2[1]
                #print("%s %s" %(keys,mim_orpha_dict[keys]))
    except IOError:
        print("Error: can\'t read the Orpha  file %s" % paras['orpha'])
        print("Error: Please download it from CancerVar source website")
        sys.exit()
    else:
        fh.close()

#10 cancer_pathway=%(database_cancervar)s/cancer_pathway.list
    global cancer_pathway_dict
    try:
        fh = open(paras['cancer_pathway'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split('\t')
            if len(cls2[0])>1:
                cancer_pathway_dict[cls2[0]]='1'
    except IOError:
        print("Error: can\'t read the cancer_pathway genes file %s" % paras['cancer_pathway'])
        print("Error: Please download it from the source website")
        sys.exit()
        return
    else:
        fh.close()

#11 cancers_genes=%(database_cancervar)s/cancers_genes.list
    global cancers_gene_dict
    try:
        fh = open(paras['cancers_genes'], "r")
        strs = fh.read()
        for line2 in strs.split('\n'):
            cls2=line2.split('\t')
            if len(cls2[0])>1:
                cancers_gene_dict[cls2[0]]='1'
    except IOError:
        print("Error: can\'t read the cancers diseases genes file %s" % paras['cancer_pathway'])
        print("Error: Please download it from the source website")
        sys.exit()
        return
    else:
        fh.close()



#end read datasets
    return



def check_downdb():
    path=paras['database_locat']
    path=path.strip()
    path=path.rstrip("\/")
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        print("Notice: the folder of %s is created!" % path)
    else:
        print("Warning: the folder of %s is already created!" % path)
    ds=paras['database_names']
    ds.expandtabs(1);
    # database_names = refGene 1000g2014oct esp6500siv2_all avsnp144 ljb26_all clinvar_20150629 exac03 hg19_dbscsnv11 dbnsfp31a_interpro rmsk ensGene

    for dbs in ds.split():
        # os.path.isfile(options.table_annovar)
        file_name=dbs
        if dbs=="1000g2014oct":
            file_name="ALL.sites.2014_10"
        if dbs=="1000g2015aug":
            file_name="ALL.sites.2015_08"

        dataset_file=paras['database_locat']+"/"+paras['buildver']+"_"+file_name+".txt"
        if dbs != 'rmsk':
            cmd="perl "+paras['annotate_variation']+" -buildver "+paras['buildver']+" -downdb -webfrom annovar "+file_name+" "+paras['database_locat']
        if dbs == 'rmsk':
            cmd="perl "+paras['annotate_variation']+" -buildver "+paras['buildver']+" -downdb "+file_name+" "+paras['database_locat']
        if  not os.path.isfile(dataset_file):
            print("Warning: The Annovar dataset file of %s is not in %s,begin to download this %s ..." %(dbs,paras['database_locat'],dataset_file))
            print("%s" %cmd)
            os.system(cmd)

def check_input():
    inputft= paras['inputfile_type']
    if inputft.lower() == 'avinput' :
        return
    if inputft.lower() == 'vcf':
        #convert2annovar.pl -format vcf4 variantfile > variant.avinput
        cmd="perl "+paras['convert2annovar']+" -format vcf4 "+ paras['inputfile']+"> "+paras['inputfile']+".avinput"
        print("Warning: Begin to convert your vcf file of %s to AVinput of Annovar ..." % paras['inputfile'])
        print("%s" %cmd)
        os.system(cmd)
    return

def check_annovar_result():
# table_annovar.pl example/ex1.avinput humandb/ -buildver hg19 -out myanno -remove -protocol refGene,esp6500siv2_all,1000g2015aug_all,avsnp144,ljb26_all,CLINSIG,exac03   -operation  g,f,f,f,f,f,f   -nastring . -csvout
    inputft= paras['inputfile_type']
    if inputft.lower() == 'avinput' :
        cmd="perl "+paras['table_annovar']+" "+paras['inputfile']+" "+paras['database_locat']+" -buildver "+paras['buildver']+" -remove -out "+ paras['outfile']+" -protocol refGene,ensGene,knownGene,esp6500siv2_all,1000g2015aug_all,exac03,avsnp147,dbnsfp30a,dbscsnv11,dbnsfp31a_interpro,rmsk,clinvar_20161128,cosmic70,icgc21  -operation  g,g,g,f,f,f,f,f,f,f,r,f,f,f   -nastring . --otherinfo"
    else:
        cmd="perl "+paras['table_annovar']+" "+paras['inputfile']+".avinput "+paras['database_locat']+" -buildver "+paras['buildver']+" -remove -out "+ paras['outfile']+"  -protocol refGene,ensGene,knownGene,esp6500siv2_all,1000g2015aug_all,exac03,avsnp147,dbnsfp30a,dbscsnv11,dbnsfp31a_interpro,rmsk,clinvar_20161128,cosmic70,icgc21  -operation  g,g,g,f,f,f,f,f,f,f,r,f,f,f  -nastring . --otherinfo"
    print("%s" %cmd)
    os.system(cmd)
    return

def get_gdi_rvis_lof(gene_name,line_out,dicts,temple):
    try:
        line_out=line_out+"\t"+'\t'.join(str(e) for e in dicts[gene_name])
    except KeyError:
        line_out=line_out+"\t"+'\t'.join(str(e) for e in temple)
    else:
        pass
    return(line_out)


def check_gdi_rvis_LOF(anvfile):
    gdi={}
    rvis={}
    lof={}
    newoutfile=anvfile+".grl_p"
# begin open file  and set dicts for gdi rvis and lof:
    try:
        fh = open(paras['gdi_file'], "r")
        strs = fh.read()
        for line in strs.split('\n'):
            cls=line.split('\t')
            if len(cls)>1:
                gdi[cls[0]]=cls[1:]
    except IOError:
        print("Error: can\'t read the annovar output file %s" % paras['gdi_file'])
        sys.exit()
        return
    else:
        pass
        fh.close()

    try:
        fh = open(paras['rvis_file'], "r")
        strs = fh.read()
        for line in strs.split('\n'):
            cls=line.split('\t')
            rvis['Gene']=['RVIS_ExAC_0.05%(AnyPopn)','%RVIS_ExAC_0.05%(AnyPopn)']
            if len(cls)>1:
                rvis[cls[4]]=cls[5:]
    except IOError:
        print("Error: can\'t read the annovar output file %s" % paras['rvis_file'])
        sys.exit()
        return
    else:
        pass
        fh.close()

    try:
        fh = open(paras['lof_file'], "r")
        strs = fh.read()
        for line in strs.split('\n'):
            cls=line.split('\t')
            if len(cls)>1:
                lof[cls[0]]=cls[1:]
    except IOError:
        print("Error: can\'t read the annovar output file %s" % paras['lof_file'])
        sys.exit()
        return
    else:
        pass
        fh.close()

    try:
        fh = open(anvfile, "r")
        fw = open(newoutfile, "w")
        strs = fh.read()
        sum=0
        for line in strs.split('\n'):
            cls=line.split('\t')
            if len(cls)>1:
                gene_name=cls[6]
                if cls[6] == 'Gene.refGene':
                    gene_name='Gene'
#some with multiple genes, so one gene by one gene  to annote
                gdi_temp=['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']
                rvis_temp=['.', '.']
                lof_temp=['.']
                sum=sum+1
                for gg in gene_name.split(','):
                    line_out=line+"\t"+gg
                    line_out=get_gdi_rvis_lof(gg,line_out,gdi,gdi_temp)
                    line_out=get_gdi_rvis_lof(gg,line_out,rvis,rvis_temp)
                    line_out=get_gdi_rvis_lof(gg,line_out,lof,lof_temp)
                    fw.write("%s\n" % line_out)

#        fh.write("This is my test file for exception handling!!")
    except IOError:
        print("Error: can\'t read/write the annovar output file %s %s" % (anvfile,newoutfile))
        sys.exit()
        return
    else:
        pass
        fh.close()
        fw.close()

    return(sum)

def check_genes(anvfile):
#check with multiple genes, so one gene by one gene  to annote
    newoutfile=anvfile+".grl_p"
    try:
        fh = open(anvfile, "r")
        fw = open(newoutfile, "w")
        strs = fh.read()
        sum=0
        for line in strs.split('\n'):
            cls=line.split('\t')
            if len(cls)>1:
                gene_name=cls[6]
                if cls[6] == 'Gene.refGene':
                    gene_name='Gene'
#some with multiple genes, so one gene by one gene  to annote
                sum=sum+1
                for gg in gene_name.split(','):
                    line_out=re.sub("^[Cc][Hh][Rr]","",line)+"\t"+gg
                    #line_out=line+"\t"+gg
                    # re.sub("[Cc][Hh][Rr]","",keys)
                    fw.write("%s\t\n" % line_out)

    except IOError:
        print("Error: can\'t read/write the annovar output file %s %s" % (anvfile,newoutfile))
        sys.exit()
        return
    else:
        pass
        fh.close()
        fw.close()

    return(sum)



def sum_of_list(list):
    sum=0
    for i in list:
        sum=sum+i
    return(sum)

def classfy(CBP,Allels_flgs,cls):
    BPS=["Pathogenic","Likely pathogenic","Benign/Likely benign","Uncertain significance"]
    PAS_out=-1
    BES_out=-1
    BPS_out=3 # BPS=[4]:Uncertain significance
    # CBP[0]:Therapeutic(2100) CBP[1]:Diagno  CBP[2]:Progno CBP[3]:Mutation(1100) CBP[4]:Variant_freq CBP[5]:Potential_germ
    # CBP[6]: Populatio(1100)  CBP[7]:Germline dat(2201) CBP[8]:Somatic dat(2100) CBP[9]:Predict_dama(2201) 
    # CBP[10]:  Path(2100)  CBP[11] : Pubs
    if CBP[0]==2 and CBP[3]==1 and CBP[6]==1 and CBP[7]==2 and CBP[8]==2 and  CBP[9]==2 and  CBP[10]==2:
        BPS_out=0
    if CBP[0]==1 and CBP[3]==1 and CBP[6]==1 and CBP[7]==2 and CBP[8]>=1 and  CBP[9]==2 and  CBP[10]>=1:
        BPS_out=1

    if CBP[0]==0 and CBP[3]==0 and CBP[6]==0 and CBP[7]==0 and CBP[8]==0 and  CBP[9]==0 and  CBP[10]==0:
        BPS_out=3
    if CBP[0]==0 and CBP[3]==0 and CBP[6]==0 and CBP[7]>=0 and CBP[8]==0 and  CBP[9]<=1 and  CBP[10]==0:
        BPS_out=2

# EVS=[1, None, None, 1, None, None, 1, 2, 2, 2, 2, None]
#     [1, None, None, 1, None, None, 1, 0, 1, 2, 2, None]

    return(BPS[BPS_out])



def check_Thera(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Therapeutic: 
    2 FDA approved or investigational with strong evidence
    1 FDA approved for different tumor type; investigational therapies with some evidence
    0 Cancer genes: none
    0 None
    '''
    global add_d;
    global cgi_d;
    level=0 # ABCD
    cls=line.split('\t')
    clstt=cls[Funcanno_flgs['Otherinfo']].split(';')
    cancer_type="CANCER"
    if (len(clstt[0])>0):
        cancer_type=clstt[0]
    gene_tr=cls[Funcanno_flgs['Gene']]
    func=cls[Funcanno_flgs['Func.refGene']]
    exonfunc=cls[Funcanno_flgs['Func.refGene']]
    # ABL1:NM_005157:exon6:c.C944T:p.T315I,ABL1:NM_007313:exon6:c.C1001T:p.T334I
    # AAChange.refGene
    line_tmp=cls[Funcanno_flgs['Gene']]+" "+cls[Funcanno_flgs['Func.refGene']]+" "+cls[Funcanno_flgs['ExonicFunc.refGene']]+" "+cancer_type
    line_tmp2=cls[Funcanno_flgs['AAChange.refGene']]
    line_tmp2_sp=line_tmp2.split(',')
    exon_func=cls[Funcanno_flgs['ExonicFunc.refGene']]
    marker_key0=gene_tr+"_"+"mut_any"
    for cls0 in line_tmp2_sp:
        cls0_1=cls0.split(':')
        if(len(cls0)>1 and len(line_tmp2_sp)>0 and len(cls0_1)==5 ):
            cls0_1=cls0.split(':')
            gene=cls0_1[0]
            transc=cls0_1[1]
            exon=re.sub('exon','',cls0_1[2])
            cdna_change=re.sub('c.','',cls0_1[3])
            amino_change=re.sub('p.','',cls0_1[4])
            ltt=len(amino_change)
            codon_num=amino_change[1:ltt-1]
            #print gene, transc,exon,cdna_change,amino_change,cancer_type 
            marker_key=gene+"_"+amino_change
            marker_key0=gene+"_"+"mut_any"
            marker_key1=gene+"_"+"exon_"+exon+"_any"
            marker_key2=gene+"_"+"codon_"+codon_num+"_any"
            marker_key00=""       
            marker_key11=""       
            marker_key22=""       
            if(cls[Funcanno_flgs['ExonicFunc.refGene']]=="nonsynonymous SNV"):
                marker_key00=gene+"_"+"missense_any"
                marker_key11=gene+"_"+"exon_"+exon+"_missense"
                marker_key22=gene+"_"+"codon_"+codon_num+"_missense"
                
            if exon_func.find("frameshift")>=0 and exon_func.find("nonframe")<0 : 
                marker_key00=gene+"_"+"frameshift_any"
                marker_key11=gene+"_"+"exon_"+exon+"_frameshift"
                marker_key22=gene+"_"+"codon_"+codon_num+"_frameshift"

            if exon_func.find("stopgain")>=0 or exon_func.find("stoploss")>=0:  
                marker_key00=gene+"_"+"nonsense_any"
                marker_key11=gene+"_"+"exon_"+exon+"_nonsense"
                marker_key22=gene+"_"+"codon_"+codon_num+"_nonsense"

            if exon_func.find("deletion")>=0 :  
                marker_key00=gene+"_"+"deletion_any"
                marker_key11=gene+"_"+"exon_"+exon+"_deletion"
                marker_key22=gene+"_"+"codon_"+codon_num+"_deletion"
            if exon_func.find("insertion")>=0 :  
                marker_key00=gene+"_"+"insertion_any"
                marker_key11=gene+"_"+"exon_"+exon+"_insertion"
                marker_key22=gene+"_"+"codon_"+codon_num+"_insertion"
 
            #deletion frameshift indel missense nonsense_any
            # nonsynonymous SNV;stopgain/stoploss(nonsense);frameshift insertion/deletion/substitution; nonframeshift insertion/deletion/substitution;
            default_s=""
            add_list=add_markers_dict.get(marker_key,default_s)+add_markers_dict.get(marker_key0,default_s)+add_markers_dict.get(marker_key00,default_s)+add_markers_dict.get(marker_key1,default_s)+add_markers_dict.get(marker_key11,default_s)+add_markers_dict.get(marker_key2,default_s)+add_markers_dict.get(marker_key22,default_s)
            cgi_list=cgi_markers_dict.get(marker_key,default_s)+cgi_markers_dict.get(marker_key0,default_s)+cgi_markers_dict.get(marker_key00,default_s)+cgi_markers_dict.get(marker_key1,default_s)+cgi_markers_dict.get(marker_key11,default_s)+cgi_markers_dict.get(marker_key2,default_s)+cgi_markers_dict.get(marker_key22,default_s)
            #print add_list
            level_AB="0"
            level_CD="0"
            level=0 # ABCD
            for i in add_list.split(","):
                #print i
                if(len(i)>0):
                    pos=int(i)
                    level="C/D-0"
                    level_CD="1"
                    level=1
                    #print add_d[pos]
            #print cgi_list
            for i in cgi_list.split(","):
                #print i
                if(len(i)>0):
                    pos=int(i)
                    #print cgi_d[pos][10] # Evidence level in cgi
                    #print cgi_d[pos][6] # Drug status/approved
                    #print cgi_d[pos][15],cancer_type # cancer type
                    if(   re.findall('Pre-clinical', cgi_d[pos][10], flags=re.IGNORECASE) or  re.findall('Case Report', cgi_d[pos][10], flags=re.IGNORECASE) ):
                        level="C/D-1"
                        level=1
                    if(   re.findall('trial', cgi_d[pos][10], flags=re.IGNORECASE) or  re.findall('trial', cgi_d[pos][6], flags=re.IGNORECASE) ):
                        level="C/D-1"
                        level_CD="1"
                        level=1
                    if(   re.findall('guidelines', cgi_d[pos][10], flags=re.IGNORECASE) or  re.findall('approved', cgi_d[pos][6], flags=re.IGNORECASE)   ):
                        level="A/B-1"
                        level_AB="1"
                        level=2
                    if( not  re.findall(cancer_type, cgi_d[pos][15], flags=re.IGNORECASE)   ):
                        level="C/D-2"
                        level_CD="1"
                        level=1

            #print level_AB,level_CD
            if level_AB=="1":  level=2  # in case overlapped by level_CD=1
            
            

            '''
            default_s="NFDa"
            #print marker_key, marker_key0,marker_key00,  marker_key1,marker_key11,  marker_key2,marker_key22 
            print add_markers_dict.get(marker_key,default_s)
            print add_markers_dict.get(marker_key0,default_s),add_markers_dict.get(marker_key00,default_s)
            print add_markers_dict.get(marker_key1,default_s),add_markers_dict.get(marker_key11,default_s)
            print add_markers_dict.get(marker_key2,default_s),add_markers_dict.get(marker_key22,default_s)
            default_s="NFDc"
            print cgi_markers_dict.get(marker_key,default_s)
            print cgi_markers_dict.get(marker_key0,default_s),cgi_markers_dict.get(marker_key00,default_s)
            print cgi_markers_dict.get(marker_key1,default_s),cgi_markers_dict.get(marker_key11,default_s)
            print cgi_markers_dict.get(marker_key2,default_s),cgi_markers_dict.get(marker_key22,default_s)
t   
            '''
    return(level)
    #print line_tmp

def check_Diagno(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Diagnostic: 
    In PG or reported evidence with consensus
    not in PG but with convincing published data
    Cancer genes: none
    None
    ''' 
    Diagno=0
    #return(Diagno)

def check_Progno(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Prognostic: 
    In PG or reported evidence with consensus
    not in PG but with convincing published data
    Cancer genes: none
    None
    ''' 
    Progno=0
    #return(Progno)

def check_Mut(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Mutation type:
    1 Activating, LOF (missense, nonsense, indel, splicing), CNVs, fusions
    1 Activating, LOF (missense, nonsense, indel, splicing), CNVs, fusions
    0 Functionally unknown; mostly missense, in-frame indels; less commonly,other types
    0 Functionally benign or unknown; mostly missense; less commonly, other types
    '''

    cls=line.split('\t')
    funcs_tmp=["nonsynonymous","missense","nonsense","frameshift","splic","stopgain","stoplost","CNV","fusion"]
    funcs_tmp2="nonframe"
    line_tmp=cls[Funcanno_flgs['Func.refGene']]+" "+cls[Funcanno_flgs['ExonicFunc.refGene']]
    Mut=0 # 0 for Tire3/4; 1 for Tire 1/2
    VS_t1=0
    VS_t2=0
    VS_t3=0
    dbscSNV_cutoff=0.6    #either score(ada and rf) >0.6 as splicealtering
    # Funcanno_flgs={'Func.refGene':0,'ExonicFunc.refGene':0
    for fc in funcs_tmp:
        if line_tmp.find(fc)>=0 and line_tmp.find(funcs_tmp2)<0 :
            VS_t1=1
            break
    try:
        if lof_genes_dict[ cls[Funcanno_flgs['Gene']] ] == '1' :
            VS_t2=1
    except KeyError:
        VS_t2=0
    else:
        pass
    # begin check the site in  affect the splicing
    try:
        if float(cls[Funcanno_flgs['dbscSNV_RF_SCORE']])>dbscSNV_cutoff or float(cls[Funcanno_flgs['dbscSNV_ADA_SCORE']])>dbscSNV_cutoff:
            VS_t3=1
    except ValueError:
        pass
    else:
        pass
    if VS_t1 !=0 and VS_t2 != 0 :
        Mut=1
    if VS_t3 !=0 and VS_t2 != 0:
        Mut=1
    #print "mut=",Mut
    return (Mut)



def check_VF(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Variant frequencies
    1 Mostly mosaic
    1 Mostly mosaic
    0 Mosaic or nonmosaic
    0 Mostly nonmosaic (VAF, approximately 50% or 100%)
    '''
    VF=0;
    #return(VF)
def check_PotG(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Potential germline
    Mostly nonmosaic (VAF approximately 50% or 100%)
    Mostly nonmosaic (VAF approximately 50% or 100%)
    Mostly nonmosaic (VAF approximately 50% or 100%)
    Mostly nonmosaic (VAF, approximately 50% or 100%)
    '''
    PotG=1
    #return (PotG)

def check_PopD(line,Freqs_flgs,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Population database: ESP, dbSNP, 1000Genome, ExAC
    1  Absent or extremely low MAF
    1  Absent or extremely low MAF
    1  Absent or extremely low MAF
    0  MAF>1% in the general population; or high MAF in some ethnic populations
    '''
    MAF_cutoff=0.005
    PopD=0;
    cls=line.split('\t')
    Freqs_3pops={'1000g2015aug_all':0,'esp6500siv2_all':0,'ExAC_ALL':0}
    # Freqs_flgs
 
    tt=1;
    for key in Freqs_flgs.keys():
        if(cls[Freqs_flgs[key]]!='.'): # absent in all  controls
            tt=tt*0;
    if tt==1:
        PopD=1

    for key in Freqs_3pops.keys():
        try:
            if (cls[Freqs_flgs[key]]!='.' and float(cls[Freqs_flgs[key]])>0.01): PopD=0 #  MAF>1%
            if (cls[Freqs_flgs[key]]!='.' and float(cls[Freqs_flgs[key]])<MAF_cutoff): PopD=1  #  extremely low MAF

        except ValueError:
            pass
        else:
            pass

    #print "PopD=",PopD,cls[Freqs_flgs['1000g2015aug_all']],cls[Freqs_flgs['esp6500siv2_all']],cls[Freqs_flgs['ExAC_ALL']]
    return (PopD)

def check_GermD(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Germline database: HGMD, ClinVar
    2 May or may not be present
    2 May or may not be present
    0 Absent or downgraded from pathogenic to VUS
    1 Absent or present but downgraded to benign/likely benign
    '''
    GermD=0
    cls=line.split('\t')

    line_tmp2=cls[Funcanno_flgs['CLINSIG']]
    if line_tmp2.find("enign")<0 and line_tmp2.find("athogenic")>=0:
        GermD=2
    if line_tmp2.find("ikely benign")>=0 or line_tmp2.find("enign")>=0:
        GermD=1
    if line_tmp2.find("enign")>=0 and line_tmp2.find("athogenic")>=0:
        GermD=0
    if line_tmp2.find("ncertain significance")>=0 :
        GermD=0
    #print "GermD=",GermD,cls[Funcanno_flgs['CLINSIG']]
    return(GermD)


def check_SomD(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Somatic database: COSMIC, My Cancer Genome, TCGA
    2 Most likely present
    1 Likely present
    0 Absent or present without association to specific tumors (potential germline VUS); present but in very few cases
    0 Absent or present without association to specific tumors (potential rare germline polymorphism)
    ''' # cosmic70    ID=COSM12560;OCCURENCE=60(haematopoietic_and_lymphoid_tissue)
    #ICGC_Id ICGC_Occurrence MU31370893  COCA-CN|1|187|0.00535,PRAD-CA|1|124|0.00806,SKCA-BR|1|66|0.01515,MELA-AU|2|183|0.01093
    SomD=0;
    cls=line.split('\t')

    if cls[Funcanno_flgs['cosmic70']]!="." or cls[Funcanno_flgs['ICGC_Id']]!=".":
        SomD=1 
    if cls[Funcanno_flgs['cosmic70']]=="." and cls[Funcanno_flgs['ICGC_Id']]==".":
        SomD=0
    if cls[Funcanno_flgs['cosmic70']]!="." and cls[Funcanno_flgs['ICGC_Id']]!=".":
        SomD=2 
    return(SomD)
    


def check_PreP(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Predictive software: SIFT, PolyPhen2, MutTaster, CADD, MetaSVM
   2 Mostly damaging; information to be used for reference only
   2 Mostly damaging; information to be used for reference only
   0 Variable; information to be used for reference only
   1 Mostly benign; information to be used for reference only
    '''
    # MetaSVM SIFT Polyphen2_HDIV MetaLR FATHMM  MutationTaster
    sift_cutoff=0.05 #SIFT_score,SIFT_pred, The smaller the score the more likely the SNP has damaging effect
    metasvm_cutoff=0 # greater scores indicating more likely deleterious effects
    cutoff_conserv=2 # for GERP++_RS

    dam=0;
    var=0;
    ben=0;
    PreP=0;

    cls=line.split('\t')
    try:
        if float(cls[Funcanno_flgs['MetaSVM_score']]) <  metasvm_cutoff:
            ben=ben+1
        else:
            dam=dam+1
    except ValueError:  
        var=var+1
    else:
        pass

    try:
        if float(cls[Funcanno_flgs['SIFT_score']]) >= sift_cutoff:
            ben=ben+1
        else:
            dam=dam+1
    except ValueError:  # the sift absent means many:  synonymous indel  stop, but synonymous also is no impact
        var=var+1
    else:
        pass


    if cls[Funcanno_flgs['Polyphen2_HDIV_pred']] == "P" or cls[Funcanno_flgs['Polyphen2_HDIV_pred']] == "D":
        dam=dam+1
    if cls[Funcanno_flgs['Polyphen2_HDIV_pred']] == "B" :
        ben=ben+1
    if cls[Funcanno_flgs['Polyphen2_HDIV_pred']] == "." :
        var=var+1

    if cls[Funcanno_flgs['MetaLR_pred']] == "D":
        dam=dam+1
    if cls[Funcanno_flgs['MetaLR_pred']] == "T" :
        ben=ben+1
    if cls[Funcanno_flgs['MetaLR_pred']] == "." :
        var=var+1


    if cls[Funcanno_flgs['FATHMM_pred']] == "D":
        dam=dam+1
    if cls[Funcanno_flgs['FATHMM_pred']] == "T" :
        ben=ben+1
    if cls[Funcanno_flgs['FATHMM_pred']] == "." :
        var=var+1

    if cls[Funcanno_flgs['MutationTaster_pred']] == "A" or cls[Funcanno_flgs['MutationTaster_pred']] == "D":
        dam=dam+1
    if cls[Funcanno_flgs['MutationTaster_pred']] == "P":
        ben=ben+1
    if cls[Funcanno_flgs['MutationTaster_pred']] == "." :
        var=var+1
    
    if cls[Funcanno_flgs['GERP++_RS']] == ".": 
        var=var+1
    else:
        if float(cls[Funcanno_flgs['GERP++_RS']])>= cutoff_conserv:
            dam=dam+1
        else:
            ben=ben+1
        




    if dam >3: PreP=2;
    if ben >3: PreP=1;
    if var >3: Prep=0;
    if dam==ben: PreP=0;

    #print "PreP=",PreP,dam,ben,var
    return(PreP)

def check_Path(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Pathway involvement
    2 Disease-associated pathways
    1 Involve disease-associated pathways or pathogenic pathways
    0 May or may not involve disease-associated pathways
    0 May or may not involve disease-associated pathways
    '''
    Path=0;
#   cancer_pathway_dic{}
#   cancers_gene_dict{}

    cls=line.split('\t')
    try:
        if cancer_pathway_dict[ cls[Funcanno_flgs['Gene']] ] == '1' :
            Path=1
    except KeyError:
        pass
    else:
        pass
    try:
        if cancers_gene_dict[ cls[Funcanno_flgs['Gene']] ] == '1' :
            Path=2
    except KeyError:
        pass
    else:
        pass
    #print "Path=",Path
    return(Path)
    



def check_Pubs(line,Funcanno_flgs,Allels_flgs,lof_genes_dict):
    '''Publications: functional study, population study, other
    Therapeutic/Diagnostic/Prognostic: reported evidence with consensus
    Therapeutic: evidence of using FDA-approved therapies for different tumor types; phase 2 or 3 clinical trials for investigational therapies; Diagnostic/Prognostic: multiple lines of reported evidence without consensus
    None or no convincing evidence to determine clinical/biological significance
    Reported evidence supportive of benign/likely benign; or none
    '''
    Pubs=1;

    #return(Pubs)




def assign(BP,line,Freqs_flgs,Funcanno_flgs,Allels_flgs):

    CBP=[0,0,0,0,0,0,0,0,0,0,0,0]

    Therapeutic=check_Thera(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[0]=Therapeutic

    Diagnosis=check_Diagno(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[1]=Diagnosis

    Prognosis=check_Progno(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[2]=Prognosis

    Mutation_type=check_Mut(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[3]=Mutation_type

    Variant_freq=check_VF(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[4]=Variant_freq

    Potential_germ=check_PotG(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[5]=Potential_germ

    Population_data=check_PopD(line,Freqs_flgs,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[6]=Population_data

    Germline_data=check_GermD(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[7]=Germline_data

    Somatic_data=check_SomD(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[8]=Somatic_data
    
    Predict_pathoge=check_PreP(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[9]=Predict_pathoge


    Pathway_invol=check_Path(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[10]=Pathway_invol

    Publications=check_Pubs(line,Funcanno_flgs,Allels_flgs,lof_genes_dict)
    CBP[11]=Publications

    #print CBP

    cls=line.split('\t')


    cls=line.split('\t')
    if len(cls)>1:#esp6500siv2_all 1000g2015aug_all ExAC_ALL
        BP_out=classfy(CBP,Allels_flgs,cls)
        line_t="%s EVS=%s" %(BP_out,CBP)

        #print("%s " % BP_out)
        BP_out=line_t
        pass
    #BP=BP_out
    return(BP_out)


def search_key_index(line,dict):
    cls=line.split('\t')
    for key in dict.keys():
        for i in range(1,len(cls)):
            ii=i-1
            if key==cls[ii]:
                dict[key]=ii
                break
    return

def my_inter_var_can(annovar_outfile):
    newoutfile=annovar_outfile+".grl_p"
    newoutfile2=annovar_outfile+".cancervar"

    Freqs_flgs={'1000g2015aug_all':0,'esp6500siv2_all':0,'ExAC_ALL':0,'ExAC_AFR':0,'ExAC_AMR':0,'ExAC_EAS':0,'ExAC_FIN':0,'ExAC_NFE':0,'ExAC_OTH':0,'ExAC_SAS':0}
    Funcanno_flgs={'Func.refGene':0,'ExonicFunc.refGene':0,'AAChange.refGene':0,'Gene':0,'Gene damage prediction (all disease-causing genes)':0,'CLNDBN':0,'CLNACC':0,'CLNDSDB':0,'dbscSNV_ADA_SCORE':0,'dbscSNV_RF_SCORE':0,'GERP++_RS':0,'LoFtool_percentile':0,'Interpro_domain':0,'rmsk':0,'SIFT_score':0,'phyloP46way_placental':0,'Gene.ensGene':0,'CLINSIG':0,'CADD_raw':0,'CADD_phred':0,'avsnp144':0,'AAChange.ensGene':0,'AAChange.knownGene':0,'MetaSVM_score':0,'cosmic70':0,'ICGC_Id':0,'ICGC_Occurrence':0,'Otherinfo':0,'Polyphen2_HDIV_pred':0,'MetaLR_pred':0,'MutationTaster_pred':0,'FATHMM_pred':0}
    Allels_flgs={'Chr':0,'Start':0,'End':0,'Ref':0,'Alt':0}
# ExAC_ALL esp6500siv2_all   1000g2015aug_all  SIFT_score    CADD_raw    CADD_phred  GERP++_RS   phyloP46way_placental  dbscSNV_ADA_SCORE   dbscSNV_RF_SCORE   Interpro_domain

    try:
        fh=open(newoutfile, "r")
        fw=open(newoutfile2, "w")
        strs=fh.read()
        line_sum=0;
        print("Notice: Begin the variants interpretation by CancerVar ")
        fw.write("#%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tclinvar: %s \t CancerVar: %s \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ("Chr","Start","End","Ref","Alt","Ref.Gene","Func.refGene","ExonicFunc.refGene", "Gene.ensGene","avsnp144","AAChange.ensGene","AAChange.refGene","Clinvar","CancerVar and Evidence","Freq_ExAC_ALL", "Freq_esp6500siv2_all","Freq_1000g2015aug_all", "CADD_raw","CADD_phred","SIFT_score","GERP++_RS","phyloP46way_placental","dbscSNV_ADA_SCORE", "dbscSNV_RF_SCORE", "Interpro_domain","AAChange.knownGene","rmsk","MetaSVM_score","Freq_ExAC_POPs","OMIM","Phenotype_MIM","OrphaNumber","Orpha"  ))
        for line in strs.split('\n'):
            BP="UNK" # the inter of pathogenetic/benign
            clinvar_bp="UNK"
            cls=line.split('\t')
            if len(cls)<2: break
            if line_sum==0:
                search_key_index(line,Freqs_flgs)
                search_key_index(line,Funcanno_flgs)
                search_key_index(line,Allels_flgs)

            else:
                #begin check the BP status from clinvar
                line_tmp2=cls[Funcanno_flgs['CLINSIG']]
                if line_tmp2 != '.':
                    cls3=line_tmp2.split(';')
                    clinvar_bp=cls3[0]

                cancervar_bp=assign(BP,line,Freqs_flgs,Funcanno_flgs,Allels_flgs)
                Freq_ExAC_POPs="AFR:"+cls[Freqs_flgs['ExAC_AFR']]+",AMR:"+cls[Freqs_flgs['ExAC_AMR']]+",EAS:"+cls[Freqs_flgs['ExAC_EAS']]+",FIN:"+cls[Freqs_flgs['ExAC_FIN']]+",NFE:"+cls[Freqs_flgs['ExAC_NFE']]+",OTH:"+cls[Freqs_flgs['ExAC_OTH']]+",SAS:"+cls[Freqs_flgs['ExAC_SAS']]
                OMIM="."
                mim2=mim2gene_dict2.get(cls[Funcanno_flgs['Gene']],".")
                mim1=mim2gene_dict.get(cls[Funcanno_flgs['Gene.ensGene']],".")
                if(mim1 !="."):
                   OMIM=mim1
                if(mim2 !="."):
                   OMIM=mim2
                Pheno_MIM=mim_pheno_dict.get(OMIM,".")
                orpha="";
                orpha_details="";
                # .;442835;;306;;.;
                for ort2 in Pheno_MIM.split(';'):
                    ort3=mim_orpha_dict.get(ort2,".")
                    if(ort3 !="."):
                        orpha=ort3+orpha
                for ort4 in orpha.split(';'):
                    if len(ort4)>0:
                         orpha_details=orpha_details+orpha_dict.get(ort4,".")+"~"
                if(orpha ==""):
                    orpha="."
                if(orpha_details ==""):
                    orpha_details="."



                fw.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tclinvar: %s \t CancerVar: %s \t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cls[Allels_flgs['Chr']],cls[Allels_flgs['Start']],cls[Allels_flgs['End']],cls[Allels_flgs['Ref']],cls[Allels_flgs['Alt']],cls[Funcanno_flgs['Gene']],cls[Funcanno_flgs['Func.refGene']],cls[Funcanno_flgs['ExonicFunc.refGene']], cls[Funcanno_flgs['Gene.ensGene']],cls[Funcanno_flgs['avsnp144']],cls[Funcanno_flgs['AAChange.ensGene']],cls[Funcanno_flgs['AAChange.refGene']],clinvar_bp,cancervar_bp,cls[Freqs_flgs['ExAC_ALL']], cls[Freqs_flgs['esp6500siv2_all']], cls[Freqs_flgs['1000g2015aug_all']], cls[Funcanno_flgs['CADD_raw']],cls[Funcanno_flgs['CADD_phred']],cls[Funcanno_flgs['SIFT_score']],  cls[Funcanno_flgs['GERP++_RS']],cls[Funcanno_flgs['phyloP46way_placental']], cls[Funcanno_flgs['dbscSNV_ADA_SCORE']], cls[Funcanno_flgs['dbscSNV_RF_SCORE']], cls[Funcanno_flgs['Interpro_domain']],cls[Funcanno_flgs['AAChange.knownGene']],cls[Funcanno_flgs['rmsk']],cls[Funcanno_flgs['MetaSVM_score']],Freq_ExAC_POPs,OMIM,Pheno_MIM,orpha,orpha_details   ))
                #print("%s\t%s %s" % (line,clinvar_bp,cancervar_bp))

            line_sum=line_sum+1

    except IOError:
        print("Error: can\'t readi/write the annovar output files %s" % (newoutfile,newoutfile2))
        sys.exit()
        return
    else:
        fh.close()
        fw.close()
    return(line_sum)


def main():


    if platform.python_version()< '3.0.0'  :
        config=ConfigParser.ConfigParser()
    else:
        config=configparser.ConfigParser()





    parser = optparse.OptionParser(usage=usage, version=version, description=description)


    parser.add_option("-?", action="help", help=optparse.SUPPRESS_HELP, dest="help")
    parser.add_option("-v", action="version", help=optparse.SUPPRESS_HELP, dest="version")

    parser.add_option("-c", "--config", dest="config", action="store",
                  help="The config file of all options. it is for your own configure file.You can edit all the options in the configure and if you use this options,you can ignore all the other options bellow", metavar="config.ini")

    parser.add_option("-b", "--buildver", dest="buildver", action="store",
                  help="The genomic build version, it can be hg19 and will support GRCh37 hg18 GRCh38 later", metavar="hg19")


    parser.add_option("-i", "--input", dest="input", action="store",
                  help="The input file contains your variants", metavar="example/ex1.avinput")

    parser.add_option("--input_type", dest="input_type", action="store",
                  help="The input file type, it can be  AVinput(Annovar's format),VCF", metavar="AVinput")

    parser.add_option("-o", "--output", dest="output", action="store",
                  help="The prefix of output file which contains the results, the file of results will be as [$$prefix].cancervar ", metavar="example/myanno")


    group = optparse.OptionGroup(parser, "CancerVar Other Options")
    group.add_option("-t", "--database_cancervar", dest="database_cancervar", action="store",
            help="The  database location/dir for the CancerVar dataset files", metavar="cancervardb")
    group.add_option("-s", "--evidence_file", dest="evidence_file", action="store",
            help="User specified Evidence file for each variant", metavar="your_evidence_file")
    parser.add_option_group(group)
    group = optparse.OptionGroup(parser, "   How to add your own Evidence for each Variant",
    """ Prepare your own evidence  file as tab-delimited,the line format:
         (The code for additional evidence should be as: PS5/PM7/PP6/BS5/BP8 ;
         The format for upgrad/downgrade of criteria should be like: grade_PS1=2;
         1 for Strong; 2 for Moderate; 3 for Supporting)
            Chr Pos Ref_allele Alt_allele  PM1=1;BS2=1;BP3=0;PS5=1;grade_PM1=1
                                """)
    parser.add_option_group(group)



    group = optparse.OptionGroup(parser, "Annovar Options",
                                "Caution: check these options from manual of Annovar.")
    group.add_option("--table_annovar", action="store", help="The Annovar perl script of table_annovar.pl",metavar="./table_annovar.pl",dest="table_annovar")
    group.add_option("--convert2annovar", action="store", help="The Annovar perl script of convert2annovar.pl",metavar="./convert2annovar.pl",dest="convert2annovar")
    group.add_option("--annotate_variation", action="store", help="The Annovar perl script of annotate_variation.pl",metavar="./annotate_variation.pl",dest="annotate_variation")
    group.add_option("-d", "--database_locat", dest="database_locat", action="store",
            help="The  database location/dir for the annotation datasets", metavar="humandb")

    parser.add_option_group(group)
    group = optparse.OptionGroup(parser, "Examples",
                                """./CancerVar.py -c config.ini  # Run the examples in config.ini
                                 ./CancerVar.py  -b hg19 -i your_input  --input_type=VCF  -o your_output
                                """)
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    #(options,args) = parser.parse_args()
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit()

    print("%s" %description)
    print("%s" %version)
    print("Notice: Your command of CancerVar is %s" % sys.argv[:])




    if os.path.isfile("config.ini"):
        config.read("config.ini")
        sections = config.sections()
        for section in sections:
            ConfigSectionMap(config,section)
    else:
        print("Error: The default configure file of [ config.ini ] is not exit! Please redownload the CancerVar.")
        sys.exit()

#begin to process user's options:
    if options.config != None:
        if os.path.isfile(options.config):
            config.read(options.config)
            sections = config.sections()
            for section in sections:
                ConfigSectionMap(config,section)
        else:
            print("Error: The config file [ %s ] is not here,please check the path of your config file." % options.config)
            sys.exit()

    if options.buildver != None:
        paras['buildver']=options.buildver
    if options.database_locat != None:
        paras['database_locat']=options.database_locat
    if options.input != None:
        paras['inputfile']=options.input
    if options.input_type != None:
        paras['inputfile_type']=options.input_type
    if options.output != None:
        paras['outfile']=options.output
    if options.evidence_file != None:
        paras['evidence_file']=options.evidence_file
        print("Warning: You provided your own evidence file [ %s ] for the CancerVar." % options.evidence_file)
    if options.database_cancervar != None:
        paras['database_cancervar']=options.database_cancervar

    #paras['ps1_aa'] = paras['ps1_aa']+'.'+paras['buildver']
    #paras['ps4_snps'] = paras['ps4_snps']+'.'+paras['buildver']
    #paras['bs2_snps'] = paras['bs2_snps']+'.'+paras['buildver']
    paras['exclude_snps'] = paras['exclude_snps']+'.'+paras['buildver']

    if options.table_annovar != None:
        if os.path.isfile(options.table_annovar):
            paras['table_annovar']=options.table_annovar
        else:
            print("Error: The Annovar file [ %s ] is not here,please download ANNOVAR firstly: http://www.openbioinformatics.org/annovar"
                    % options.table_annovar)
            sys.exit()
    if options.convert2annovar != None:
        if os.path.isfile(options.convert2annovar):
            paras['convert2annovar']=options.convert2annovar
        else:
            print("Error: The Annovar file [ %s ] is not here,please download ANNOVAR firstly: http://www.openbioinformatics.org/annovar"
                    % options.convert2annovar)
            sys.exit()
    if options.annotate_variation != None:
        if os.path.isfile(options.annotate_variation):
            paras['annotate_variation']=options.annotate_variation
        else:
            print("Error: The Annovar file [ %s ] is not here,please download ANNOVAR firstly: http://www.openbioinformatics.org/annovar"
                    % options.annotate_variation)
            sys.exit()


    if not os.path.isfile(paras['inputfile']):
        print("Error: Your input file [ %s ] is not here,please check the path of your input file." % paras['inputfile'])
        sys.exit()
    if  not os.path.isfile(paras['evidence_file']) and paras['evidence_file']!="None":
        print("Warning: Your specified evidence file [ %s ] is not here,please check the path of your evidence file." % paras['evidence_file'])
        print("         Your analysis will begin without your specified evidence.")





    print ("INFO: The options are %s " % paras)
    check_downdb()
    check_input()
    check_annovar_result() #  to obtain myanno.hg19_multianno.csv
    annovar_outfile=paras['outfile']+"."+paras['buildver']+"_multianno.txt"
    read_datasets()
    #sum1=check_gdi_rvis_LOF(annovar_outfile)
    sum1=check_genes(annovar_outfile)
    sum2=my_inter_var_can(annovar_outfile)

    inputfile=paras['inputfile']
    if os.path.isfile(inputfile):
        count = 0
        thefile = open(inputfile, 'rb')
        while True:
            buffer = thefile.read(8192*1024)
            if not buffer:
                break
            count += buffer.count('\n')
        thefile.close( )
        print ("Notice: About %d lines in your input file %s " % (count,inputfile))

    outfile=annovar_outfile+".cancervar"
    if os.path.isfile(outfile):
        print ("Notice: About %d variants has been processed by CancerVar" % (sum2-1))
        print ("Notice: The CancerVar is finished, the output file is [ %s.cancervar ]" % annovar_outfile)
    else:
        print ("Warning: The CancerVar seems not run correctly, please check your inputs and options in configure file")

    print("%s" %end)




if __name__ == "__main__":
    main()
