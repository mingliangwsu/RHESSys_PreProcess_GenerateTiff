#import sys

#sys.path.append("C:/Program Files/ArcGIS/Pro/Resources\ArcPy")

import arcpy
from arcpy.sa import *
arcpy.SetLogHistory(False)

arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
start = 0
end = 90
step = 0.5
for i in range(0, 300):
    print('temp ' + str(i))
    if arcpy.Exists("HillSha_de" + str(i)):
        arcpy.Delete_management("HillSha_de" + str(i))
    if arcpy.Exists("HillSha_dem" + str(i)):
        arcpy.Delete_management("HillSha_dem" + str(i))
    if arcpy.Exists("HillSha_dem_" + str(i)):
        arcpy.Delete_management("HillSha_dem_" + str(i))
for i in np.arange(start, end, step):
    print(str(i))
    stri = str(int(i*10))
    if arcpy.Exists("te_" + stri):
        arcpy.Delete_management("te_" + stri)
    if arcpy.Exists("tw_" + stri):
        arcpy.Delete_management("tw_" + stri)