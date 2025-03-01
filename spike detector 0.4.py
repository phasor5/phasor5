#Instructions: 
#    Place in a folder with a single .txt files generated by NACshow.
''' ============== ====================== ====================
    ==============    User parameters     ===================
    ============== ====================== ===================='''
    
fs = 10000 #Hz --> Must match the sampling frequency of the experiment. Program cannot interpret sampling rate from the data files.
graph_size = (120,12) # Dimensions of the output graph image file. Not sure what units these are, maybe inches?????????????
trial_numbers = [0, 1, 2, 3] #The trial number(s) to process - provide a list with [] .
t_display_units = "seconds" #DON'T CHANGE Yet.

Mode = 1  #not used yet.
'''Modes:   1: inter-stim only
            2: pre-stim-post comarison
            3: stim-post comparion
            4: post only
'''
#t_analyze_window = (0, 2.5) #[secs] start & end time of processing each trial, as a list of two numbers. Write "all" to not trim data.
t_analyze_window = "all"

filter_type = "highpass" #choose "highpass",  "lowpass", "bandpass" or "none"
    #highpass - no phase lag. bandpass causes phase lag.
lowcut = 300 #(Hz)
highcut = 4000.0 #(Hz). 
filter_order = 2 #Two is best.
spike_thresholds = [0.025, 0.035, 0.045]  #[mV] list of numbers. Negative = downward deflecting spikes. Positive = upward deflecting spikes.

graph_x_interval = "auto" #[seconds] or write "auto"
graph_y_interval = 0.1 #Doesn't do anything yet.
#graph_focus = "whole trial" #!!!!!!!!!!! Choose "whole trial" or "stim train" 

# ====== Stim detection function parameters ==========
stim_peak = 0.8 #[mV] Positive threshold to trigger stim artefact detector.
stim_blanking = 2 #[ms], width of stim artefact to be blanked, around midpoint of stim artefact
slope_dt = 4 #[samples], the time increment over which to check stim slope
stim_slope_thresh = 0.12

stim_refractory = 0 #[ms] Period between stim and start of EPSP.
#epsp_padding = 100 #[ms], gap between EPSP analysis and stim artefact.
epsp_highcut = 500 #[Hz] cutoff freq of EPSP LPF. 
epsp_length = 25 #[ms] length of EPSP after stim refractory period.

''' ========= END USER PARAMETERS ====================================================== '''

''' ============== ====================== ====================
    ==============    Start of Program    ===================
    ============== ====================== ===================='''

# IMPORT DATA ===============


#from decimal import Decimal
from scipy.io.wavfile import write
import os
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')
from scipy.signal import butter, lfilter, filtfilt
import xlsxwriter
#from playsound import playsound
import time
#from numpy import loadtxt
#import sys
from scipy.stats import linregress


start_time = time.time()
master_start_time = time.time()

#Fast load of file data into one list of floats, and generate indices of gaps between trial data
directory = "/"
dir_list = os.listdir(".")
print("Text files in this directory:")
for file_name in dir_list:
    if ('.txt' in file_name[-4:]):
        print(file_name)
        file = file_name
#print("time initial import of data",time.time()-start_time)
print("====================")
print("File to be processed:")
print(file)
print("Processing file, please wait.... ")

#===== Slow file loading ========

start_time = time.time()

f = open(file, 'r')
data = np.empty(1)
data = [x.strip().split('\t') for x in f]
f.close() 
print("time doing strip split",time.time()-start_time)

#data = np.empty(1)
#data = [x.strip().split('\t') for x in f]
start_time = time.time()

data_0 = [item[0] for item in data] #gets rid of those annoying quotations marks that each data item has when imported.
data_float = [float(x) if x!='' else 0 for x in data_0] #if gap in data, replace with a 0.
print("time converting to floats",time.time()-start_time)
del data_0
# ============================


