#import sys

#sys.path.append("C:/Program Files/ArcGIS/Pro/Resources\ArcPy")

import arcpy
from arcpy.sa import *
arcpy.ResetEnvironments()
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
arcpy.env.scratchWorkspace = "C:/WorkSpace/arcpro_scrach.gdb"
arcpy.env.overwriteOutput = True

gdppath = arcpy.env.workspace
shapefile_path = gdppath[:gdppath.rfind("/")] + '/'


#basin_grid = Raster("gbasin")
#basin_shp = "U:/Projects/Colorado_MZ/BigThomson_WS_Shapefile/BigThomson_Shapefile.shp"
output_path = "U:/Projects/Colorado_MZ/raster_tiff/"
#gridmetbnd = Raster("gridmet_utm")
dem = Raster("U:/Projects/Colorado_MZ/Inputs/DEP_30m_utm.tif")
outFillSink = output_path + "filled_dem.tif"
outSlope = output_path + "slope.tif"

#spatial references
dem_ref = arcpy.Describe(dem).spatialReference
geo_ref = arcpy.SpatialReference(4269)

drain = -1

input_outlet_location = True
olat = 40.3538
olon = -105.5841
drain = 104.7 #km2 it's for reference in case the gage is near two main streams; if don't know, set -1
gbasin_from_gage = "gbasin_from_gage"
cbasin_from_gage = "cbasin_from_gage"

#create point feature
if input_outlet_location:
# Create a point feature class
    point = arcpy.Point(olon, olat)
    new_geom = arcpy.PointGeometry(point, geo_ref)
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, "ctemp_pour", "POINT")
    arcpy.AddField_management("ctemp_pour", "PID", "SHORT")
    # Insert the point into the feature class
    #fields = ['SHAPE@',"PID"]
    #cursor = arcpy.da.InsertCursor("ctemp_pour", fields)
    #cursor.insertRow([new_geom,1])
    row_values = [(1, (olon, olat))]
    with arcpy.da.InsertCursor("ctemp_pour", ['PID', 'SHAPE@XY']) as cursor:
    # Insert new rows that include the ID and a x,y coordinate
    #  pair that represents the county center
        for row in row_values:
            cursor.insertRow(row)

    #define projection
    arcpy.management.DefineProjection("ctemp_pour", geo_ref)
    arcpy.Project_management("ctemp_pour", "ctemp_pour_reproj", dem_ref)
    #arcpy.Delete_management("XXXXXX")
    
#TESTING!
desc = arcpy.Describe(dem)
xmin = desc.extent.XMin
ymin = desc.extent.YMin
xmax = desc.extent.XMax
ymax = desc.extent.YMax
cell_size = desc.meanCellWidth
buffer_dist = 100 * cell_size
buffer_extent = arcpy.Extent(xmin - buffer_dist, ymin - buffer_dist, xmax + buffer_dist, ymax + buffer_dist)
# Set the extent environment variable
arcpy.env.extent = buffer_extent

#assume dem in meter
if drain > 0 and input_outlet_location:
    drain_cells = int(drain * 1000 * 1000 / (cell_size * cell_size))

if input_outlet_location:
    #create pour point into raster
    arcpy.PointToRaster_conversion("ctemp_pour_reproj", "PID", "XXXXXX", "MAXIMUM", "", cell_size)
    inpour = Raster("XXXXXX") + 0
    #arcpy.Delete_management("YYYYYY")
    #arcpy.Delete_management("XXXXXX")
    inpour.save("temp_inpour_grid")

#file 
kernel = NbrCircle(3, "CELL")
# apply the FocalStatistics tool to smooth the DEM
smoothed_dem = FocalStatistics(dem, kernel, "MEAN")
dem_filled = Fill(smoothed_dem)


# Create a flow accumulation raster
flow_dir = FlowDirection(dem_filled)
flow_acc = FlowAccumulation(flow_dir, "#", "INTEGER")

