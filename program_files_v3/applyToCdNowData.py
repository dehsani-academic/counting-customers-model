
from excelReadWithTransactionTypes import filter_data_from_excel
from fitData import fit_data_for_fader_model
from expectations import get_expected_num_trans

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta



def run_sample(xl_path, start_date, cutoff_date, future_time, num_tests, sample_size):
    """
    this will test the number of expected transactions in next period
    wrt the number of transactions within start/cutoff dates
    
    will compare to actual number of cdnow data
    
    Parameters
    ----------
    t: (float) future time in weeks
    """
    
    # setup num_tests number of plots
    fig, axes = plt.subplots(num_tests)
    # run through n_tests
    for cur_test in range(num_tests):
        print(cur_test)
    
        df_fader = filter_data_from_excel(xl_path, cutoff_date, start_date=start_date)
        all_ids = df_fader['ids']
            
        # get sample_size indices for sample size
        sample_ids = np.random.choice(all_ids, size=sample_size, replace=False)
        
        # for the sample ids get params
        df_sample = filter_data_from_excel(xl_path, cutoff_date,
                                           start_date=start_date, customer_ids=sample_ids)    
        x = df_sample['number']
        t_x = df_sample['date']
        T = df_sample['period']
        params = fit_data_for_fader_model(x, t_x, T, 4)[0]
        
        num_trans_array = np.asarray([1,2,3,4,5,6])
        expected_trans = np.array([])
        actual_trans = np.array([])
        # for these params get expected number in future_time for each number of transactions
        for num_trans in num_trans_array:
            expected_trans = np.append(expected_trans,
                                       get_expected_num_trans(future_time, params, num_trans, df_sample))
           
            df_sample_trans = df_sample.loc[df_sample['number'] == num_trans]
            # now get actual number of transactions
            new_start = cutoff_date
            new_start_dt = datetime.strptime(new_start,'%Y%m%d')
            new_cutoff_dt = new_start_dt + timedelta(days = future_time*7)
            new_cutoff = new_cutoff_dt.strftime('%Y%m%d')
            
            df_actual_future = filter_data_from_excel(xl_path, new_cutoff, 
                                                      start_date=new_start, customer_ids=sample_ids)
            # correct this! might be none, if so, set to zero!
            df_actual_future_prev_trans = df_actual_future.loc[df_actual_future['ids'].isin(df_sample_trans['ids'])]
            actual_num_trans = df_actual_future_prev_trans['number'].mean()
            
            actual_trans = np.append(actual_trans, actual_num_trans)
            
        
        # now plot 
        axes[cur_test].plot(num_trans_array, expected_trans, 'b', label = 'expected trans')
        axes[cur_test].plot(num_trans_array, actual_trans, 'r', label = 'actual trans')
    
        axes[cur_test].legend(loc='best')  
    
        
    
    
    
    
xl_path = r'path/to/cdnow_data.xlsx'
run_sample(xl_path, '19970101', '19971001', 39, 5 , 100)