print("file data beginning snippet",data_float[0:10])
gap_list = [(index) for index, element in enumerate(data) if element == ['']] #generates list of indices for starts of trials 
gap_list = ([-1] + gap_list)   
n_trials = len(gap_list)-1 #!!!!!!! CHEK THE -1 OK WItH MULTIPLE TRIALS
n_trials = len(gap_list) #!!!!!!! CHEK THE -1 OK WItH MULTIPLE TRIALS
#print("gap_list",gap_list)
#print("n_trials",n_trials)
del data
#Trial number x starts at gap_list[x]
end_time = time.time()
time_elapsed = end_time - start_time
print("Finished initial loading of data, total time elapsed (seconds): ",time_elapsed)

#print("Trial data length",len(master_data))


'''
 ====================================================
 ======              FILTER FUNCTIONS               =======:
 ===================================================='''
def high_pass_filter(data, fc, fs, order):
    nyq = 0.5 * fs
    cutoff = fc/nyq
    #scipy.signal.butter(9, Wn, btype='low', analog=False, output='ba', fs=None) #returns two items, 
    b, a = butter(order, cutoff, btype='highpass', analog=False, output='ba', fs=None) #returns critical bounds to be used for actual filter , 
    filtered_data = lfilter(b, a, data)
    return filtered_data

'''def low_pass_filter(data, fc, fs, order): #has phase shift
    nyq = 0.5 * fs
    cutoff = fc/nyq
    #scipy.signal.butter(9, Wn, btype='low', analog=False, output='ba', fs=None) #returns two items, 
    b, a = butter(order, cutoff, btype='lowpass', analog=False, output='ba', fs=None) #returns critical bounds to be used for actual filter , 
    filtered_data = lfilter(b, a, data)
    return filtered_data'''

def low_pass_filter2(data, fc, fs, order): #no phase shift
    nyq = 0.5 * fs
    cutoff = fc/nyq
    #scipy.signal.butter(9, Wn, btype='low', analog=False, output='ba', fs=None) #returns two items, 
    b, a = butter(order, cutoff, btype='lowpass', analog=False, output='ba', fs=None) #returns critical bounds to be used for actual filter , 
    filtered_data = filtfilt(b, a, data)
    return filtered_data


def butter_bandpass(lowcut, highcut, fs, order=filter_order):
    nyq = 0.5 * fs
    low = lowcut / nyq
    #print("low",low)
    high = highcut / nyq
    #print("high",high)
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=filter_order): #called if bandpass
    b, a = butter_bandpass(lowcut, highcut, fs, order=filter_order)
    y = lfilter(b, a, data)
    return y

''' ============================================================
 ====== Spike detection and signal processing functions  =======:
 =============================================================='''

def generate_starts_stops(sig,spike_threshold): #filtered_signal = array, spike_threshold = voltage value
   # for jjj in range(siglength-1)
    #down_swings=filtered_signal.astype(float) #make down_swings type a float
    #down_swings_cut=down_swings<spike_threshold
    
   #4/26/21: spiketrain_overthresh_bool declare size beforehand.
   if spike_threshold > 0:
       deflection = "up"
   else:
       deflection = "down"
   print("Spike deflection = ", deflection, " threshold ", spike_threshold)
   start_time = time.time()

   starts = []
   stops = []   
   spiketrain_overthresh_bool = []
   i = 0
   siglength = len(sig)
   #print("siglength from generate starts stops ",siglength)
   spiketrain_overthresh_bool = [0] * siglength
   print("Spike detector running.....")
   for i in range(siglength):
      progress_indicator = divmod(i, fs)
      if progress_indicator[1] == 0:
          print(i/fs, "seconds processed")
          
      if deflection == "up":
          #Upward spike deflection
          #print("debug sig, spike_threshold",sig[i],",",spike_threshold)
          if float(sig[i]) >= float(spike_threshold):  # 
             #spiketrain_overthresh_bool = np.append(spiketrain_overthresh_bool, "1")
             spiketrain_overthresh_bool[i] = 1
             #print("      threshold sample")
          else:
             #spiketrain_overthresh_bool = np.append(spiketrain_overthresh_bool, "0")
             spiketrain_overthresh_bool[i] = 0
      elif deflection == "down":     
          #Downward spike deflection:
          if float(sig[i]) <= float(spike_threshold):  
             spiketrain_overthresh_bool[i] = 1
             #print("  threshold sample, sig = ",float(sig[i]), "spike_threshold ", float(spike_threshold))
          else:
             spiketrain_overthresh_bool[i] = 0
             #print(" under threshold sample, sig = ",float(sig[i]), "spike_threshold ", float(spike_threshold))
  
      if i > 0:
          if int(spiketrain_overthresh_bool[i]) > int(spiketrain_overthresh_bool[i-1]): # !!!!!!!! do comparison without converting to int?
             starts.append(i)
             #print("*Spike Detected ")

          if spiketrain_overthresh_bool[i-1] > spiketrain_overthresh_bool[i]:
             stops.append(i)
             
   #Generate spike widths...
   starts_stops_length = int(len(starts))
   spike_widths = []
   for k in range(0,starts_stops_length-1):
       spike_widths = np.append(spike_widths, stops[k] - starts[k])
   n_spikes = len(starts)
   print("number of regular spikes detected",n_spikes)
   end_time = time.time()
   time_elapsed = end_time - start_time
   print("time elapsed detecting regular spikes",time_elapsed)

   return(starts, stops, spike_widths, n_spikes)


