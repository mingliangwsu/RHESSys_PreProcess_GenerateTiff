#import sys

#sys.path.append("C:/Program Files/ArcGIS/Pro/Resources\ArcPy")

import arcpy
from arcpy.sa import *
arcpy.SetLogHistory(False)
arcpy.ResetEnvironments()

#Inputs
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
arcpy.env.scratchWorkspace = "C:/WorkSpace/arcpro_scrach.gdb"
arcpy.env.overwriteOutput = True
dem = Raster("dem_filled")

#Output
outEhorizon = "ehorizon_1000"
outWhorizon = "whorizon_1000"
output_path = "U:/Projects/Colorado_MZ/raster_tiff/"

#gdppath = arcpy.env.workspace
#shapefile_path = gdppath[:gdppath.rfind("/")] + '/'

#basin_grid = Raster("gbasin")
#basin_shp = "U:/Projects/Colorado_MZ/BigThomson_WS_Shapefile/BigThomson_Shapefile.shp"
#gridmetbnd = Raster("gridmet_utm")


#TESTING!
desc = arcpy.Describe(dem)
xmin = desc.extent.XMin
ymin = desc.extent.YMin
xmax = desc.extent.XMax
ymax = desc.extent.YMax
cell_size = desc.meanCellWidth
# Set the extent environment variable
arcpy.env.extent = dem
sr = desc.spatialReference
origin = arcpy.Point(xmin, ymin)

start = 0
end = 90
step = 0.5

import numpy as np
arr_e = dict()
arr_w = dict()
#generate hillshade for each step angle
for i in np.arange(start, end, step):
    print(str(i))
    stri = str(int(i*10))
    te = arcpy.sa.Hillshade(in_raster=dem,azimuth=90,altitude=i,model_shadows="NO_SHADOWS",z_factor=1)
    tw = arcpy.sa.Hillshade(in_raster=dem,azimuth=270,altitude=i,model_shadows="NO_SHADOWS",z_factor=1)
    arr_e[stri] = arcpy.RasterToNumPyArray(te)
    arr_w[stri] = arcpy.RasterToNumPyArray(tw)

print("Processing all...")
#initialize by the value of -1

e_base = arr_e[str(int(start*10))].copy().astype(float)
w_base = arr_w[str(int(start*10))].copy().astype(float)
e_base[:] = -1
w_base[:] = -1


for i in np.arange(start, end, step):
    print(str(i))
    stri = str(int(i*10))
    rad = i * 3.14159 * 1000.0 / 180.0
    e_base = np.where((arr_e[stri] >= 1) & (e_base < 0), rad, e_base)
    w_base = np.where((arr_w[stri] >= 1) & (w_base < 0), rad, w_base)
print("Saving all...")
eraster = arcpy.NumPyArrayToRaster(e_base, origin, cell_size, cell_size)
arcpy.DefineProjection_management(eraster, sr)
eraster.save(outEhorizon)
wraster = arcpy.NumPyArrayToRaster(w_base, origin, cell_size, cell_size)
arcpy.DefineProjection_management(wraster, sr)
wraster.save(outWhorizon)
 
#output tiff
eraster.save(output_path + outEhorizon + '.tif') 
wraster.save(output_path + outWhorizon + '.tif') 
 
print("Cleaning up ...")
arcpy.env.workspace = "C:/WorkSpace/arcpro_scrach.gdb"
for i in range(0, 300):
    print(str(i))
    if arcpy.Exists("HillSha_de" + str(i)):
        arcpy.Delete_management("HillSha_de" + str(i))
    if arcpy.Exists("HillSha_dem" + str(i)):
        arcpy.Delete_management("HillSha_dem" + str(i))
    if arcpy.Exists("HillSha_dem_" + str(i)):
        arcpy.Delete_management("HillSha_dem_" + str(i))



