
import netCDF4 as nc
import numpy as np
import stagnated
import sys

#import Kalpana functions from github repository
# change these to your own paths!
sys.path.append('/Users/liting/Documents/GitHub/Kalpana')
from kalpana.export import *
from kalpana.visualizations import *
import contextily as cx
import os
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import rasterize
from netCDF4 import Dataset
#from modified_functions import *


def nc2shp63(ncFile, var, levels, conType, pathOut, epsgOut, vUnitOut='ft', vUnitIn='m', epsgIn=4326,
           subDomain=None, epsgSubDom=None, exportMesh=False, meshName=None, dzFile=None, zeroDif=-20,time_index=0):
    ''' Run all necesary functions to export adcirc outputs as shapefiles.
        Parameters
            ncFile: string
                path of the adcirc output, must be a netcdf file
            var: string
                Name of the variable to export
            levels:list
                Contour levels. Min, Max and Step. Max IS included as in np.arange method.
                Values must be in vUnitOut vertical unit.
            conType: string
                'polyline' or 'polygon'
            pathout: string
                complete path of the output file (*.shp or *.gpkg)
            epsgOut: int
                coordinate system of the output shapefile
            vUnitIn, vUnitOut: string. Default for vUnitIn is 'm' and 'ft' for vUnitOut
                input and output vertical units. For the momment only supported 'm' and 'ft'
            epsgIn: int. Default 4326.
                coordinate system of the adcirc input
            subDomain: str or list. Default None
                complete path of the subdomain polygon kml or shapelfile, or list with the
                uper-left x, upper-left y, lower-right x and lower-right y coordinates. The crs must be the same of the
                adcirc input file.
            exportMesh: boolean. Default False
                True for export the mesh geodataframe and also save it as a shapefile
            meshName: str
                file name of the output mesh shapefile
            dzFile: str
                full path of the pickle file with the vertical difference between datums
                for each mesh node
            zeroDif: int
                threshold for using nearest neighbor interpolation to change datum. Points below
                this value won't be changed.
        Returns
            gdf: GeoDataFrame
                gdf with contours
            mesh: GeoDataFrame, only if exportMesh is True
                gdf with mesh elements, representative length and area of each triangle
    '''
    
    print('Start exporting adcirc to shape')
    ## read adcirc file
    nc = netcdf.Dataset(ncFile, 'r')
    ## change units of the requested levels
    if vUnitIn == 'm' and vUnitOut == 'ft':
        levels = [l / 3.2808399 for l in levels]
    elif vUnitIn == 'ft' and vUnitOut == 'm':
        levels = [l * 3.2808399 for l in levels]
    if conType == 'polygon':   
        maxmax = np.max(nc[var][:].data)
        orgMaxLevel = levels[1]
        stepLevel = levels[2]
        ## list of levels to array
        levels_aux = np.arange(levels[0], np.ceil(maxmax), stepLevel)
        ## given levels will now match the avarege value of each interval    
        levels_aux = levels_aux - stepLevel/2
        levels = levels_aux.copy()
    else:
        orgMaxLevel = levels[1]
        stepLevel = levels[2]
        levels = np.arange(levels[0], orgMaxLevel + stepLevel, stepLevel)
    
    t00 = time.time()
    gdf = runExtractContours63(nc, var, levels, conType, epsgIn, stepLevel, orgMaxLevel, 
                            dzFile, zeroDif,time_index)
    print(f'    Ready with the contours extraction: {(time.time() - t00)/60:0.3f} min')
    
    ## clip contours if requested
    if subDomain is not None:
        t0 = time.time()
        subDom = readSubDomain(subDomain, epsgSubDom)
        gdf = gpd.clip(gdf, subDom.to_crs(epsgIn))
        print(f'    Cliping contours based on mask: {(time.time() - t0)/60:0.3f} min')
    
    ## change vertical units if requested
    if vUnitIn == vUnitOut:
        pass
    else:
        t0 = time.time()
        gdf = gdfChangeVerUnit(gdf, vUnitIn, vUnitOut)
        print(f'    Vertical units changed: {(time.time() - t0)/60:0.3f} min')
    
    ## change CRS if requested
    if epsgIn == epsgOut:
        pass
    else:
        t0 = time.time()
        gdf = gdf.to_crs(epsgOut)
        print(f'    Changing CRS: {(time.time() - t0)/60:0.3f} min')
    
    ## save output shape file
    t0 = time.time()
    if pathOut.endswith('.shp'):
        gdf.to_file(pathOut)
    elif pathOut.endswith('.gpkg'):
        gdf.to_file(pathOut, driver = 'GPKG')
    elif pathOut.endswith('.wkt'):
        gdf.to_csv(pathOut)
    print(f'    Saving file: {(time.time() - t0)/60:0.3f} min')
    
    ## export mesh if requested
    if exportMesh == True:
        print('    Exporting mesh')
        t0 = time.time()
        mesh = mesh2gdf(nc, epsgIn, epsgOut)
        
        if subDomain is not None:
            mesh = gpd.clip(mesh, subDom.to_crs(epsgOut))
        
        mesh.to_file(os.path.join(os.path.dirname(pathOut), f'{meshName}.shp'))
        print(f'    Mesh exported: {(time.time() - t0)/60:0.3f} min')
        print(f'Ready with exporting code after: {(time.time() - t00)/60:0.3f} min')
        return gdf, mesh
    
    else:
        print(f'Ready with exporting code after: {(time.time() - t00)/60:0.3f} min')
        return gdf
    


