Setting up python for using Kalpana will depend on which of the features listed below you want to use. 
For more detail go to https://ccht.ccee.ncsu.edu/ or to the paper (Rucker et al., 2021).

(1) Exporting ADCIRC outputs as Shapefiles, GeoPackage or KMZ.
(2) Downscale ADCIRC maximum water elevation output to a finer resolution.


Feature (1)
Create a conda environment using the provided yml file. Change name and prefix (location to store python packages).
To create a conda environment from a yml file and store the packages in a specified path, use:
'conda env create -f kalpana_env_H2.yml -p /path/to/the/environment'
We provide two yml files, one has the specific versions of the package I use at the NCSU HPC, and the other one doesn't have 
the specific versions.
If you prefer to install the packages using pip, you can use
'conda create -n Kalpana python=3.9'
'pip install -r requirements.txt'

Feature (2)
First you need to have GRASS GIS installed (https://grass.osgeo.org/), versions >= 8.2 are supported.
How to setup the python environment varies across OS. 

If using Ubuntu or a linux HPC you need to create a conda enviroment in the usual way following instructions in the conda documentation 
(https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

For Windows you need to use the python installation that comes with GRASS GIS, and you can not have more python installations on
your system. For using the grass python.exe, you need to launch grass and then use the grass cmd. In this case you are not able to use
conda, so you need to install all the necessary dependencies using pip. Soon we will provide a requierements.txt file to install all
packages.

Examples of how to setup and running kalpana will come soon!
