

"""
negative_log_likelihood taken from benalexkeen:
        major idea is to use pandas series,
        if use numpy arrays, a different (incorrect result is obtained)
http://benalexkeen.com/bg-nbd-model-for-customer-base-analysis-in-python/
"""

from excelReadWithTransactionTypes import filter_data_from_excel

import numpy as np
from scipy.special import gammaln
from scipy.optimize import minimize

def negative_log_likelihood(params, x, t_x, T):
    """
    Parameters
    ----------
    params: array [r,alpha,a,b]
    x: column (number of purchases) of data frame (from raw or filtered data)
        as pandas series
    t_x: column (value of purchases) as pandas series
    T: pandas series of time period considered (should be input)
    """
    
    
    if np.any(np.asarray(params) <= 0):
        return np.inf

    r, alpha, a, b = params

    ln_A_1 = gammaln(r + x) - gammaln(r) + r * np.log(alpha)
    ln_A_2 = (gammaln(a + b) + gammaln(b + x) - gammaln(b) -
           gammaln(a + b + x))
    ln_A_3 = -(r + x) * np.log(alpha + T)
    
    
    # see boolean array indexing
    # https://stackoverflow.com/questions/36603042/what-does-xx-2-0-mean-in-python
    ln_A_4 = x.copy()
    # this selects only the cells where x > 0 and changes ln_A_4 accordingly
    # note the values for x = 0 are not changed
    ln_A_4[ln_A_4 > 0] = (
        np.log(a) -
        np.log(b + ln_A_4[ln_A_4 > 0] - 1) -
        (r + ln_A_4[ln_A_4 > 0]) * np.log(alpha + t_x[ln_A_4 > 0])
    )
    
    # creates array [0,1,0, ... ] where 0 if x = 0, 1 if x = 1
    # for the x in that position in the array
    delta =  np.where(x>0, 1.0, 0)
    log_likelihood = ln_A_1 + ln_A_2 + np.log(np.exp(ln_A_3) + delta * np.exp(ln_A_4))

    
    # log_likelihood is an array, return sum (-)
    return -log_likelihood.sum()



########################################
######  data fitting  ##################
########################################


# taken from Cam, Davidson, Pilon
# https://github.com/CamDavidsonPilon/lifetimes/blob/master/lifetimes/utils.py

# minimizing_function will be the leastlikelihood function
def fit_data_for_fader_model(num_purchases, time_last_purchase, time_period, params_size,
              iterative_fitting=1, initial_params=None, tol=1e-6, fit_method='Nelder-Mead'):
    """

    Parameters
    ----------
    num_purchases: pandas series of ints
        giving number of purchases (within time frame)
    time_last_puchase: pandas series of floats
        giving time in weeks of last purchase
    time_period: pandas series of floats 
        giving the time period considered
    
    tol: float, optional
        Tolerance for termination of the function minimization process.
    initial_params: array_like, optional
        set the initial parameters for the fitter.
    iterative_fitting: int, optional
        perform iterative_fitting fits over random/warm-started initial params
    fit_method: string, optional
        Fit_method to passing to scipy.optimize.minimize
    maxiter: int, optional
        Max iterations for optimizer in scipy.optimize.minimize        
        
    Returns
    -------
    the optimal parameters for the customer_data_dict input
        as an array [r,alpha,a,b]
    """
    ll = []
    sols = []

    def _func_caller(params, func_args, function):
        # fcn_args are the three arguments x,t_x,T so pass as *args
        return function(params, *func_args)

    if iterative_fitting <= 0:
        raise ValueError("iterative_fitting parameter should be greater than 0 as of lifetimes v0.2.1")

    if iterative_fitting > 1 and initial_params is not None:
        raise ValueError("iterative_fitting and initial_params should not be both set, as no improvement could be made.")


    # extract the 

    total_count = 0

    while total_count < iterative_fitting:
        current_init_params = np.random.normal(1.0, scale=0.05, size=params_size) if initial_params is None else initial_params

        output = minimize(_func_caller, method=fit_method, tol=tol,
                          x0=current_init_params,
                          args=([num_purchases, time_last_purchase, time_period], negative_log_likelihood),
                          options={'maxiter': 2000})

        sols.append(output.x)
        ll.append(output.fun)
        total_count += 1
        
    argmin_ll, min_ll = min(enumerate(ll), key=lambda x: x[1])
    minimizing_params = sols[argmin_ll]
    return minimizing_params, min_ll






# for cdnow data
xl_path = r'path/to/cdnow_data.xlsx'

fader_df = filter_data_from_excel(xl_path, '19971001', start_date = '19970101')

# for simple format id, x, tx, T
#get x, t_x, T from dataframe
x = fader_df['number']
t_x = fader_df['date']
T = fader_df['period']


# scale time
T_max = T.max()
t_x_scaled = t_x/T_max
T_scaled = T/T_max


init_params = np.array([1.0, 1.0, 1.0, 1.0])


optimal_params, opt_val = fit_data_for_fader_model(x,t_x_scaled,T_scaled, 
                                                   4, initial_params=init_params)

# at end dont forget to unscale alpha:
optimal_params[1] = optimal_params[1]*T_max
print(optimal_params)





