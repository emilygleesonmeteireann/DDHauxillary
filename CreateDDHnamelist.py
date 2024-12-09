import re
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import seaborn as sns
from netCDF4 import Dataset

sns.set(style='whitegrid')
# path to where the to-be.modified harmonie_namelists.pm is located 
os.chdir('/home/marvink/Documents/DDH/')
# model dataset of interest
dat = Dataset('https://thredds.met.no/thredds/dodsC/metusers/marvink/CY46DDH_ISLAS_REF.nc')
#%%

# fuctions to help define region to extract
def find_closest(dat,plon,plat):
    """
    Finds the closest grid point to any given coordinate
    
    Parameters:
    dat  = NetCDF dataset handler
    plon = longitude of interest (single entry)
    plat = latitude of interest (single entry)
    
    Returns:
    x = x-coordinate
    y = y-corrdinate
    """
    # get clostest x,y index to point
    lats = dat.variables['latitude'][:,:]
    lons = dat.variables['longitude'][:,:]
    abslat = np.abs(lats-plat)
    abslon= np.abs(lons-plon)
    c = np.maximum(abslon,abslat)
    x, y = np.where(c == np.min(c))
    x, y = x[0],y[0]
    return x,y,lats,lons

def check_define_ROI(dat,vnam,ts,lvl,plon,plat,xD,yD,cmap=plt.cm.viridis,
                     vlim=[np.nan,np.nan],onmap=True):
    """
    Explore region of interest (ROI) to extract with DDH. Plots field of choice. 
    Allows to modify the plot
    
    Parameters:
    dat  = NetCDF dataset handler
    vnam = variable name to plot from NetCDF file
    ts   = time step to plot, multiple entires possible as list e.g. [6,9]
    lvl  = model levels to plot, for now just single entries
    plon = longitude to focus region on (single entry)
    plat = latitude to focus region on (single entry)
    xD   = departure from x coordinate for ROI in the form x-xD[0], x+xD[1]
           needs to be a list
    yD   = departure from y coordinate for ROI in the form y-yD[0], y+yD[1]
           needs to be a list
    
    Parameters optional:
    cmap  = colormap to use in figure, default is viridis
    vlim  = colormap limits for the plot, if used give as list e.g. [273.15, 280]
    onmap = plots field on a map using cartopy, default = True
    
    Returns:
    x = x-coordinate
    y = y-corrdinate
    """
    # get coordinates
    x,y,lats,lons = find_closest(dat,plon,plat)
    
    for t in ts:
        Var = dat.variables[vnam][t,lvl,:,:]
        
        if not onmap:
            # plot normal pcolormesh
            plt.figure(figsize=(12,12))
            if np.isnan(vlim[0]):
                plt.pcolormesh(Var[x-xD[0]:x+xD[1],y-yD[0]:y+yD[0]],cmap=cmap)
            else:
                plt.pcolormesh(Var[x-xD[0]:x+xD[1],y-yD[0]:y+yD[0]],cmap=cmap,
                               vmin=vlim[0],vmax=vlim[1])
            plt.colorbar()
        if onmap:
            # ROI shading based on indices
            roi_lons = lons[x-xD[0]:x+xD[1], y-yD[0]:y+yD[1]]
            roi_lats = lats[x-xD[0]:x+xD[1], y-yD[0]:y+yD[1]]
            
            mextend = [np.min(lons[x-xD[0]:x+xD[1],y-yD[0]:y+yD[1]]),
                       np.max(lons[x-xD[0]:x+xD[1],y-yD[0]:y+yD[1]]),
                       np.min(lats[x-xD[0]:x+xD[1],y-yD[0]:y+yD[1]]),
                       np.max(lats[x-xD[0]:x+xD[1],y-yD[0]:y+yD[1]])]
            # plot on map with cartopy
            fig,ax=plt.subplots(1,1, figsize=(12,12),\
                                    subplot_kw={'projection':ccrs.Mercator()})
            ax.coastlines('10m')
            ax.add_feature(cfeature.BORDERS)
            gl = ax.gridlines(linewidth=1, color='gray', alpha=0.5)
            if np.isnan(vlim[0]):
                cs = ax.pcolormesh(lons,lats,Var,\
                                  transform=ccrs.PlateCarree(),cmap=cmap)
            else:
                cs = ax.pcolormesh(lons,lats,Var,vmin=vlim[0],vmax=vlim[1],\
                                  transform=ccrs.PlateCarree(),cmap=cmap)                   
                
            ax.set_extent(mextend,crs=ccrs.PlateCarree())
       
            
            # Adding a light red shading to highlight the ROI gridboxes
            ax.pcolormesh(roi_lons, roi_lats, np.ones_like(roi_lons), 
                          transform=ccrs.PlateCarree(),
                          cmap='Reds', alpha=0.2, shading='auto')
            # indicate the point 
            ax.scatter(plon,plat,s=100,color='k',transform=ccrs.PlateCarree())
            #
            ax.set_title('current ROI size: '+
                         str(np.shape(roi_lons)[0]*np.shape(roi_lons)[1])+
                         ' grid points',
                         fontsize=27,fontweight='bold')
            
            
            cbar_ax = fig.add_axes([0.25, 0.08, 0.5, 0.03])
            cbar=fig.colorbar(cs, cax=cbar_ax,orientation='horizontal',\
                              label=vnam)
    return x,y

       
