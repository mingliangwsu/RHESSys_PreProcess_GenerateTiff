import arcpy
import numpy as np
from arcpy.sa import *
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
arcpy.env.scratchWorkspace = "C:/WorkSpace/arcpro_scrach.gdb"
arcpy.env.overwriteOutput = True
start = 0
end = 1
step = 0.5
sr = arcpy.Describe('te_0').spatialReference
desc = arcpy.Describe('te_0')
xmin = desc.extent.XMin
ymin = desc.extent.YMin
xmax = desc.extent.XMax
ymax = desc.extent.YMax
cell_size = desc.meanCellWidth
origin = arcpy.Point(xmin, ymin)

print("Processing all...")
#initialize by the value of -1
arr_e = dict()
arr_w = dict()
for i in np.arange(start, end, step):
    print(str(i))
    stri = str(int(i*10))
    te = Raster('te_' + stri)
    tw = Raster('tw_' + stri)
    arr_e[stri] = arcpy.RasterToNumPyArray(te)
    arr_w[stri] = arcpy.RasterToNumPyArray(tw)

e_base = arr_e['0'].copy().astype(float)
w_base = arr_w['0'].copy().astype(float)
e_base[:] = -1
w_base[:] = -1


for i in np.arange(start, end, step):
    print(str(i))
    stri = str(int(i*10))
    rad = i * 3.14159 * 1000.0 / 180.0
    #ec = (arr_e[stri] >= 1 and e_base < 0) 
    #wc = (arr_w[stri] >= 1 and w_base < 0)
    e_base = np.where((arr_e[stri] >= 1) & (e_base < 0), rad, e_base)
    w_base = np.where((arr_w[stri] >= 1) & (w_base < 0), rad, w_base)

eraster = arcpy.NumPyArrayToRaster(e_base, origin, cell_size, cell_size)
arcpy.DefineProjection_management(eraster, sr)
eraster.save("ehorizon")
wraster = arcpy.NumPyArrayToRaster(w_base, origin, cell_size, cell_size)
arcpy.DefineProjection_management(wraster, sr)
wraster.save("whorizon")
