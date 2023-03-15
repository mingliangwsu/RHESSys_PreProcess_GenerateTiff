"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4, param5, param6):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    subbasin = Raster(param1)
    landform = Raster(param2)
    others = param3
    arcpy.env.overwriteOutput = param4
    minpatch = int(param5)
    outpatch = param6
    cellsize = arcpy.Describe(subbasin).meanCellWidth
    minarea = cellsize * cellsize * minpatch
    rasterlist = [subbasin,landform,others]
    arcpy.AddMessage("Combinning...")
    t = Combine(rasterlist)
    #eliminate small ones
    arcpy.conversion.RasterToPolygon(t, "ctemp", "NO_SIMPLIFY")
    arcpy.management.AddGeometryAttributes("ctemp", "AREA")
    expression = '"POLY_AREA"' + ' < ' + str(minarea)
    #outFeatureClass = fc + '_clean'
    exclusionExpression = "#"
    # Execute MakeFeatureLayer
    arcpy.AddMessage("Select expression:" + expression)
    arcpy.MakeFeatureLayer_management("ctemp", "ptemp")
    # Execute SelectLayerByAttribute to define features to be eliminated
    arcpy.SelectLayerByAttribute_management("ptemp", "NEW_SELECTION", expression)
    # Execute Eliminate
    arcpy.Eliminate_management("ptemp", "tttemp", "LENGTH", exclusionExpression)
    arcpy.conversion.FeatureToRaster("tttemp", "Id", outpatch, cellsize)
    
    #t.save(outpatch)
    arcpy.Delete_management("ptemp")
    arcpy.Delete_management("ctemp")
    arcpy.Delete_management("tttemp")
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    param2 = arcpy.GetParameterAsText(2)
    param3 = arcpy.GetParameter(3)
    param4 = arcpy.GetParameter(4)
    param5 = arcpy.GetParameter(5)
    param6 = arcpy.GetParameterAsText(6)
    script_tool(param0, param1, param2, param3, param4, param5, param6)
    #arcpy.SetParameterAsText(2, "Result")