def stim_train_detect(sig, stim_cut):     #stim deflection up only for now
    start_time = time.time()
    stim_starts = []
    stim_stops = []
    i = 0
    siglength = len(sig)
    #print("stim_train_detect: sig length",siglength)
    #print("sig shape",np.shape(sig))
    #print("sig sample",sig[0:10])
    stimtrain_overthresh_bool = [0] * siglength
    is_included = "no"
    for i in range(siglength): # i = [samples]
          #progress_indicator = divmod(i, fs)
          #if progress_indicator[1] == 0:
              #print("Sample number: ",i)
           
              #Upward spike deflection:
          #print("type stim_cut ",type(stim_cut))
          if float(sig[i]) >= float(stim_cut):  # upward deflection
               stimtrain_overthresh_bool[i] = 1
               #print("      threshold sample")
          else:
               stimtrain_overthresh_bool[i] = 0
          if i > 0:
              if (stimtrain_overthresh_bool[i]) > (stimtrain_overthresh_bool[i-1]): 
                 #check slope before adding start
                 slope, intercept, r, p, se = linregress([i-slope_dt, i], [sig[i-slope_dt],sig[i]])
                 #print("candidate starts slope", slope, "at ", sample_to_sec(i), "seconds")
                 if slope >= stim_slope_thresh:
                     stim_starts.append(i)
                     print("*Stim artefact rising edge detected, slope ",slope, "at ",sample_to_sec(i))
                     is_included = "yes"
                 else:
                     is_included = "no"
              if stimtrain_overthresh_bool[i-1] > stimtrain_overthresh_bool[i]:
                 if is_included == "yes":
                     #stim_stops = np.append(stim_stops, i)\
                     #slope, intercept, r, p, se = linregress([i-slope_dt, i], [sig[i-slope_dt],sig[i]])
                     #print("stim stop at ", sample_to_sec(i))
                     #if slope <= -stim_slope_thresh:
                     stim_stops.append(i)
    
    starts_stops_length = int(len(stim_starts))
    stim_spike_widths = []
    for k in range(0,starts_stops_length-1):
        stim_spike_widths = np.append(stim_spike_widths, stim_stops[k] - stim_starts[k])
    stim_n_spikes = len(stim_starts)
    print("number of stim spikes detected",stim_n_spikes, ", at locations", stim_starts)
    end_time = time.time()
    time_elapsed = end_time - start_time

    print("time elapsed detecting stim spikes",time_elapsed)
    print("stim starts",stim_starts)
    print("stim stops",stim_stops)

    return(stim_starts, stim_stops, stim_spike_widths, stim_n_spikes)
        

