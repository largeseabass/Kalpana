## first step is to add the github repo to the path, so functions can be imported
import sys
sys.path.append(r'/rsstu/users/j/jcdietri/DHS-CRCoE-2016-2020/tacuevas/github/Kalpana')
from kalpana.downscaling import meshRepLen2raster

'''
This script creates a grass location importing the DEM for downscaling and also creates
a new DEM with same resolution and extend with the size of the mesh triangles. This step
is key for the downscaling and can be run in advance, since only depends on the mesh.
'''

fort14 = r'/share/jcdietri/tacuevas/kalpana/inputs/fort.14'
epsgIn = 4326 ## CRS for lat/lon
epsgOut = 6543 ## projected CRS for NC
pathOut = r'/share/jcdietri/tacuevas/kalpana/outputs2/test01/NC9.shp' ## full path of 
grassVer = 8.3
pathRasFiles = r'/share/jcdietri/tacuevas/kalpana/inputs'
rasterFiles = 'ncDEMs'

meshRepLen2raster(fort14, epsgIn, epsgOut, pathOut, grassVer, pathRasFiles, rasterFiles, 
                  subDomain=None, nameGrassLocation=None, createGrassLocation=True, 
                  createLocMethod='from_raster')