slope = Slope(dem_filled)
aspect = Aspect(dem_filled)
curvature = Curvature(dem_filled)

out_raster = arcpy.sa.Hillshade(in_raster="dem_filled",azimuth=315,altitude=45,model_shadows="NO_SHADOWS",z_factor=1)
out_raster.save("hillshade")

#calculate twi
slope_f = (slope * 1.570796) / 90.0
tan_slp = Con(slope > 0, Tan(slope_f), 0.001)
fa_scaled = (flow_acc + 1) * cell_size
twi = Ln(fa_scaled / tan_slp) #TWI(dem_filled)

dem_filled.save("dem_filled")
flow_dir.save("flow_dir")
flow_acc.save("flow_acc")
aspect.save("aspect")  
slope.save("slope") 
curvature.save("curvature")
twi.save("TWI")

#generating hillslopes
# Define the output classified raster
# Use the Mosaic To New Raster tool to create a composite raster
arcpy.management.CompositeBands(
    in_rasters="slope;aspect;curvature;TWI;hillshade",
    out_raster="composite5b"
)

# Use the Iso Cluster Unsupervised Classification tool to classify the composite raster
outUnsupervised = IsoClusterUnsupervisedClassification("composite5b", 10, 50, 15)
outUnsupervised.save("hillslope_classes")

# Threshold the flow accumulation to identify streams

#number of km2 (the first big number is to generate the large basin boundary)
t_area_km2 = [25,1]
t_area_30mcell = []
for num in t_area_km2:
    cells = int(num * 1000000 / (cell_size * cell_size))
    t_area_30mcell.append(cells)

