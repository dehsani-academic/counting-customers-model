


import pandas as pd
import numpy as np
from datetime import datetime





def _excel_read(xl_path):
    """
    we expect the excel file to look like the raw data
    from Fader et al., but with an extra type column:
        (person, type(s), number, value, date) 
    
    Returns
    -------
    a DataFrame object representing the excel file
    zeros are placed in cells with no data
    
    """

    df = pd.read_excel(xl_path)
    df[np.isnan(df)] = 0
    
    # do not want to set index as ids because
    # there will be multiple entries for each id
    # df = df.set_index('ids')
    
    df['ids']= df['ids'].astype(int)
    df['number']= df['number'].astype(int)
    
    # drop the rows which have 0 as the id
    df = df.drop(df.loc[df['ids'] == 0].index)
    
    # date should be a datetime object
    df['date']= pd.to_datetime(df['date'], format = '%Y%m%d')
    
    # reset index to start at 0 (helps for filtering)
    df = df.reset_index()
    df = df.drop('index', axis=1)
        
    return df


def _filter_data_by_type(df_data, transaction_types = ['all']):
    """
    Parameters
    ----------
    takes in data frame of the purchase data
    option: transaction_types is an array,
        can specify which types of 
        transactions are to be considered
    
    Returns
    -------
    a DataFrame object representing the 
    transactions of desired type
    df = id, x, value, t_x (as datetime)
    
    """
    for i in range(len(transaction_types)):
        if transaction_types[i] == 'all':
            return df_data
    
    index_to_keep = pd.Int64Index([])
    
    for i in range(len(transaction_types)):
        a_type = transaction_types[i]
        index_to_keep = index_to_keep.append(df_data.loc[df_data[a_type] != 0].index)
    
    index_list = index_to_keep.tolist()
    df_data = df_data.take(index_list)
    return df_data


def _filter_data_by_date(df_data, cutoff_date, start_date = '19000101'):
    """
    Parameters
    ----------
    takes in data frame of the purchase data
    start/cutoff_date: date in string %Y%m%d format
    
    will group all purchases from single id together (within time period)
    
    Returns
    -------
    a DataFrame object representing the 
    transactions of desired type
    df = id, x, value, t_x, T
        where T is time period (in weeks) based on time period considered
    
    """
    
    start_date = datetime.strptime(start_date,'%Y%m%d')
    cutoff_date = datetime.strptime(cutoff_date,'%Y%m%d')
    T_dt = cutoff_date - start_date
    T_days = T_dt.days
    T_weeks = T_days/7

    # create a mask to select the proper indices
    mask = (df_data['date'] >= start_date) & (df_data['date'] <= cutoff_date)
    df_data = df_data.loc[mask]
    
    # use agg to get data in one row for one customer:
    agg_fcns = {'number': 'sum', 'value': 'sum', 'date': 'max'}
    df = df_data.groupby('ids').agg(agg_fcns)
    
    # use map to convert date into t_x = last time in weeks
    df['date'] = df['date'].map(lambda x: (x-start_date).days/7)
    
    df['period'] = T_weeks
    
    return df




def filter_data_from_excel(xl_path, cutoff_date, 
                           transaction_types = ['all'], 
                           start_date = '19000101',
                           customer_ids = ['all']):
    """
    takes excel file from xl_path
    
    Returns
    -------
    DataFrame object that contains the info for a Fader model:
        cust_id, number of purchases, (value), last time purchase, period
    
    Note: there is one extra column giving the value of the purchases
        which can be used to find expected values
    """

    df_raw = _excel_read(xl_path)
    if not ('all' in customer_ids):
        df_raw = df_raw.loc[df_raw['ids'].isin(customer_ids)]
        
    # now filter by type
    type_df = _filter_data_by_type(df_raw,transaction_types)
    #now filter by date
    date_type_df = _filter_data_by_date(type_df, cutoff_date, start_date)
    
    return date_type_df




