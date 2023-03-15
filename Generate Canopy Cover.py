"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4):
    """Script code goes below"""
    #Inputs
    arcpy.env.workspace = param0
    vegetation = Raster(param1)
    evc = Raster(param2)
    arcpy.env.overwriteOutput = param3
    #tiffpath = param4 + "/"
    gmask = vegetation
    cc_name = param4
    #env
    arcpy.AddMessage("Workspace:" + arcpy.env.workspace)
    #INPUTS
    #gbasin = Raster("gbasin")
    #1:evergreen 2:deciduous 3:grass 4:non veg 5:shrub 6:water
    #LANDFIRE EVC 
    #100, Sparse Vegetation Canopy
    #110-195 %tree
    #210-279 %shrub
    #310-399 %herb 
    
    #clip evc
    evc_ref = arcpy.Describe(evc).spatialReference
    veg_ref = arcpy.Describe(vegetation).spatialReference
    out_cell_size = str(int(arcpy.Describe(vegetation).meanCellWidth))
    
    #get corner in EVC
    #vegetation to EVC projection
    arcpy.AddMessage("Clipping EVC...")
    if evc_ref.factoryCode == veg_ref.factoryCode and evc_ref.name == veg_ref.name:
        arcpy.CopyRaster_management(vegetation, "veg_alb")
    else:
        arcpy.management.ProjectRaster(vegetation, "veg_alb", evc_ref, "NEAREST", out_cell_size)
    
    desc = arcpy.Describe("veg_alb")
    xmin = desc.extent.XMin
    ymin = desc.extent.YMin
    xmax = desc.extent.XMax
    ymax = desc.extent.YMax
    cell_size = desc.meanCellWidth
    buffer_dist = 200 * cell_size
    
    bnd = str(xmin - buffer_dist) + ' ' + str(ymin - buffer_dist) + ' ' + str(xmax + buffer_dist) + ' ' + str(ymax + buffer_dist) #x-min, y-min, x-max, y-max
    arcpy.management.Clip(evc, bnd, "evc_alb")
    #reproject to same as Vegetation inputs
    arcpy.env.snapRaster = vegetation
    if evc_ref.factoryCode == veg_ref.factoryCode and evc_ref.name == veg_ref.name:
        arcpy.CopyRaster_management("evc_alb", "evc_target")
    else:
        arcpy.management.ProjectRaster("evc_alb", "evc_target", veg_ref, "NEAREST", out_cell_size)
    
    #get output canopy cover
    arcpy.AddMessage("Generating canopy cover...")
    arcpy.env.extent = vegetation
    tevc = Float(Raster("evc_target") / 100.0)
    tcc = Raster(tevc.getRasterInfo())
    with RasterCellIterator({'rasters':[vegetation, tevc, tcc,gmask],'skipNoData':[gmask]}) as rci_skip:
        for i,j in rci_skip:
            if vegetation[i,j] in [1,2]:
                if tevc[i,j] >= 1.10 and tevc[i,j] <= 1.95:
                    tcc[i,j] = tevc[i,j] - 1.0
                else:
                    tcc[i,j] = 0.05
            elif vegetation[i,j] == 5:
                if tevc[i,j] >= 2.10 and tevc[i,j] <= 2.79:
                    tcc[i,j] = tevc[i,j] - 2.0;
                else:
                    tcc[i,j] = 0.05
            elif vegetation[i,j] in [3,4]:
                if tevc[i,j] >= 3.10 and tevc[i,j] <= 3.99:
                    tcc[i,j] = tevc[i,j] - 3.0;
                else:
                    tcc[i,j] = 0.05
            else:
                tcc[i,j] = 0.0
    
    #export to TIF
    arcpy.CopyRaster_management(tcc, cc_name)
    
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    param2 = arcpy.GetParameterAsText(2)
    param3 = arcpy.GetParameter(3)
    param4 = arcpy.GetParameterAsText(4)
    #param5 = arcpy.GetParameterAsText(5)
    script_tool(param0, param1, param2, param3, param4)
    #arcpy.SetParameterAsText(2, "Result")
