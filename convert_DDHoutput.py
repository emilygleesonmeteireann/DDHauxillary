#!/usr/bin/python

import numpy as np
from netCDF4 import Dataset
from subprocess import check_output
from subprocess import run as sbp_run
from glob import glob
import os
import os.path 
import datetime
import tarfile
import glob

# Set paths for lfa tools in DDH Toolbox and experiment output directory
# Author: Marvin Kaehnert, marvink@met.no
# INFO: this is far from optimal
#########################################################################
iwrite   = True    # Select whether or not to write output netcdf file
expnam   = 'CY46E_DDH_ISLAS_SCA_LWTHRESH/'
lfa_path = '/perm/famk/convert_DDH/lfa/'
datadir  = '/ec/res4/scratch/famk/hm_home/'
outdir   = '/perm/famk/convert_DDH/out/'
var_txt_path = '/perm/famk/convert_DDH/'
# specifcs for experiment/ depends where data is stored. Might not always be needed. See DDHdata an bottom of script
YY = '2014'
MM = '03'
DD = '20'
HH = '18'
##### Now set variabeles for DDH conversion
# the testfiles contain a 14 x 14 grid domain over Sodanylä
#TODO get rid of hard coding
nlevs  = 65         # model levels
nhlevs = nlevs+1    # half levels
nlon = 32           # y-dimension of output subdomain, when using find_closest fucntion
nlat = 25           # x-dimension of output subdomain, -''-
print('Initialized')
#########################################################################

def file_list(outputdir):
    '''
    fns, files, times = file_list(outputdir)
        outputdir = full path to model output
        fns = list of full path to each file
        files = list of file names
        times = numpy array of times in decimal hours       
    '''
    fns = [x for x in glob.glob(outputdir + '/DHF*')]
    fns.sort()
    files = [os.path.basename(x) for x in fns]
    times = np.array([np.float32(s[10:14]) for s in files])
    return fns, files, times


def variable_list(fn, lfalaf):
    '''
    var_name,var_size = variable_list(fn)
        fn = full path to single output file
        lfalaf = full path to lfalaf script
        var_name = list of names of variables
        var_size = array of sizes of variables
    '''
    var_text = check_output([lfalaf,fn])
    var_text = var_text.decode('ascii').split('\n')[1:-1]
    var_name = [s[31:] for s in var_text]
    var_size = np.array([np.int32(s[23:28].strip(' ')) for s in var_text])  # this one might cause problems, depending on size
    return var_name, var_size


def vertical_levels(nlevs,psurf):#,model_path):
    ''' 
    ahalf, bhalf, plevs = vertical_levels(nlevs,psurf,model_path)
        nlevs = number of vertical levels
        psurf = pressure at the surface in hPa
        model_path = path to main model directory
        ahalf = a half levels
        bhalf = b half levels
        plevs = pressure levels in hPa
        This function calls the HIRLAM Vertical Levels script to obtain the ahalf levels
        and bhalf levels, and to calculate the vertical full levels in pressure coordinates.
    '''
    var_lev_scr = 'Vertical_levels.pl'
    ahalf = np.fromstring(check_output([var_lev_scr,str(nlevs),'AHALF']).decode('ascii').replace('\n',''),sep=',')
    bhalf = np.fromstring(check_output([var_lev_scr,str(nlevs),'BHALF']).decode('ascii').replace('\n',''),sep=',')
    plevs = (ahalf + bhalf * psurf * 100) / 100
    return ahalf, bhalf, plevs


