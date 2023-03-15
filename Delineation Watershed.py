"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4, param5, param6
                , param7, param8, param9, param10, param11, param12
                , param13, param14, param15, param16, param17
                , param18, param19, param20, param21):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    arcpy.env.scratchWorkspace = param1
    dem = Raster(param2)
    input_outlet_location = param3
    drain = -1
    olat = param4
    olon = param5
    drain = param6 #km2 it's for reference in case the gage is near two main streams; if don't know, set -1
    drain_list = param7
    arcpy.env.overwriteOutput = param8
    wsprefix = param9
    hillprefix = param10
    streamprefix = param11
    gbasin_from_gage = param12
    cbasin_from_gage = param13
    odem = param14
    oslope = param15
    oaspect = param16
    oacc = param17
    odir = param18
    otwi = param19
    ocur = param20
    ohillclasses = param21
    
    arcpy.AddMessage("workspace:" + arcpy.env.workspace)
    
    gdppath = arcpy.env.workspace
    shapefile_path = gdppath[:gdppath.rfind("/")] + '/'
    
    
    
    #basin_grid = Raster("gbasin")
    #basin_shp = "U:/Projects/Colorado_MZ/BigThomson_WS_Shapefile/BigThomson_Shapefile.shp"
    #output_path = param8 + "/"
    #arcpy.AddMessage("Workspace:" + gdppath)
    #outfilleddemtiff = param11 
    #outslopetiff = param12
    
    #gridmetbnd = Raster("gridmet_utm")
    #outFillSink = output_path + outfilleddemtiff
    #outSlope = output_path + outslopetiff
    
    #spatial references
    dem_ref = arcpy.Describe(dem).spatialReference
    geo_ref = arcpy.SpatialReference(4269)
    
    
    
    
    #create point feature
    if input_outlet_location:
    # Create a point feature class
        arcpy.AddMessage("Create outlet feature...")
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
        arcpy.AddMessage("Created ctemp_pour_reproj.")
        #arcpy.Delete_management("XXXXXX")
        
    #TESTING!
    desc = arcpy.Describe(dem)
    #xmin = desc.extent.XMin
    #ymin = desc.extent.YMin
    #xmax = desc.extent.XMax
    #ymax = desc.extent.YMax
    cell_size = desc.meanCellWidth
    #buffer_dist = 100 * cell_size
    #buffer_extent = arcpy.Extent(xmin - buffer_dist, ymin - buffer_dist, xmax + buffer_dist, ymax + buffer_dist)
    # Set the extent environment variable
    arcpy.env.extent = dem
    
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
    
    arcpy.AddMessage("Created dem_filled.")
    
    # Create a flow accumulation raster
    flow_dir = FlowDirection(dem_filled)
    flow_acc = FlowAccumulation(flow_dir, "#", "INTEGER")
    
    slope = Slope(dem_filled)
    aspect = Aspect(dem_filled)
    curvature = Curvature(dem_filled)
    
    out_raster = arcpy.sa.Hillshade(in_raster=dem_filled,azimuth=315,altitude=45,model_shadows="NO_SHADOWS",z_factor=1)
    out_raster.save("hillshade")
    arcpy.AddMessage("Created hillshade.")
    
    #calculate twi
    slope_f = (slope * 1.570796) / 90.0
    tan_slp = Con(slope > 0, Tan(slope_f), 0.001)
    fa_scaled = (flow_acc + 1) * cell_size
    twi = Ln(fa_scaled / tan_slp) #TWI(dem_filled)
    arcpy.AddMessage("Saving filled dem, slope, aspect, and TWI...")
    
    dem_filled.save(odem)
    flow_dir.save(odir)
    flow_acc.save(oacc)
    aspect.save(oaspect)  
    slope.save(oslope) 
    curvature.save(ocur)
    twi.save(otwi)
    
    #generating hillslopes
    # Define the output classified raster
    # Use the Mosaic To New Raster tool to create a composite raster
    arcpy.management.CompositeBands(
        in_rasters="slope;aspect;curvature;TWI;hillshade",
        out_raster="composite5b"
    )
    arcpy.AddMessage("Creating hillslope classes (for generating patch)...")
    # Use the Iso Cluster Unsupervised Classification tool to classify the composite raster
    outUnsupervised = IsoClusterUnsupervisedClassification("composite5b", 10, 50, 15)
    outUnsupervised.save(ohillclasses)
    
    # Threshold the flow accumulation to identify streams
    
    #number of km2 (the first big number is to generate the large basin boundary)
    arcpy.AddMessage("Generating hillslopes...")
    t_area_km2 = drain_list #[25,1]
    t_area_30mcell = []
    for num in t_area_km2:
        cells = int(num * 1000000 / (cell_size * cell_size))
        t_area_30mcell.append(cells)
    
    for i, threshold in enumerate(t_area_30mcell):
        arcpy.AddMessage("i, threshold:" + str(i) + " " + str(threshold) + " drain_tolerence_km2:" + str(t_area_km2[i]))
        suffix = '_' + str(int(t_area_km2[i])) + 'km2'
        test10 = Con(flow_acc > threshold, 1)
        out_str = Con(flow_acc > threshold, 1, 0)
        out_riv_shp = 'f_' + streamprefix + suffix
        arcpy.AddMessage("out_riv_shp:" + out_riv_shp)
        arcpy.conversion.RasterToPolyline(test10, out_riv_shp)
        out_stream = streamprefix + suffix
        test10.save(out_stream)
        # Generate the stream link raster
        out_link = 'glnk_' + streamprefix + suffix
        out_raster = arcpy.sa.StreamLink(out_stream,flow_dir)
        out_raster.save(out_link)
        #links
        glink = Raster(out_link)
        testacc10 = ZonalStatistics(glink, 'Value', flow_acc, "MAXIMUM")
        testout10 = Con(testacc10 == flow_acc, glink)
        
        
        if input_outlet_location:
            #add the observation outlet into this outlet points set
            #set ID
            maxid = int(arcpy.GetRasterProperties_management(glink, "MAXIMUM").getOutput(0)) + 1
            arcpy.AddMessage("maxid:" + str(maxid))
            
            
            #find closed link grid to inpour
            # Create a SearchCursor object to iterate over the cells in the raster
            # Loop through each cell and check its value
            #only need find one time
            if i == 0:
              column = -1
              row_index = -1
              arcpy.AddMessage("Snapping gage to link gridcell...\n")
              with RasterCellIterator({'rasters':[inpour]}) as rci:
                 for ii,jj in rci:
                     if inpour[ii,jj] == 1:
                         row_index = ii
                         column = jj
              if column == -1 or row_index == -1:
                  arcpy.AddMessage("ERROR: Can't find index for gage site!\n")
              else:
                  arcpy.AddMessage(" the gage is located at row:" + str(row_index) + " col:" + str(column))
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
            if i == 0:
                cell_id = "{},{}".format(icol, irow)
                arcpy.AddMessage(" Found pour location in link(col,row):" + cell_id)
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
                entire_basin = Watershed(flow_dir, "temptcc_basin")
                entire_basin.save(gbasin_from_gage)
                arcpy.conversion.RasterToPolygon(entire_basin, cbasin_from_gage, "NO_SIMPLIFY","Value")
                
                
            testout10 = Raster("temptcc")  
        #End if input gage
    
        
        #outlet
        out_outl = 'foutl_' + streamprefix + suffix
        out_streamlink = 'flnk_' + streamprefix + suffix
        gout_point = "goutp_" + streamprefix + suffix
        arcpy.conversion.RasterToPoint(testout10, out_outl, 'Value')
        arcpy.conversion.RasterToPolyline(testacc10, out_streamlink)
        testout10.save(gout_point)    
        subbasin = wsprefix + suffix
        psubbasin = 'f_' + wsprefix + suffix
        gsubbasin = 'g_' + wsprefix + suffix
        basin = Watershed(flow_dir, gout_point)
        basin.save(subbasin)
        arcpy.conversion.RasterToPolygon(subbasin, psubbasin, "NO_SIMPLIFY")
        #split subbasin to hillslopes 
        hillslope = 'f_' + hillprefix + suffix
        ghillslope = 'g_' + hillprefix + suffix
        arcpy.AddMessage("Generating hillslope:" + hillslope)
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
            arcpy.AddMessage("    " + fc + " Done!\n")
            if fc == hillslope:
                arcpy.conversion.FeatureToRaster(outFeatureClass, "hillslope_id", ghillslope, cell_size)
            else:
                arcpy.conversion.FeatureToRaster(outFeatureClass, "gridcode", gsubbasin, cell_size)
        arcpy.AddMessage(" Drain " + str(t_area_km2[i]) + " km  Done!\n")
        
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    param2 = arcpy.GetParameterAsText(2)
    param3 = arcpy.GetParameterAsText(3)
    param4 = arcpy.GetParameter(4)
    param5 = arcpy.GetParameter(5)
    param6 = arcpy.GetParameter(6)
    param7 = arcpy.GetParameter(7)
    param8 = arcpy.GetParameter(8)
    param9 = arcpy.GetParameterAsText(9)
    param10 = arcpy.GetParameterAsText(10)
    param11 = arcpy.GetParameterAsText(11)
    param12 = arcpy.GetParameterAsText(12)
    param13 = arcpy.GetParameterAsText(13)
    param14 = arcpy.GetParameterAsText(14)
    param15 = arcpy.GetParameterAsText(15)
    param16 = arcpy.GetParameterAsText(16)
    param17 = arcpy.GetParameterAsText(17)
    param18 = arcpy.GetParameterAsText(18)
    param19 = arcpy.GetParameterAsText(19)
    param20 = arcpy.GetParameterAsText(20)
    param21 = arcpy.GetParameterAsText(21)
    
    script_tool(param0, param1, param2, param3, param4, param5, param6
                , param7, param8, param9, param10, param11, param12
                , param13, param14, param15, param16, param17
                , param18, param19, param20, param21)
    #arcpy.SetParameterAsText(2, "Result")