# functions that modify the harmonie namelist           
def generate_bdeddh_entries(start_y, end_y, start_x, end_x):
    """
    Generates entries for NAMDDH for all grid points in region of interest
    
    Parameters:
    start_y = start of y-coordinates of region of interest
    end_y   = end of y-coordinates of region of interest
    start_x = start of x-coordinates of region of interest
    end_x   = end of x-coordinates of region of interest
    
    Returns:
    L = string to insert into harmonie_namelists.pm
    """
    L = []
    c1 = 0
    for jlon in range(start_y, end_y):
        for jgl in range(start_x, end_x):
            c1 += 1
            entry = (
                f"  'BDEDDH(1,{c1})' => '1.,',\n"
                f"  'BDEDDH(2,{c1})' => '1.,',\n"
                f"  'BDEDDH(3,{c1})' => '{jlon}.,',\n"
                f"  'BDEDDH(4,{c1})' => '{jgl}.,',\n"
            )
            L.append(entry)
    return ''.join(L)

def modify_namelist(file_path, new_entries):
    """
    Reads in and modifies harmonie_namelists.pm to include all grid points in
    the ROI.

    Parameters:
    file_path   = path to harmonie_namelists.pm file
    new_entries = output from generate_bdeddh_entries  function
    """
    with open(file_path, "r") as f:
        data = f.read()

    # Remove all lines containing 'BDEDDH'
    data = re.sub(r"  'BDEDDH\(\d+,\d+\)' => '[-\d\.]+.,',\n", "", data)

    # Find the %ddh block and insert new entries
    the_idx = data.find('%ddh')
    if the_idx != -1:
        the_idx = data.find('}', the_idx)  # Find the end of NAMDDH block
        newdata = data[:the_idx] + new_entries + data[the_idx:]
    else:
        newdata = data
    return newdata
#%% test for open cellular convection around Andøya
# for starters time step 24
ts = [24]
# lon lat for Andøya
lon = 16.074
lat = 69.296

# check a large area
xD = [15,30]
yD = [40,10]
x,y = check_define_ROI(dat,'toa_outgoing_longwave_flux',ts,0,lon,lat,xD,yD,cmap=plt.cm.Greys_r,onmap=True)

# check a more confined area
xD = [5,20]
yD = [30,2]
x,y = check_define_ROI(dat,'toa_outgoing_longwave_flux',ts,0,lon,lat,xD,yD,cmap=plt.cm.Greys_r,onmap=True)

#%% example for checking several time steps
ts = [12,18,24,30]
xD = [5,20]
yD = [30,2]
x,y = check_define_ROI(dat,'toa_outgoing_longwave_flux',ts,0,lon,lat,xD,yD,cmap=plt.cm.Greys_r,onmap=True)
#%% Now modify the namelist accordingly

start_y = y - yD[0]
end_y   = y + yD[1]

start_x = x - xD[0]
end_x   = x + xD[1]

bdeddh_entries = generate_bdeddh_entries(start_y, end_y, start_x, end_x)

modified_namelist = modify_namelist("harmonie_namelists.pm", bdeddh_entries)

with open("harmonie_namelists_new.pm", "w") as f:
    f.write(modified_namelist)

print("New namelist file 'harmonie_namelists_new.pm' has been created.")