def runExtractContours63(ncObj, var, levels, conType, epsg, stepLevel, orgMaxLevel, dzFile=None, zeroDif=-20,time_index=0):

    ''' Run "contours2gpd" or "filledContours2gpd" if npro = 1 or "contours2gpd_mp" or "filledContours2gpd_mp" if npro > 1.
        Parameters
            ncObj: netCDF4._netCDF4.Dataset
                Adcirc input file
            var: string
                Name of the variable to export
            levels: np.array
                Contour levels. The max value in the entire doman and over all timesteps is added to the requested levels.
            conType: string
                'polyline' or 'polygon'
            epsg: int
                coordinate system
            stepLevel: int or float
                step size of the levels requested
            orgMaxLevel: int or float
                max level requested
            dzFile: str
                full path of the pickle file with the vertical difference between datums
                for each mesh node
            zeroDif: int
                threshold for using nearest neighbor interpolation to change datum. Points below
                this value won't be changed.
        Returns
            gdf: GeoDataFrame
                Polygons or polylines as geometry columns. If the requested file is time-varying the GeoDataFrame will include all timesteps.
            
    '''
    ## get triangles and nodes coordinates
    nv = ncObj['element'][:,:] - 1 ## triangles starts from 1
    x = ncObj['x'][:].data
    y = ncObj['y'][:].data
    z = ncObj['depth'][:].data
    
    ## get extra info: variable name, variable long-name and unit name
    vname = ncObj[var].name
    lname = ncObj[var].long_name
    #u = ncObj[var].units

    ## matplotlib triangulation
    tri = mpl.tri.Triangulation(x, y, nv)
    
    ## if the variable requested is the bathymetry, values are inverted (times -1) for plotting
    if var == 'depth':
        timeVar = 0
        auxMult = -1
    else:
        auxMult = 1
    
    ## time constant

    aux = ncObj[var][time_index][:].data
    if dzFile != None: ## change datum
        dfNewDatum = changeDatum(x, y, z, aux, dzFile, zeroDif)
        ## change nan to -99999 and transform it to a 1D vector
        aux = np.nan_to_num(dfNewDatum['newVar'].values, nan = -99999.0).reshape(-1)*auxMult
    else: ## original datum remains constant
        ## change nan to -99999 and transform it to a 1D vector
        aux = np.nan_to_num(aux, nan = -99999.0).reshape(-1)*auxMult
    ## non-filled contours
    if conType == 'polyline':
        labelCol = 'z'
        gdf = contours2gpd(tri, aux, levels, epsg, True)
    ## filled contours
    elif conType == 'polygon':
        labelCol = 'zMean'
        gdf = filledContours2gpd(tri, aux, levels, epsg, stepLevel, orgMaxLevel, True)
    ## error message
    else:
        print('only "polyline" and "polygon" types are supported!')
        sys.exit(-1)
    ## add more info to the geodataframe
    gdf['variable'] = [vname]*len(gdf)
    gdf['name'] = [lname]*len(gdf)
        #gdf['zLabelCol'] = [f'{x:0.2f} {unit}' for x in gdf[labelCol]]        
    return gdf



