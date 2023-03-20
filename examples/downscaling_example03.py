#!/usr/bin/env python
# coding: utf-8

# In[1]:

'''
This example combine downscaling examples 1 and 2. DEM with mesh elements size and the grass location are created. This should be considerable more slow than running example 2, since creating the inputs for the downscaling is the slower part.
'''

#import sys
#sys.path.append(r'/rsstu/users/j/jcdietri/DHS-CRCoE-2016-2020/tacuevas/github/Kalpana')
from downscaling import runStatic

ncFile = r'/home/kalpana/maxele.63.nc'
levels = [0, 11, 1]
epsgOut = 6543
pathOut = r'/home/kalpana/maxele_florence.shp'
grassVer = 8.3
pathRasFiles = '.'
rasterFiles = 'ncDEMs_epsg6543'
meshFile = r'/home/kalpana/NC9.shp'
epsgIn = 4326
vUnitIn = 'm'
vUnitOut = 'ft'
var = 'zeta_max'
conType = 'polygon'
subDomain = None
exportMesh = True
dzFile = r'/home/kalpana/NC9mesh_from_tss2navd88.pkl'
zeroDif = -20 
nameGrassLocation = None
createGrassLocation = True
createLocMethod = 'from_raster'
attrCol = 'zMean'
repLenGrowing = 1.0 
compAdcirc2dem = True
floodDepth = False
clumpThreshold = 'from_mesh'
perMinElemArea = 1
ras2vec = False
exportOrg = False

runStatic(ncFile, levels, epsgOut, pathOut,  grassVer, pathRasFiles, rasterFiles, meshFile,
          epsgIn, vUnitIn, vUnitOut, var, conType, subDomain, exportMesh, dzFile, zeroDif, 
          nameGrassLocation, createGrassLocation, createLocMethod, attrCol, repLenGrowing, 
          compAdcirc2dem, floodDepth, clumpThreshold, perMinElemArea, ras2vec, exportOrg)
