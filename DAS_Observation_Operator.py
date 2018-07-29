'''
# -*- coding: utf-8 -*- 
Copyright of DasPy:
Author - Xujun Han (Forschungszentrum Juelich, Germany)
x.han@fz-juelich.de, xujunhan@gmail.com

DasPy was funded by:
1. Forschungszentrum Juelich, Agrosphere (IBG 3), Juelich, Germany
2. Cold and Arid Regions Environmental and Engineering Research Institute, Chinese Academy of Sciences, Lanzhou, PR China
3. Centre for High-Performance Scientific Computing in Terrestrial Systems: HPSC TerrSys, Geoverbund ABC/J, Juelich, Germany

Please include the following references related to DasPy:
1. Han, X., Li, X., He, G., Kumbhar, P., Montzka, C., Kollet, S., Miyoshi, T., Rosolem, R., Zhang, Y., Vereecken, H., and Franssen, H. J. H.: 
DasPy 1.0 : the Open Source Multivariate Land Data Assimilation Framework in combination with the Community Land Model 4.5, Geosci. Model Dev. Discuss., 8, 7395-7444, 2015.
2. Han, X., Franssen, H. J. H., Rosolem, R., Jin, R., Li, X., and Vereecken, H.: 
Correction of systematic model forcing bias of CLM using assimilation of cosmic-ray Neutrons and land surface temperature: a study in the Heihe Catchment, China, Hydrology and Earth System Sciences, 19, 615-629, 2015a.
3. Han, X., Franssen, H. J. H., Montzka, C., and Vereecken, H.: 
Soil moisture and soil properties estimation in the Community Land Model with synthetic brightness temperature observations, Water Resour Res, 50, 6081-6105, 2014a.
4. Han, X., Franssen, H. J. H., Li, X., Zhang, Y. L., Montzka, C., and Vereecken, H.: 
Joint Assimilation of Surface Temperature and L-Band Microwave Brightness Temperature in Land Data Assimilation, Vadose Zone J, 12, 0, 2013.
'''
from mpi4py import MPI
from concurrent import futures
import netCDF4, numpy, string, smtplib, sys, imp, math, multiprocessing, shutil, fnmatch, shlex
sys.path.append('Utilities')
from DAS_Assim import *
from DAS_Assim_Common import *
from DAS_Utilities import *

#os.system("taskset -pc 0-47 %d" % os.getpid())