def remove_stim_artefacts(stim_starts, stim_stops, sig_data):
    #write zeros between stim start and stop
    #print("remove_stim_artefacts stim starts stops",stim_starts,stim_stops)
    stim_midpoints = []
    for i in range(len(stim_starts)):
        stim_midpoints.append((stim_starts[i] + stim_stops[i])/2)
    #stim_midpoints = [(i + j)/2 for i in stim_starts for j in stim_stops]
    print("stim_midpoints",stim_midpoints)
    sig_blank_starts = [(i - (stim_blanking/2000)*fs) for i in stim_midpoints]
    sig_blank_stops = [(i + (stim_blanking/2000)*fs) for i in stim_midpoints]
    for i, j in zip(sig_blank_starts, sig_blank_stops):
        sig_data[int(i):int(j)] = 0
    
    stim_midpoints_scaled = [sample_to_sec(x) for x in stim_midpoints]
    print("stim artefacts removed at",stim_midpoints_scaled, " seconds")
    return sig_data, sig_blank_starts, sig_blank_stops, stim_midpoints
        

def remove_epsps(stim_starts, stim_stops, signal):
    #takes whole signal and subtracts low freq waveform proceeding stim artefact.
    # returns signal, list of starts, list of stops of epsp removal section
    epsp_starts = []
    epsp_stops = []
    for i in range(len(stim_starts)):
        # print("remove epsp i",i)
        epsp_t_start = int(stim_stops[i] + (stim_refractory/1000)*fs) #[samples]
        epsp_t_stop = int(epsp_t_start + (epsp_length/1000)*fs) #[samples]
        epsp_starts.append(epsp_t_start)
        epsp_stops.append(epsp_t_stop)
        print("epsp_t_start (secs)",sample_to_sec(epsp_t_start))
        print("epsp_t_stop (secs)",sample_to_sec(epsp_t_stop))
        sig_epsp_waveform = low_pass_filter2(signal[epsp_t_start:epsp_t_stop], epsp_highcut, fs, order=filter_order)
        #subtract above from whole signal between indices.
        signal[epsp_t_start:epsp_t_stop] = signal[epsp_t_start:epsp_t_stop] - sig_epsp_waveform
        '''
        plt.figure(figsize=graph_size)
        title = "EPSP"
        plt.title(title)
        plt.xlabel(t_display_units)
        #Plot neural data
        plt.plot(range(epsp_t_start,epsp_t_stop), sig_epsp_waveform, linewidth=1) # # filtered signal'''
    return signal, epsp_starts, epsp_stops
        #Another way to do it would have been:
        #np.polyfit(range(epsp_t_start, epsp_t_stop), signal[0], deg, rcond=None, full=False, w=None, cov=False)

def stim_period(stim_mids): #Returns the mean period between stim spikes
    inter_stim_intervals = [0] * (len(stim_mids)-1)
    for i in range(len(stim_mids)-1):
        inter_stim_intervals[i] = stim_mids[i+1] - stim_mids[i]
    print("inter_stim_intervals",inter_stim_intervals)
    stim_period_ = sum(inter_stim_intervals)/len(inter_stim_intervals)
    return stim_period_

def spike_stats(stim_mids, starts): #returns spike_id (which stim spike the spike proceeds), and isi_list
    '''Mode 1: Look at interstim interval spikes'''
    
    #Generate spike ID's...:
    #append stim_mids with a virtual extra stim to categorize "post" spikes
    #stim_mids2=stim_mids
    #stim_mids2.append(stim_mids[-1]+(stim_mids[-1]-stim_mids[-2]))

    spike_ids = np.digitize(starts, stim_mids, False) #Spike number 0 means pre-stim spike
                        
    #ISI Calculations: each spike except the first has a corresponding ISI.
    isi_list = [0] * (len(starts))
    #print("(starts)",len(starts))
    #print("starts",[sample_to_sec(x) for x in starts])
    #print("len(isi_list)",len(isi_list))
    for i in range(len(isi_list)-1):
        isi_list[i+1] = (starts[i+1] - starts[i])/fs
    #print("isi list",isi_list)
    spikes_per_stim = [0] * len(stim_mids)
    #print("length stim mids",len(stim_mids))
    for i in range(len(stim_mids)):
        j = i +1
        #print("stim mids i",j)
        for ID in spike_ids:
            if ID == j:
                spikes_per_stim[i] += 1    
            
    av_isi_per_stim = 0
    sd_isi_per_stim = 0
    #spike_IDs, ISIs, spikes_per_stim, av_ISI_per_stim, sd_ISI_per_stim 
    if len(spike_ids) == 0: #If no spikes were detected, need spike_ids to be not empty.
        spike_ids = 0
    return spike_ids, isi_list, spikes_per_stim, av_isi_per_stim, sd_isi_per_stim

