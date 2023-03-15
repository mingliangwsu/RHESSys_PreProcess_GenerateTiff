"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4, param5, param6, param7, param8):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    HUCfc = param1
    sql_sel = param2
    cellsize = param3
    ref = param4
    arcpy.env.overwriteOutput = param5
    outputbndfc = param6
    outputbndraster = param7
    fieldn = param8
    arcpy.AddMessage("Select HUC unit...")
    #arcpy.SelectLayerByAttribute_management(HUCfc, "NEW_SELECTION", sql_sel)
    #arcpy.SelectLayerByAttribute_management(HUCfc, "NEW_SELECTION", "HUC_CODE = '10190006'")
    arcpy.MakeFeatureLayer_management(HUCfc, "ctemp", sql_sel)
    result = arcpy.GetCount_management("ctemp")
    count = int(result.getOutput(0))
    arcpy.AddMessage("Number of selected features: {}".format(count))
    # Write the selected features to a new feature class
    #arcpy.CopyFeatures_management(HUCfc, 'ctemp')
    arcpy.AddMessage("Reprojecting...")
    arcpy.Project_management("ctemp", outputbndfc, ref)
    arcpy.AddMessage("To raster...with field:" + fieldn)
    arcpy.conversion.FeatureToRaster(outputbndfc, fieldn, "tempr", cellsize)
    temp = Con(~IsNull("tempr"), 1)
    temp.save(outputbndraster)
    # Clean up
    arcpy.Delete_management("ctemp")
    arcpy.Delete_management("tempr")
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    param2 = arcpy.GetParameter(2)
    param3 = arcpy.GetParameter(3)
    param4 = arcpy.GetParameter(4)
    param5 = arcpy.GetParameter(5)
    param6 = arcpy.GetParameterAsText(6)
    param7 = arcpy.GetParameterAsText(7)
    param8 = arcpy.GetParameterAsText(8)
    script_tool(param0, param1, param2, param3, param4, param5, param6, param7, param8)
    #arcpy.SetParameterAsText(2, "Result")