def create_new_var(var_name,sflag,cflag):
    '''
    new_var_info = create_new_var(var_name)
        var_name = list of names of variables from output file
        new_var_info = list of meta data for variables where possible
        This loads the csv file containing variable data. It creates a list of new names
        for thr variables based on the data from the csv file where possible, or based on the
        original output names but in lower case and with special characters removed.
        
    '''
    fn = var_txt_path + 'variable_list.csv'
    var_list = check_output(['cat',fn]).decode('ascii').replace('\r\r\n',',')[:-1]
   # var_list = check_output(['cat',fn]).decode('ascii').replace('\r',',')[:-1]
    var_list = np.array(var_list.split(','))
    var_list = np.reshape(var_list,[len(var_list)//4,4])
    
    new_var_name = [s.lower().replace(' ','_') for s in vname]
    new_var_name = [s.replace('-','_') for s in new_var_name]
    new_var_name = [s.replace('.','_') for s in new_var_name]
    new_var_info = np.empty([len(vname),4],dtype=object)
    new_var_info[:,0] = new_var_name
    new_var_info[:,1] = var_name
    # small workaround for the indetical namend surf variables
    # not needed for default model runs
    if sflag:
        snams1 = ['surf_radtemp1','surf_efftemp1','surf_thflx1','surf_qflx1']
        snams0 = ['surf_radtemp0','surf_efftemp0','surf_thflx0','surf_qflx0']
        c1 = -1
        gg = np.where(new_var_info[:,1]=='SURF1')
        for g in gg[0]:
            c1 = c1+1
            new_var_info[g,0] = snams1[c1]
            new_var_info[g+1,0] = snams0[c1]
    for i in range(len(var_name)):
        try:
            indy = list(var_list[:,1]).index(var_name[i])
            new_var_info[i,:] = var_list[indy,:]
        except:
            pass
    # small workaround for the identical named cloud area fractions
    # should not happen in future runs, is a fail in cy43
    # yet there is also another cloud written out later on.. check if it is the same
    if cflag:
        snams1 = ['Cloud1','fail1_1','fail2_1','fail3_1','fail4_1','fail5_1','Cloud21']
        snams0 = ['Cloud0','fail1_0','fail2_0','fail3_0','fail4_0','fail5_0','Cloud20']
        c1 = -1
        gg = np.where(new_var_info[:,1]=='VNT1')
        for g in gg[0]:
            c1 = c1+1
            new_var_info[g,0] = snams1[c1]
            new_var_info[g+1,0] = snams0[c1]
            new_var_info[g,1] = snams1[c1]
            new_var_info[g+1,1] = snams0[c1]
    #print(new_var_info[:,0])

    ################## remove some of the variables that I am currently not interested in
    ################## so lets delete all the docd info (is still in test file if needed)
    nmask = ['docd',
            'tke', 
            'tq', 
            'tmyq',
            't2m',
            'pblt',
            'fail',
            'indice']

    ii = [i for i,x in enumerate(new_var_info[:,0]) if any([ m in x for m in nmask]) ]
    new_var_info = np.delete(new_var_info,ii,0) # delete all these rows
    return new_var_info,ii

##### NEW STUFF
def get_dimensions(size, nlat, nlon, nlevs,nfluxs):


        result = ['time']
        if size == 1:
            pass
        elif size == 11:
            result += ['diminfo']
        elif size == 17:
            result += ['dimdoc']
        elif size/(nlon*nlat) == 1:
            result += ['longitude','latitude']
        elif size/(nlon*nlat) == nlevs:
            result += ['longitude','latitude','level']
        elif size/(nlon*nlat) == nfluxs:
            result += ['longitude','latitude','halflevel']
        else:
            raise ValueError('Unknow size of a dimension for a variable',size)
        
        return result


def openNCfile(outdir,expnam,nlevs,times,nlat,nlon,var_names,
                   var_size,meta):
        # Set name of output file
        # Check if output file exists and confirm overwrite
        fnout = outdir + expnam[0:-1]+'.nc' # :D
        print(fnout)
        dumpflag = False
        if os.path.isfile(fnout):
            inp = input("Output file already exists. Overwrite?  (y/n)")
            if str(inp).lower() == 'y': 
                sbp_run(['rm','-f',fnout]) ##TODO::os.remove           
                dumpflag = True
        else:
            dumpflag = True
    
        # Create netcdf file and output
        if dumpflag:
            # Create new netcdf file
            dataset = Dataset(fnout, 'w', format='NETCDF4')
    
            # Create dimensions
            nlevs       = int(nlevs)
            levels      = dataset.createDimension('level',nlevs) # 65 * number of regions
            longitudes  = dataset.createDimension('longitude',nlon) 
            latitudes   = dataset.createDimension('latitude',nlat) 
            fluxes      = dataset.createDimension('halflevel',nlevs+1) # half levels -> nlevs +(1* number of fields)
            dimdoc      = dataset.createDimension('dimdoc',17)  # info of DDH domain
            diminfo     = dataset.createDimension('diminfo',11) # info of var dimension
            time        = dataset.createDimension('time', None)
    
            # Create dimension variables 
            Vlevels  = dataset.createVariable('level', int, ('level',))
            Vlons    = dataset.createVariable('longitude', float, ('longitude',))
            Vlats    = dataset.createVariable('latitude', float, ('latitude',))
            Vhlevels = dataset.createVariable('halflevel', int, ('halflevel',))
            Vdoc     = dataset.createVariable('dimdoc', int, ('dimdoc',))
            Vinfo    = dataset.createVariable('diminfo', int, ('diminfo',))
            Vtime    = dataset.createVariable('time', float, ('time',))
    
            # Create variables
            for vn,vs in zip(var_names,var_size):
                dataset.createVariable(vn,float,get_dimensions(vs,nlat,nlon,nlevs,nhlevs))

    
            # Write variable attributes
            Vlevels.units = ""
            Vlevels.long_name = "Vertical model levels, all regions"
            Vhlevels.long_name = "Vertical half levels, all regions"
            Vhlevels.units = ""
            Vdoc.long_name = "17 numbers from docfishier variable"
            Vdoc.units = ""
            Vinfo.long_name = "11 numbers for date and region info"
            Vinfo.units = ""
            Vtime.units = "hrs"
            Vtime.long_name = "Fractions of hours into the model run"
            for vn in var_names: # looping through variables
                if meta[vn][3] is not None:
                    dataset.variables[vn].units = meta[vn][3]
                if meta[vn][2] is not None:
                    dataset.variables[vn].long_name = meta[vn][2]
            
            # Write global attributes
            dataset.description = '''\
    Converted output from DDH using convert_lfa_nc.py. Written by Marvin Kaehnert (MET-Norway). 
    Visit www.umr-cnrm.fr/gmapdoc/IMG/pdf/ddh.pdf for detailed informations about DDH.
    '''
            dataset.history = "Created " + datetime.datetime.now().isoformat()
    
            # Write data to variables
            Vlevels[:] = np.arange(nlevs)+1
            Vhlevels[:] = np.arange(nhlevs)+1
            Vdoc[:]    = np.arange(17)+1
            Vinfo[:]   = np.arange(11)+1
            Vtime[:]   = times  #TODO: change to UTC timestep
    
            # Close and write file
            # dataset.close()
            return dataset

# shape data accordingly
def fillData(dataset, t, vn, data,nlat, nlon, nlevs,nfluxs):

    if len(data) == 1:
        print('single number data entry')
        dataset.variables[vn][t] = data
    else:
        #print(vn, data)
        #print(dataset.variables)
        #print(dataset.variables[vn])
        #print(dataset.variables[vn][t])
        #print(dataset.variables[vn][t][:])
        
        dim_names = get_dimensions(len(data), nlat, nlon, nlevs,nfluxs)
        dim_size = [ dataset.dimensions[n].size for n in dim_names[1:] ]
        
        #print(dim_names, dim_size)
        #TODO improve the lines below
        if len(dim_size)==1:
            dataset.variables[vn][t,:] = data.reshape(dim_size)
        elif len(dim_size)==2:
            dataset.variables[vn][t,:,:] = data.reshape(dim_size)
        elif len(dim_size)==3:
            dataset.variables[vn][t,:,:,:] = data.reshape(dim_size)

                    
# convert the DDH units into SI, for the standard units    
def convertUNITS(dataset):
    print('Start Units conversion')
    TT     = ['CT1'] 
    QX     = ['QL1','QI1','QR1','QS1','QG1','QV']
    RH     = ['Q1']
    rest   = ['EK1', 'EP1', 'U1', 'V1','W1','Cloud1']
    pp = dataset.variables['PP1'][:]
    const_CT = 85.99506148113663 # from DDHtool conversion list, this is 86400/cp
    cp = (const_CT/86400)**-1
    
    for vn in TT:   # convert thermal energy
        dataset.variables[vn][:] = ((dataset.variables[vn][:])/pp/cp).data
    for vn in QX:   # getvalues in g/kg
        dataset.variables[vn][:] = ((dataset.variables[vn][:])/pp*1000).data
    for vn in RH: # transfrom to %
        dataset.variables[vn][:] = ((dataset.variables[vn][:])/pp*100).data
    for vn in rest: # normal transform
        dataset.variables[vn][:] = ((dataset.variables[vn][:])/pp).data
    # now for tendencies:
    keys = dataset.variables.keys()
    # temperature
    TTEND = [k for k in keys if 'CT_' in k]
    for vn in TTEND:   # convert thermal energy
        dataset.variables[vn][:] = ((dataset.variables[vn][:])/pp/cp).data
    # microphysical species
    QTEND = [k for k in keys if k.startswith('Q') and len(k) > 2 and k[2]=='_']
    for vn in QTEND:   # getvalues in g/kg
        dataset.variables[vn][:] = ((dataset.variables[vn][:])/pp*1000).data
    print('Units converted')
###### END OF NEW STUFF

#%%
# Define paths to lfa scripts
lfac = lfa_path + 'lfac'
lfalaf = lfa_path + 'lfalaf'
lfa2lfp = lfa_path + 'lfa2lfp'
print('Paths set')


# only set up for a single experiment
#DDHdata = glob.glob(datadir+expnam+'/*/*/*/')[0]
# can change depdening on where DDH data is stored, FIXME
DDHdata = datadir+expnam+'/archive/'+YY+'/'+MM+'/'+DD+'/'+HH
# fix needed for some experiments of mine
fixvar = False 
exch  = ['QUPD1', 'QUPD0','QUPM1', 'QUPM0', 'TUPD1', 'TUPD0', 'TUPM1', 'TUPM0', 'EUPD1', 'EUPD0',
         'EUPM1', 'EUPM0', 'DUPD1', 'DUPD0', 'DUPM1', 'DUPM0', 'BUPD1', 'BUPD0','BUPM1', 'BUPM0',
         'W2UD1', 'W2UD0', 'W2UM1', 'W2UM0']
exch1 = ['HLCLD1','HLCLD0','HLCLM1','HLCLM0']


print(DDHdata)    
# Get list of files and variables
fns, files, times = file_list(DDHdata)
vname, vsize = variable_list(fns[0],lfalaf)
print('List of files')
# for gug testing specifc parts of data
# for shorter period
#fns = fns[500:1500]
#files = files[500:1500]
#times = times[500:1500]

# to lost every variable name in the DDH file (provides info on number of points)
# print vname

# Obtain new variable names and empty variables
sflag = True # True if surf problem in variable names (multiple SURF0 / SURF1)
cflag = True # Cloud cover is written out twice in AROME!
new_var,deli = create_new_var(vname,sflag,cflag) # deli are the deleted indexes to fix the starts/stops
if fixvar:
    for ii,v in zip(range(14,38),exch):
        new_var[ii,0] = v
    for ii,v in zip(range(-4,0),exch1):
        new_var[ii,0] = v
### we do not want to do this        
fnumb = len(files)
# fixing allocation to account for deleted variables
vsize2 = np.delete(vsize,deli)
print('Make chosen variables to dict')
meta = {d[0]: d for d in new_var}
var_names = new_var[:,0]
print(f'Variable names used for output:\n{var_names}')
# create dataset

dataset = openNCfile(outdir,expnam,nlevs,times,nlat,nlon,var_names,
                     vsize2,meta)



# Create list of where data for each variable starts and stops tops = dat_locs[1::2]in lfp file
dat_locs = np.ones(len(vsize)*2, dtype=int)
dat_locs[1::2] = vsize
dat_locs = np.cumsum(dat_locs)
starts = dat_locs[0::2]
stops = dat_locs[1::2]
# now delete the start and stop entries from the variables that were deleted, to extract correct variables.
starts = np.delete(starts,deli)
stops  = np.delete(stops,deli)
print('list where var starts stops')

# Loop over files, convert each to lfp and loop over variables to extract them to new_variables
tmp_fn = DDHdata + '/temp.lfp'
print('The file will contain '+ str(len(fns))+ 'time steps')
for i in range(len(fns)):
#for i in range(len(times)):
    sbp_run(['rm','-f',tmp_fn])
    sbp_run([lfa2lfp, fns[i], tmp_fn])
    fascii = check_output(['cat',tmp_fn]).decode('ascii').split('\n')
     
    for j in range(len(new_var)):
        data = np.array(fascii[starts[j]:stops[j]]).astype(np.float32)
        fillData(dataset, i, var_names[j], data, nlat, nlon, nlevs,nhlevs)
    print('Done with time step', i)
sbp_run(['rm','-f',tmp_fn])


convertUNITS(dataset)
dataset.close()
print('Done!')
    
    ###################################################################