for i, threshold in enumerate(t_area_30mcell):
    print("i, threshold:" + str(i) + " " + str(threshold))
    suffix = '_' + str(t_area_km2[i]) + 'km2'
    test10 = Con(flow_acc > threshold, 1)
    out_str = Con(flow_acc > threshold, 1, 0)
    out_riv_shp = 'out_riv' + suffix
    arcpy.conversion.RasterToPolyline(test10, out_riv_shp)
    out_stream = 'stream_raster' + suffix
    test10.save(out_stream)
    # Generate the stream link raster
    out_link = "gout_link" + suffix
    out_raster = arcpy.sa.StreamLink(out_stream,"flow_dir")
    out_raster.save(out_link)
    #links
    glink = Raster(out_link)
    testacc10 = ZonalStatistics(glink, 'Value', flow_acc, "MAXIMUM")
    testout10 = Con(testacc10 == flow_acc, glink)
    
    
    if input_outlet_location:
        #add the observation outlet into this outlet points set
        #set ID
        maxid = int(arcpy.GetRasterProperties_management(glink, "MAXIMUM").getOutput(0)) + 1
        print("maxid:" + str(maxid))
        
        
        #find closed link grid to inpour
        # Create a SearchCursor object to iterate over the cells in the raster
        # Loop through each cell and check its value
        #only need find one time
        if i == 0:
          column = -1
          row_index = -1
          print("Snapping gage to link gridcell...\n")
          with RasterCellIterator({'rasters':[inpour]}) as rci:
             for ii,jj in rci:
                 if inpour[ii,jj] == 1:
                     row_index = ii
                     column = jj
          if column == -1 or row_index == -1:
              print("ERROR: Can't find index for gage site!\n")
          else:
              print(" the gage is located at row:" + str(row_index) + " col:" + str(column))
          #find closed cell
          find = False
          skiplist = []
          while not find:
            irow = -1
            icol = -1
            mindist = 9999999999;
            with RasterCellIterator({'rasters':[glink, flow_acc],'skipNoData':[glink,flow_acc]}) as rci_skip:
             for ii,jj in rci_skip:
              #print('i:' + str(i) + ' j:' + str(j) + ' mindist:' + str(mindist))
              dist = (ii - row_index) * (ii - row_index) + (jj - column) * (jj - column)
              accept = False
              if dist < mindist:
                  #assume accum 
                  if drain > 0 and list([ii,jj]) not in skiplist:
                      diff = abs(flow_acc[ii,jj] - drain_cells)
                      if diff <= (0.2 * drain_cells):
                          accept = True
                          print('i:' + str(ii) + ' j:' + str(jj) + ' mindist:' + str(mindist) + '     diff(cells in drainage:)' + str(diff))
                      else:
                         skiplist.append(list([ii,jj]))
                  else:
                      accept = True        
              if accept:
                  irow = ii
                  icol = jj
                  mindist = dist
            if irow > 0 and icol > 0:
                find = True
        #set new outlet
        cell_id = "{},{}".format(icol, irow)
        print(" Found pour location in link(col,row):" + cell_id)
        #arcpy.SetValue_management(testout10, cell_id, maxid) 
        
        tcc = Raster(testout10.getRasterInfo())    
        #generate entire basin 
        tcc_basin = Raster(testout10.getRasterInfo())  
        with RasterCellIterator({'rasters':[testout10,tcc,tcc_basin,glink],'skipNoData':[glink]}) as rci_skip:
           for ii,jj in rci_skip:
               if ii == irow and jj == icol:
                   tcc[ii,jj] = maxid
                   tcc_basin[ii,jj] = 1
               else:
                   tcc[ii,jj] = testout10[ii,jj]
        arcpy.CopyRaster_management(tcc, "temptcc") 
        
    
        if i == 0:
            arcpy.CopyRaster_management(tcc_basin, "temptcc_basin") 
            entire_basin = Watershed("flow_dir", "temptcc_basin")
            entire_basin.save(gbasin_from_gage)
            arcpy.conversion.RasterToPolygon(entire_basin, cbasin_from_gage, "NO_SIMPLIFY","Value")
            
            
        testout10 = Raster("temptcc")  
    #End if input gage

    
    #outlet
    out_outl = "out_outl" + suffix
    out_streamlink = "out_streamlink" + suffix
    gout_point = "gout_point" + suffix
    arcpy.conversion.RasterToPoint(testout10, out_outl, 'Value')
    arcpy.conversion.RasterToPolyline(testacc10, out_streamlink)
    testout10.save(gout_point)    
    subbasin = "subbasin" + suffix
    psubbasin = "psubbasin" + suffix
    basin = Watershed("flow_dir", gout_point)
    basin.save(subbasin)
    arcpy.conversion.RasterToPolygon(subbasin, psubbasin, "NO_SIMPLIFY")
    #split subbasin to hillslopes 
    hillslope = "hillslope" + suffix
    arcpy.management.FeatureToPolygon([psubbasin,out_riv_shp], hillslope)
    arcpy.management.AddField(hillslope, "hillslope_id", "LONG")
    fields = ["OBJECTID", "hillslope_id"]
    with arcpy.da.UpdateCursor(hillslope, fields) as cursor:
        # loop through each row in the feature class
        for row in cursor:
            # calculate the value for field2 based on the value in field1
            row[1] = row[0]
            # update the row
            cursor.updateRow(row)
    #clean up small gridcells
    eliminate_criteria = "AREA"
    minimum_area = "100 SquareMeters"
    exclusion_criteria = None
    # Execute the Eliminate tool
    for fc in [psubbasin,hillslope]:
        arcpy.management.AddGeometryAttributes(fc, "AREA")
        tempLayer = "temp"
        #in m2
        expression = '"POLY_AREA" < 90000'
        outFeatureClass = fc + '_clean'
        exclusionExpression = "#"
        # Execute MakeFeatureLayer
        arcpy.MakeFeatureLayer_management(fc, tempLayer)
        # Execute SelectLayerByAttribute to define features to be eliminated
        arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", expression)
        # Execute Eliminate
        arcpy.Eliminate_management(tempLayer, outFeatureClass, "LENGTH", exclusionExpression)
        print("    " + fc + " Done!\n")
    print("  " + str(t_area_km2[i]) + " Done!\n")
    
#clean ups