def DAS_Observation_Operator(Ensemble_Number,Def_PP,Def_Print, active_nodes_server, job_server_node_array, DAS_Depends_Path, Def_Region, Soil_Layer_Num, Grid_Resolution_CEA, DasPy_Path, \
            Start_Year, Start_Month, Start_Day, Start_Hour, LATIXY_Mat, LONGXY_Mat, Mask_Index, Station_XY, Station_XY_Index, N0, nlyr,
            Def_First_Run_RTM, DAS_Output_Path, CMEM_Work_Path_Array, Datetime_Start, Datetime_Stop, Datetime_Stop_Init, Datetime_Initial,
            maxpft, PCT_PFT_High, PCT_PFT_Low, PCT_PFT_WATER, Density_of_liquid_water, Run_Dir_Array, Row_Numbers_String, Col_Numbers_String,
            Forcing_File_Path_Array, history_file_name, Constant_File_Name, NAvalue, CLM_NA,
            Row_Numbers, Col_Numbers, Variable_Assimilation_Flag,Variable_List,Variable_ID,SensorVariable,SensorType,
            Soil_Density, DAS_Data_Path, Region_Name, mksrf_edgen, mksrf_edges, mksrf_edgew, mksrf_edgee, Grid_Resolution_GEO, Soil_Layer_Index_DA, Soil_Texture_Layer_Opt_Num,
            NC_FileName_Assimilation_2_Constant, NC_FileName_Assimilation_2_Diagnostic, NC_FileName_Assimilation_2_Parameter,
            NC_FileName_Assimilation_2_Initial, NC_FileName_Assimilation_2_Bias, omp_get_num_procs_ParFor, octave, r):
    
    #NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][17, :, :] = 1.0
    print '=============================================================================================================='
                        
    if Variable_Assimilation_Flag[Variable_List.index("Soil_Moisture")] == 1:
        if Variable_ID.count('Neutron') > 0:
            if SensorVariable[Variable_ID.index('Neutron')] == "Soil_Moisture":
                SensorType_Name = SensorType[Variable_ID.index('Neutron')]
                print "################### Using COSMOS as Observation Operator"
                if Def_PP and Ensemble_Number > 1:
                    
                    NC_File_Out_Assimilation_2_Initial = netCDF4.Dataset(NC_FileName_Assimilation_2_Initial, 'r+')
                    Prop_Grid_Array_H_Trans = NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][:,:,:,:]
                    
                    print "********************************************** Using PP to Accelerate COSMOS"             
                    Job_Num_Per_Node = int(numpy.ceil(float(Ensemble_Number) / len(active_nodes_server)))
                    print "The following submits",Job_Num_Per_Node,"jobs on each node and then retrieves the results"
                    
                    if Job_Num_Per_Node == 0:
                        Job_Num_Per_Node = 1
                    job_server_node_results = []
                    Ens_Index = 0
                    
                    Job_Num_Per_Node_Index = 0
                    while Job_Num_Per_Node_Index < Job_Num_Per_Node and Ens_Index < Ensemble_Number:
                        for Node_Index in range(len(active_nodes_server)):
                            job_server_node = job_server_node_array[numpy.min([Job_Num_Per_Node_Index+Node_Index*len(job_server_node_array)/len(active_nodes_server),len(job_server_node_array)-1])]
                            #job_server_node = job_server_node_array[Node_Index]
                            if Ens_Index > Ensemble_Number - 1:
                                break
                            job_server_node_results.append(job_server_node.submit(Run_COSMOS, args=(Ens_Index, DAS_Depends_Path, Def_Region, Def_PP, Def_Print, N0, nlyr, Soil_Layer_Num, Grid_Resolution_CEA, DasPy_Path, Row_Numbers, Col_Numbers, 
                                                                                                    NC_FileName_Assimilation_2_Constant, NC_FileName_Assimilation_2_Diagnostic, NC_FileName_Assimilation_2_Initial, NC_FileName_Assimilation_2_Bias, omp_get_num_procs_ParFor),
                                          depfuncs=(moving_average_2d,),
                                          modules=("numpy", "netCDF4", "sys", "os", "re", "unittest", "time", "datetime", "shutil", "fnmatch", "subprocess", "string", "socket", "gc", "imp", "getpass", "calendar", "scipy.signal",'scipy.weave', 'scipy.ndimage'), group='COSMOS'))
                            
                            Ens_Index = Ens_Index + 1
                        Job_Num_Per_Node_Index = Job_Num_Per_Node_Index + 1
                            
                    for job_server_node in job_server_node_array:
                        job_server_node.wait()
                        if Def_Print >= 2:
                            job_server_node.print_stats()
                    
                    if len(job_server_node_results) > 0:
                        for job in job_server_node_results:
                            job_index = job_server_node_results.index(job)
                            if job_index > (Ensemble_Number - 1):
                                break
                            if Def_Print:
                                print "Results of ",job_index,"is", job()[Station_XY_Index[0][1],Station_XY_Index[0][0]]
                            Prop_Grid_Array_H_Trans[job_index, Variable_List.index("Soil_Moisture"), :, :] = job()
                    
                    NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][:,:,:,:] = Prop_Grid_Array_H_Trans
                    del Prop_Grid_Array_H_Trans
                    NC_File_Out_Assimilation_2_Initial.sync()
                    NC_File_Out_Assimilation_2_Initial.close()
                else:
                    print "********************************************** Run COSMOS Sequentially"
                    Prop_Grid_Array_H_Trans_Temp = numpy.zeros((Ensemble_Number,Row_Numbers,Col_Numbers),dtype=numpy.float32)
                    for Ens_Index in range(Ensemble_Number):
                        Prop_Grid_Array_H_Trans_Temp[Ens_Index,:,:] =  Run_COSMOS(Ens_Index, DAS_Depends_Path, Def_Region, Def_PP, Def_Print, N0, nlyr, Soil_Layer_Num, Grid_Resolution_CEA, DasPy_Path, Row_Numbers, Col_Numbers, 
                                                                                  NC_FileName_Assimilation_2_Constant, NC_FileName_Assimilation_2_Diagnostic, NC_FileName_Assimilation_2_Initial, NC_FileName_Assimilation_2_Bias, omp_get_num_procs_ParFor, octave, r)
                    NC_File_Out_Assimilation_2_Initial = netCDF4.Dataset(NC_FileName_Assimilation_2_Initial, 'r+')
                    NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][:, Variable_List.index("Soil_Moisture"), :, :] = Prop_Grid_Array_H_Trans_Temp
                    NC_File_Out_Assimilation_2_Initial.sync()
                    NC_File_Out_Assimilation_2_Initial.close()
    
        
        if Variable_ID.count('TBH') > 0:
            if SensorVariable[Variable_ID.index('TBH')] == "Soil_Moisture":
                SensorType_Name = SensorType[Variable_ID.index('TBH')]
                print "################### Using CMEM as Observation Operator"
                if Def_First_Run_RTM:
                    CMEM_Work_Path_Home = DAS_Output_Path+"ObsModel/CMEM/"+Region_Name
                    if not os.path.exists(CMEM_Work_Path_Home):
                        os.makedirs(CMEM_Work_Path_Home)
                    
                    if Ensemble_Number == 1:
                        CMEM_Work_Path_Array.append(CMEM_Work_Path_Home)                                    
                        shutil.copy(DasPy_Path+"ObsModel/CMEM/bin/cmem",CMEM_Work_Path_Home+"/cmem")
                        shutil.copy(DasPy_Path+"ObsModel/CMEM/bin/LSM_VERTICAL_RESOL.asc",CMEM_Work_Path_Home+"/LSM_VERTICAL_RESOL.asc")
                    else:
                        for Ens_Index in range(Ensemble_Number):
                            CMEM_Work_Path_Temp = CMEM_Work_Path_Home+"/Ens"+str(Ens_Index+1)
                            if not os.path.exists(CMEM_Work_Path_Temp):
                                os.makedirs(CMEM_Work_Path_Temp)                                        
                            shutil.copy(DasPy_Path+"ObsModel/CMEM/bin/cmem",CMEM_Work_Path_Temp+"/cmem")
                            shutil.copy(DasPy_Path+"ObsModel/CMEM/bin/LSM_VERTICAL_RESOL.asc",CMEM_Work_Path_Temp+"/LSM_VERTICAL_RESOL.asc")
                            CMEM_Work_Path_Array.append(CMEM_Work_Path_Temp)
                
                Tair_Time = (Datetime_Stop - Datetime_Initial).days + (Datetime_Stop - Datetime_Initial).seconds / 86400.0   # DoY                                                     
                                
                if Def_First_Run_RTM:
                    # Read CMEM Parameters
                    Read_CMEM_Par(Def_Region, DAS_Data_Path, DAS_Output_Path, Region_Name, Row_Numbers, Col_Numbers, Datetime_Stop, maxpft, PCT_PFT_High, PCT_PFT_Low, PCT_PFT_WATER, NC_FileName_Assimilation_2_Constant)
                
                if Def_PP and Ensemble_Number > 1:
                    
                    NC_File_Out_Assimilation_2_Initial = netCDF4.Dataset(NC_FileName_Assimilation_2_Initial, 'r+')
                    Prop_Grid_Array_H_Trans = NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][:,:,:,:]
                    
                    print "********************************************** Using PP to Accelerate CMEM"
                    Job_Num_Per_Node = int(numpy.ceil(float(Ensemble_Number) / len(active_nodes_server)))
                    print "The following submits",Job_Num_Per_Node,"jobs on each node and then retrieves the results"
                                                    
                    if Job_Num_Per_Node == 0:
                        Job_Num_Per_Node = 1
                    job_server_node_results = []
                    Ens_Index = 0
                    
                    Job_Num_Per_Node_Index = 0
                    while Job_Num_Per_Node_Index < Job_Num_Per_Node and Ens_Index < Ensemble_Number:
                        for Node_Index in range(len(active_nodes_server)):
                            job_server_node = job_server_node_array[numpy.min([Job_Num_Per_Node_Index+Node_Index*len(job_server_node_array)/len(active_nodes_server),len(job_server_node_array)-1])]
                            #job_server_node = job_server_node_array[Node_Index]
                            if Ens_Index > Ensemble_Number - 1:
                                break
                            job_server_node_results.append(job_server_node.submit(Run_CMEM, args=(Ens_Index, NC_FileName_Assimilation_2_Constant, NC_FileName_Assimilation_2_Diagnostic, NC_FileName_Assimilation_2_Initial, NC_FileName_Assimilation_2_Bias, NC_FileName_Assimilation_2_Parameter, Forcing_File_Path_Array, history_file_name, CMEM_Work_Path_Array, \
                                                                                                  mksrf_edgen, mksrf_edges, mksrf_edgew, mksrf_edgee, Grid_Resolution_GEO, Row_Numbers, Col_Numbers, Datetime_Start, Datetime_Stop, Datetime_Stop_Init,
                                            Def_Region, DAS_Data_Path, Region_Name, Constant_File_Name, Soil_Layer_Num, NAvalue, CLM_NA, DasPy_Path, Def_Print, Density_of_liquid_water, Run_Dir_Array, Row_Numbers_String, Col_Numbers_String, Station_XY_Index,
                                            Tair_Time, Soil_Texture_Layer_Opt_Num, SensorType_Name, Mask_Index, Station_XY, DAS_Output_Path),
                                              modules=("numpy", "netCDF4", "sys", "os", "re", "unittest", "time", "datetime", "shutil", "fnmatch", "subprocess", "string", "socket", "gc", "imp", "getpass", "calendar", 'scipy.weave',), group='CMEM'))
                            
                            Ens_Index = Ens_Index + 1
                        Job_Num_Per_Node_Index = Job_Num_Per_Node_Index + 1
                            
                    for job_server_node in job_server_node_array:
                        job_server_node.wait()
                        if Def_Print >= 2:
                            job_server_node.print_stats()
                    
                    if len(job_server_node_results) > 0:
                        for job in job_server_node_results:
                            job_index = job_server_node_results.index(job)
                            if job_index > (Ensemble_Number - 1):
                                break
                            if Def_Print:
                                print "Results of ",job_index,"is", job()[Station_XY_Index[0][1],Station_XY_Index[0][0]]
                            Prop_Grid_Array_H_Trans[job_index, Variable_List.index("Soil_Moisture"), :, :] = job()
                            #print numpy.min(Prop_Grid_Array_H_Trans[job_index,0,:,:]),numpy.max(Prop_Grid_Array_H_Trans[job_index,0,:,:]),numpy.min(job()),numpy.max(job())
                    NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][:,:,:,:] = Prop_Grid_Array_H_Trans
                    del Prop_Grid_Array_H_Trans
                    NC_File_Out_Assimilation_2_Initial.sync()
                    NC_File_Out_Assimilation_2_Initial.close()
    
                    Def_First_Run_RTM = 0
                    
                else:
                    print "############################################### Run CMEM Sequentially"
                    Prop_Grid_Array_H_Trans_Temp = numpy.zeros((Ensemble_Number,Row_Numbers,Col_Numbers),dtype=numpy.float32)
                    for Ens_Index in range(Ensemble_Number):
                        Prop_Grid_Array_H_Trans_Temp[Ens_Index, :, :] = Run_CMEM(Ens_Index, NC_FileName_Assimilation_2_Constant, NC_FileName_Assimilation_2_Diagnostic, 
                                                                                 NC_FileName_Assimilation_2_Initial, NC_FileName_Assimilation_2_Bias, NC_FileName_Assimilation_2_Parameter, 
                                                                                 Forcing_File_Path_Array, history_file_name, CMEM_Work_Path_Array, mksrf_edgen, mksrf_edges, mksrf_edgew, mksrf_edgee, 
                                                                                 Grid_Resolution_GEO, Row_Numbers, Col_Numbers, Datetime_Start, Datetime_Stop, Datetime_Stop_Init,
                                Def_Region, DAS_Data_Path, Region_Name, Constant_File_Name, Soil_Layer_Num, NAvalue, CLM_NA, DasPy_Path, Def_Print, Density_of_liquid_water, 
                                Run_Dir_Array, Row_Numbers_String, Col_Numbers_String, Station_XY_Index,
                                Tair_Time, Soil_Texture_Layer_Opt_Num, SensorType_Name, Mask_Index, Station_XY, DAS_Output_Path)
                    NC_File_Out_Assimilation_2_Initial = netCDF4.Dataset(NC_FileName_Assimilation_2_Initial, 'r+')
                    NC_File_Out_Assimilation_2_Initial.variables['Prop_Grid_Array_H_Trans'][:, Variable_List.index("Soil_Moisture"), :, :] = Prop_Grid_Array_H_Trans_Temp
                    NC_File_Out_Assimilation_2_Initial.sync()
                    NC_File_Out_Assimilation_2_Initial.close()
                    
                    
