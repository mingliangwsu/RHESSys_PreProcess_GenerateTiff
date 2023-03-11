import arcpy,csv
from arcpy.sa import *
import math
arcpy.env.workspace = "Z:/Projects/BioEarth/Datasets/Global_LAI/grid"
geo_ref = arcpy.SpatialReference(4269)
input_rasters = [Raster("y2011m5_0"),Raster("y2011m5_1"),Raster("y2011m6_0"),Raster("y2011m6_1"),Raster("y2011m7_0"),Raster("y2011m7_1"),Raster("y2011m8_0"),Raster("y2011m8_1"),Raster("y2011m9_0"),Raster("y2011m9_1"),Raster("y2010m5_0"),Raster("y2010m5_1"),Raster("y2010m6_0"),Raster("y2010m6_1"),Raster("y2010m7_0"),Raster("y2010m7_1"),Raster("y2010m8_0"),Raster("y2010m8_1"),Raster("y2010m9_0"),Raster("y2010m9_1"),Raster("y2009m5_0"),Raster("y2009m5_1"),Raster("y2009m6_0"),Raster("y2009m6_1"),Raster("y2009m7_0"),Raster("y2009m7_1"),Raster("y2009m8_0"),Raster("y2009m8_1"),Raster("y2009m9_0"),Raster("y2009m9_1")]
y2011max = arcpy.sa.CellStatistics(input_rasters,"MAXIMUM")
if arcpy.Exists("y2009_11max"):
    arcpy.Delete_management("y2009_11max")
arcpy.management.DefineProjection(y2011max, geo_ref)
y2011max.save("y2009_11max")