def write_worksheet(starts, stim_starts, ISIs, spike_id, threshold, info): #Per input file writes an xlsx file containing list of ISI's, basic stats and filtered signal.
    #Works w/ open workbook 
    print("Writing to Excel file.... ")
    if spike_id[0] == 0:
        stim_sheet_indices = []
    else:
        stim_sheet_indices = [0]

    for i in range(len(spike_id)-1):
            if spike_id[i] != spike_id[i+1]:
                stim_sheet_indices.append(i)
    stim_sheet_indices = [i + 2 for i in stim_sheet_indices]
    #print("stim sheet indices",stim_sheet_indices)
        
    #bookname = file[:-4] +" Trial " + str(trial_number) + ".xlsx"
    #workbook = xlsxwriter.Workbook(bookname) 
    worksheet = workbook.add_worksheet(str("Trial "+str(trial_number)+" thresh"+str(threshold)))


    worksheet.write(0,0, "Stim time (s)")
    worksheet.write(0,1, "Spike time (s)")
    worksheet.write(0,2, "Stim Spike #")
    worksheet.write(0,3, "ISI")
    worksheet.write(0,5, "Spikes/stim")
    worksheet.write(0,7, "Info")
    worksheet.write(1,7, info)

    print("length stim starts",len(stim_starts))
    print("length stim_sheet_indices",len(stim_sheet_indices))

    for i in range(len(stim_sheet_indices)):
        worksheet.write(stim_sheet_indices[i],0, stim_starts[i])
    [worksheet.write(i+1, 1 , starts[i]) for i in range(len(starts))]
    [worksheet.write(i+1, 2 , spike_id[i]) for i in range(len(spike_id))]
    [worksheet.write(i+1, 3 , ISIs[i]) for i in range(len(ISIs))]
    [worksheet.write(i+1, 5 , spikes_per_stim[i]) for i in range(len(spikes_per_stim))]

    '''
    if Mode == "1":
        for i in range(len(starts_scaled)):
            worksheet.write(i, 0, starts_scaled[i])
            workbook.close()
    '''
def sample_to_sec(samples): #converts a sample number to absolute time in seconds
    if t_analyze_window == "all":
        secs = samples/fs
    else:
        secs = samples/fs + t_analyze_window[0]
    return secs 
    
'''======================================
=======     END OF FUNCTIONS     ========
======================================'''
Run = "yes"

#new sheet for each trial and threshold
#Add info to graphs. Threshold, filter , y axis values and x axis.
#Graph title =  Trial number and threshold.

#bookname = file[:-4] +" Trial " + str(trial_number) + ".xlsx"

start_time = time.time()

