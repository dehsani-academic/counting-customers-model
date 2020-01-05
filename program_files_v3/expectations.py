
from excelReadWithTransactionTypes import _excel_read, filter_data_from_excel
from fitData import fit_data_for_fader_model

import numpy as np
from scipy.special import hyp2f1

#from fitData import fitDataForFaderModel, getSampleData
#from excelExtraction import _excel_read


# for expected values see 
# Fader, et. al. formula (10)
# in its place other models can be used (with different parameters)
    
def get_expected_customer_purchases_from_fader_model(t, params, x, t_x, T):
    """
    returns the mean number of expected transactions 
    of particular customers 
    in a length of time, t, in the future
    
    r, alpha, a, b are the parameters calculated according to
    all customer data related to selected transaction types
    
    x, t_x, T will be pandas Series
    
    Note: uses the gaussian hypergeometric function
        from scipy: hyp2f1(a, b, c, z)	Gauss hypergeometric function 2F1(a, b; c; z)
    """
    
    r, alpha, a, b = params
    
    # define the step function
    delta = np.where(x>0, 1, 0)
    
    mult_factor = (a+b+x-1)/(a-1) 
    
    numerator= (1 -
                ( ((alpha + T)/(alpha + T + t))**(r+x) )*
                hyp2f1(r+x, b+x, a+b+x-1, t/(alpha+T+t))
                )
    
    denominator = 1 + delta * ( (a/(b+x-1) )* 
                               ((alpha + T)/(alpha + t_x))**(r+x)
                               ) 
    
    expected_value = mult_factor * numerator/denominator
    
    return expected_value.mean()


def get_expected_num_trans(t, params, number_trans, cust_df):
    
    
    # first build a df of people with same number of trans
    df_trans = cust_df.loc[cust_df['x'] == number_trans]
    x = df_trans['x']
    t_x = df_trans['t_x']
    T = df_trans['T']
    
    # now pass the DataFrame to get_expected_customer_purchases_from_fader_model
    # the mean will be returned
    average_expected_trans = get_expected_customer_purchases_from_fader_model(t, params, x, t_x, T)
    
    return average_expected_trans



def get_expected_trans_val(xl_path, customer_ids, future_time, cutoff_date, start_date = '19000101'):
    """
    this method assumes data for each transaction:
        number of units purchased, total value of purchase, date (not used)
    
    Parameters
    ----------
    df_raw: the raw data frame produced by reading excel file into
        _excel_read(xl_path) method.  listed are all transactions
    
    customer_ids: an array of ints which are the customer_ids
        for which a total expected transaction number and value is desired
        if cust_ids = ['all'] then use all the data
        
    future time: the number of weeks into the future being prognosed
    
    start/cutoff_date: in format '%Y%m%d'
        
    Returns
    -------
    int num_trans, int val_trans: 
        a tuple representing the number of transactions and
        the value of the transactions expected from the customers
    
    """
    
    df_raw = _excel_read(xl_path)
    df_cust_data = df_raw.loc[df_raw['ids'].isin(customer_ids)]

    # get paramters for the data 
    # if group is large just get params for the group, else for entire
    
    if len(customer_ids) < 100 or not('all' in customer_ids):
        # filter dataframe to get x, t_x, T based on cutoff/start dates
        df_fader = filter_data_from_excel(xl_path, cutoff_date, start_date=start_date)
    else:
        df_fader = filter_data_from_excel(xl_path, cutoff_date, 
                                          start_date=start_date, customer_ids=customer_ids)
    x = df_fader['number']
    t_x = df_fader['date']
    T = df_fader['period']
    
    # dont forget to scale with T.max
    T_max = T.max()
    t_x_scaled = t_x/T_max
    T_scaled = T/T_max
    
    params = fit_data_for_fader_model(x, t_x_scaled, T_scaled, 4)[0]
    # at end dont forget to unscale alpha:
    params[1] = params[1]*T_max
    
    # feed into get_expected_num_trans method
    expected_num = get_expected_customer_purchases_from_fader_model(future_time, params, x, t_x, T)
    
    ################## for expected value ###################
    # filter the dataframe object to include only the desired customers

    
    # now filter the dates
    mask = (df_cust_data['date'] >= start_date) & (df_cust_data['date'] <= cutoff_date)
    df_cust_data = df_cust_data.loc[mask]

    # get the (pandas Series) value of transactions
    val_purchases = df_cust_data['value']
    # throw out outliers from (Series val_purchases)
    filtered_val_purchases = val_purchases[(val_purchases - val_purchases.mean() ).abs() <
                                           2*val_purchases.std()]
    
    # get the (pandas Series) number of transactions
    num_purchases = df_cust_data['number']
    # throw out outliers from (Series val_purchases)
    filtered_num_purchases = num_purchases[(val_purchases - val_purchases.mean() ).abs() <
                                           2*val_purchases.std()]
    
    expected_single_val = (filtered_val_purchases/filtered_num_purchases).mean()
    expected_val = expected_single_val * expected_num
    
    
    return expected_num, expected_val





xl_path = r'path/to/cdnow_data.xlsx'

# expectations for cust 1:
num, val = get_expected_trans_val(xl_path, [2,3], 39, '19971001', start_date='19970101')
print(num,val)