def shapefile_to_netcdf(shapefile_path1, shapefile_path2, ncfile_path, threshold_value=0.001, nx=100, ny=100,overwrite=True):
    # check if nc file exists
    if os.path.exists(ncfile_path):
        if overwrite:
            print(f"File '{ncfile_path}' exists. Overwriting...")
            os.remove(ncfile_path)  # Delete the file to overwrite
        else:
            raise PermissionError(f"File '{ncfile_path}' already exists. Set overwrite=True to overwrite the file.")

    # Load the shapefiles
    gdf1 = gpd.read_file(shapefile_path1)
    gdf2 = gpd.read_file(shapefile_path2)

    # Define the grid resolution for rasterization
    lon_min1, lon_max1 = gdf1.total_bounds[0], gdf1.total_bounds[2]
    lat_min1, lat_max1 = gdf1.total_bounds[1], gdf1.total_bounds[3]

    print(f"lon_min1: {lon_min1}, lon_max1: {lon_max1}, lat_min1: {lat_min1}, lat_max1: {lat_max1}")

    # Create a grid of lon/lat
    lon1 = np.linspace(lon_min1, lon_max1, nx)
    lat1 = np.linspace(lat_min1, lat_max1, ny)

    # Create an affine transformation for rasterio to align the grid
    transform = rasterio.transform.from_bounds(lon_min1, lat_max1, lon_max1, lat_min1, nx, ny)

    # Rasterize the shapefile geometries onto the grid
    rasterized_data1 = rasterize(
        [(geom, 1) for geom in gdf1.geometry],  # Marks all shapes with a value of 1
        out_shape=(ny, nx),
        transform=transform,
        fill=np.nan,  # Fill value for areas with no geometries
        dtype='float64'
    )

    rasterized_data2 = rasterize(
        [(geom, 1) for geom in gdf2.geometry],  # Marks all shapes with a value of 1
        out_shape=(ny, nx),
        transform=transform,
        fill=np.nan,  # Fill value for areas with no geometries
        dtype='float64'
    )

    combined_data = np.sqrt(rasterized_data1**2 + rasterized_data2**2)
    combined_data = np.where(combined_data <= 1.5, 1, 0)



    with Dataset(ncfile_path, 'w', format='NETCDF4') as nc:
        # Create dimensions
        nc.createDimension('lon', nx)
        nc.createDimension('lat', ny)

        # Create variables for lon, lat, and the rasterized data
        lons = nc.createVariable('lon', 'f4', ('lon',))
        lats = nc.createVariable('lat', 'f4', ('lat',))
        data_var = nc.createVariable('stag_water', 'f4', ('lat', 'lon'))

        # Write lon, lat, and rasterized data to the NetCDF file
        lons[:] = lon1
        lats[:] = lat1
        data_var[:, :] = combined_data  # Assign the processed data to the NetCDF variable

        # Add metadata (optional)
        data_var.units = '1'  # Value of 1 where shapes exist, 0 elsewhere
        data_var.long_name = f'Stagnated water calculated from u-vel and v-vel with threshold: {threshold_value}'
        nc.title = 'Converted Shapefile to NetCDF'
        nc.history = 'Created with Python script using geopandas, rasterio, and netCDF4'

    print(f"NetCDF file '{ncfile_path}' created successfully.")