while Run == "yes":
    #Create new Excel file.
    bookname = file[:-4] +" Trial spike data.xlsx"
    workbook = xlsxwriter.Workbook(bookname) 

    for trial_number in trial_numbers:
        #One graph per trial. 
        print("Processing trial number ",trial_number)
        trial_number = trial_number #!!!!!!! Is this gonna work?

            
        #====== Pick trial to assign to master_data  =========           
        trial_data = data_float[(gap_list[trial_number]+1):(gap_list[trial_number+1])]
        master_data = np.array(trial_data)
        del trial_data
    
        #====== Trim data  =========           
        if t_analyze_window != "all": #Should the data be trimmed?
            print("Data is being trimmed:")
            if int(fs*t_analyze_window[0]) < len(master_data): 
                t_startpoint = int(fs*t_analyze_window[0]) #[samples]
                print("   t startpoint",t_startpoint, " samples")
                if int(fs*t_analyze_window[1]) < len(master_data):
                    t_endpoint = int(fs*t_analyze_window[1]) #[samples]
                    print("   t_endpoint", t_endpoint, " samples")
                else:
                    t_endpoint = int(len(master_data)) #[samples]
                    print("endpoint not trimmed, t endpoint",t_endpoint, " samples")    
            #trim from time 0 to start point
            if t_startpoint > 0: #remove sample data from 0 to startpoint
                #trimmed_data = np.delete(master_data, 1, range(0, t_startpoint+1)) #remove columns 
                #trimmed_data = np.delete(master_data, 1, range(0, t_startpoint+1)) #remove columns 
                trimmed_data = np.delete(master_data,np.s_[0:t_startpoint+1],axis=0)
            else:
                trimmed_data = master_data 
            #trim from t_endpoint to end of data.
            if len(master_data) > t_endpoint: #if data goes on beyond the specified end point time.
                n_end_trim = len(master_data) - t_endpoint 
                if n_end_trim > 0:
                    #print("end trim n",n_end_trim)
                    #trim from (last index - n_end_trim) to last index
                    print("master data length",len(master_data))
                    print("trimmed data shape",np.shape(trimmed_data))
        
                    n_row = int(np.shape(trimmed_data)[0])
                    #print("trimmed data type",type(trimmed_data))
                    #trimmed_data = np.delete(trimmed_data, 0, range(n_row - n_end_trim, n_row))
                    trimmed_data = np.delete(trimmed_data, np.s_[(n_row-n_end_trim): n_row],axis=0)
            print("original data shape",master_data.shape)
            print("trimmed_data shape",trimmed_data.shape)
        else: #no trimming occurs.
            t_startpoint = 0 #[samples]
            #print("master_Data type",type(master_data))
            if type(master_data) == list:
                t_endpoint = int(len(master_data)) #[samples]
            else:
                t_endpoint = int(len(master_data)) #[samples]
            print("data not trimmed. t startpoint",t_startpoint)
            print("   t endpoint",t_endpoint)
            trimmed_data = master_data 
        end_time = time.time()
        time_elapsed = end_time - start_time
        print("time elapsed trimming data",time_elapsed)
        print("t_endpoint [samples]: ",t_endpoint)
        y_values = trimmed_data
        del trimmed_data
        
        #==========  STIM AND EPSP PROCESSING  ===========
        raw_unblanked_sig = np.array(y_values)
        
        stim_starts, stim_stops, stim_widths, stim_n_spikes = stim_train_detect(y_values,stim_peak) # Generate stim_starts etc.
        
        y_values, stim_blank_starts, stim_blank_stops, stim_midpoints = remove_stim_artefacts(stim_starts, stim_stops, y_values) # Remove stim artefact from signal
        y_values, epsp_starts, epsp_stops = remove_epsps(stim_starts, stim_stops, y_values) #remove EPSP from signal
        
        #  ========  UNIT SCALING, SAMPLES -> SECONDS: ================================= 
        if t_analyze_window == "all":
            trim_offset = 0
        else:
            trim_offset = float(t_analyze_window[0])

        stim_starts_secs = [x/fs for x in stim_starts]
        stim_starts_scaled = [x+trim_offset for x in stim_starts_secs]
        stim_stops_secs = [x/fs for x in stim_stops]
        stim_stops_scaled = [x+trim_offset for x in stim_stops_secs]
        epsp_starts_scaled = [sample_to_sec(x) for x in epsp_starts]
        epsp_stops_scaled = [sample_to_sec(x) for x in epsp_stops]
        
        #raw_blanked_sig = np.array(y_values)
        
        # =========  APPLY FILTER   ============
        if filter_type == "bandpass":
            print("band pass filter ",lowcut, highcut, "Hz")
            filtered_signal = butter_bandpass_filter(y_values, lowcut, highcut, fs, order=filter_order) # filter is on
        elif filter_type == "highpass":
            print("high pass filter ",lowcut, "Hz")
            filtered_signal = high_pass_filter(y_values, lowcut, fs, order=filter_order)
        elif filter_type == "lowpass":
            print("low pass filter ",lowcut, "Hz")
            filtered_signal = low_pass_filter2(y_values, highcut, fs, order=filter_order)
        elif filter_type == "none":
            print("No filter applied")
            filtered_signal = y_values
        else:
            print("Filter type not entered correctly. Defaulting to #nofilter.")
            filtered_signal = y_values
        
        #Write audio 
        title = file[:-4] + " Trial " + str(trial_number) + " filtered"
        write(title + ".wav", fs, filtered_signal) #write data to a wav file

        for spike_threshold in spike_thresholds: #Create unique Excel worksheet and graphs for each threshold for each trial.
            #Collect dot positions per threshold.
            spike_threshold = spike_threshold #!!!!!!! Is this gonna work?
            #  ========  SPIKE DETECTION & STATS: ===================================
            starts, stops, widths, n_spikes = generate_starts_stops(filtered_signal,spike_threshold)
            spike_IDs, ISIs, spikes_per_stim, av_ISI_per_stim, sd_ISI_per_stim = spike_stats(stim_starts, starts)
            #print("spike_IDs",spike_IDs)
            #print("ISIs",ISIs)
            #  ========  UNIT SCALING, SAMPLES -> SECONDS: ================================= 
            starts_secs = [x/fs for x in starts]
            starts_scaled = [x+trim_offset for x in starts_secs]
            # ==========  WRITE EXCEL          ==========================================
            info = "Threshold "+str(spike_threshold)+", filter "+filter_type+ " "+ str(lowcut) + " " + str(highcut)+ " , trial length (s) "+ str(sample_to_sec(len(y_values)))
            write_worksheet(starts_scaled, stim_starts_scaled, ISIs, spike_IDs, spike_threshold, info)
            
            # ==========  GRAPHING          ==========================================
            
            #Create t-axis values 
            t_values = np.arange(t_startpoint, t_endpoint-1) #x axis units are samples -_____-
            if t_display_units == "milliseconds":
                t_values_graph = (t_values/fs)*1000
            elif t_display_units == "seconds":
                t_values_graph = (t_values/fs)
            else:
                print("Invalid entry for t_display_units. Defaulting to units of seconds.")
                t_values_graph = (t_values/fs)
            
            #==========   FIRST GRAPH WITHOUT ORIGINAL SIG   ===============
            plt.figure(figsize=graph_size)
            title = file[:-4] + " Trial " + str(trial_number)  + " thresh" + str(spike_threshold) + " filt'd.png"
            plt.title(title)
            plt.xlabel(t_display_units)
                #Plot neural data
            try:
                plt.plot(t_values_graph, filtered_signal, linewidth=1) # # filtered signal
                #plt.plot(t_values_graph, raw_unblanked_sig, linewidth=0.5, c="Red") # raw signal
                #plt.plot(t_values_graph, filtered_signal, 'go')
            except:
                plt.plot(t_values_graph, filtered_signal[:-1], linewidth=1)
                #plt.plot(t_values_graph, raw_unblanked_sig[:-1], linewidth=0.5, c="Red")
                #plt.plot(t_values_graph, filtered_signal[:-1], 'go')
            plt.scatter(epsp_starts_scaled, np.full(len(epsp_starts_scaled), 0.02), marker="x", s=120, c="Yellow") #EPSP starts
            plt.scatter(epsp_stops_scaled, np.full(len(epsp_stops_scaled), 0.02), marker="x", s=120, c="Green") #EPSP stops
            plt.scatter(starts_scaled, np.full(len(starts), spike_threshold), marker="D", c="Red") #Plot spike dots
            plt.scatter(stim_starts_scaled, np.full(stim_n_spikes, 0.1), marker="D", c="Orange") #Stim starts
            plt.scatter(stim_stops_scaled, np.full(len(stim_stops_scaled), 0.1), marker="x", c="Orange") #Stim stops
            #plt.yticks(np.arange(min(t_values_graph), max(t_values_graph)+graph_x_interval, graph_x_interval))
            if graph_x_interval != "auto":
                plt.xticks(np.arange(min(filtered_signal), max(filtered_signal)+graph_y_interval, graph_y_interval))
            for xc in stim_starts_scaled:
                plt.axvline(x=xc, c="Yellow")
            plt.tight_layout()
            plt.show
            plt.savefig(title)
            plt.close()
            
            #==========   SECOND GRAPH INCLUDING ORIGINAL SIG   ===============
            plt.figure(figsize=graph_size)
            title = file[:-4] + " Trial " + str(trial_number) + " thresh" + str(spike_threshold) + " orig+filt.png"
            plt.title(title)
            plt.xlabel(t_display_units)
                #Plot neural data
            try:
                plt.plot(t_values_graph, filtered_signal, linewidth=1) # # filtered signal
                plt.plot(t_values_graph, raw_unblanked_sig, linewidth=0.5, c="Red") # raw signal
                #plt.plot(t_values_graph, filtered_signal, 'go')
            except:
                plt.plot(t_values_graph, filtered_signal[:-1], linewidth=1)
                plt.plot(t_values_graph, raw_unblanked_sig[:-1], linewidth=0.5, c="Red")
                #plt.plot(t_values_graph, filtered_signal[:-1], 'go')
            plt.scatter(epsp_starts_scaled, np.full(len(epsp_starts_scaled), 0.02), marker="x", s=120, c="Yellow") #EPSP starts
            plt.scatter(epsp_stops_scaled, np.full(len(epsp_stops_scaled), 0.02), marker="x", s=120, c="Green") #EPSP stops
            plt.scatter(starts_scaled, np.full(len(starts), spike_threshold), marker="D", c="Red") #Plot spike dots
            plt.scatter(stim_starts_scaled, np.full(stim_n_spikes, 0.1), marker="D", c="Orange") #Stim starts
            plt.scatter(stim_stops_scaled, np.full(len(stim_stops_scaled), 0.1), marker="x", c="Orange") #Stim stops
            if graph_x_interval != "auto":
                plt.xticks(np.arange(min(t_values_graph), max(t_values_graph)+graph_x_interval, graph_x_interval))
            for xc in stim_starts_scaled:
                plt.axvline(x=xc, c="Yellow")
            plt.tight_layout()
            plt.show
            plt.savefig(title)
            plt.close()
            
        
    
    # FINISH PROGRAM ================
    workbook.close()
    print("Trial " + str(trial_number) + " written")
    #title_number += 1
    
    end_time = time.time()
    time_elapsed = end_time - master_start_time
    print("Program time elapsed:",time_elapsed," seconds.")
    
    #os.system('say "program finished"')
    print("Program finished running without any problems ¯\_( ͡❛ ͜ʖ ͡❛)_/¯")
    
    #Ask if user wants to change any parameters and run again?
    user_halt = True
    while user_halt == True:
        choice = input("Enter 'Run' to run again with new parameters or 'Stop' to exit program \n")
        if choice == "Run":
            while user_halt == True:
                param = input("Enter a variable name from User Parameters that you want to change, or 'Run' to run. \n")
                print(param)
                if param != "Run":
                    param_value = input(('Enter new value for ',param))
                    if param != "filter_type" and param != "t_analyze_window":
                        vars()[param] = list(param_value)
                    elif param == "graph_x_interval":
                        if param_value == "auto":
                            graph_x_interval = "auto"
                        else:
                            vars()[graph_x_interval] = param_value
                    else:
                        vars()[param] = param_value
                    print(param, "now = ", param_value)
                else:
                    print("Programming running again....")
                    user_halt = False
                    break
                    break
                    break
        elif choice == "Stop":
            print("Program terminating. 𝔾𝕠𝕠𝕕𝕓𝕪𝕖.")
            Run = "No"
            del data_float
            del y_values
            del t_values
            del t_values_graph
            del master_data
            del raw_unblanked_sig
            break
        else:
            print("▄██████████████▄▐█▄▄▄▄█▌")
            print("██████▌▄▌▄▐▐▌███▌▀▀██▀▀")
            print("████▄█▌▄▌▄▐▐▌▀███▄▄█▌")
            print("▄▄▄▄▄██████████████▀")
            print("You did not enter a correct input, please try again...")
            
            
