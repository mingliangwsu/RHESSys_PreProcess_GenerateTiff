import arcpy,csv
from arcpy.sa import *
import math
arcpy.ResetEnvironments()
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
arcpy.env.mask = Raster("gbasin")
arcpy.env.extent = Raster("gbasin")
arcpy.env.overwriteOutput = True
output_path = "U:/Projects/Colorado_MZ/raster_tiff/"

basin_grid = Raster("gbasin")
#flai = Raster("U:/Projects/Colorado_MZ/raster_tiff/LAI.tif")
desc = arcpy.Describe(basin_grid)
xmin = desc.extent.XMin
ymin = desc.extent.YMin
xmax = desc.extent.XMax
ymax = desc.extent.YMax
cell_size = desc.meanCellWidth
#num_rows = desc.height
#num_cols = desc.width
if not arcpy.Exists("f_gbasin"):
    arcpy.management.CopyRaster(basin_grid, "f_gbasin", pixel_type='32_BIT_FLOAT')
fbasin = Raster("f_gbasin")
xcor = Raster(fbasin.getRasterInfo())
ycor = Raster(fbasin.getRasterInfo())
with RasterCellIterator({'rasters':[fbasin, xcor, ycor],'skipNoData':[fbasin]}) as rci_skip:
    for i,j in rci_skip:
        xcor[i,j] = xmin + cell_size * 0.5 + j * cell_size
        ycor[i,j] = ymax - cell_size * 0.5 - i * cell_size

if arcpy.Exists(output_path + "xcor.tif"):
    arcpy.Delete_management(output_path + "xcor.tif")
xcor.save(output_path + "xcor.tif")
if arcpy.Exists(output_path + "ycor.tif"):
    arcpy.Delete_management(output_path + "ycor.tif")
ycor.save(output_path + "ycor.tif")
