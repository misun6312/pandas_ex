import pandas as pd
import numpy as np
from datetime import datetime
from pytz import timezone

SINGUP_DATA = 'input/customers_(4).csv'
ORDER_DATA = 'input/orders_(4).csv'

OUT_CSV = 'output/result.csv'
OUT_HTML = 'output/result.html'

# Date window size for order analysis 
window_size = 7

def formatting(x):
    if x is not np.nan: 
        return str(x[0])+' orders (1st time : '+str(x[1])+')'
    else:
        return ''

def main():
	# Data load
	df_sign = pd.read_csv(SINGUP_DATA)
	df_order = pd.read_csv(ORDER_DATA)

	# timezone converting
	date_str = df_sign['created'].loc[0]
	datetime_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
	datetime_obj_utc = datetime_obj.replace(tzinfo=timezone('UTC'))
	datetime_obj_pacific = datetime_obj_utc.astimezone(timezone('US/Pacific'))

	df_sign = df_sign.set_index(pd.DatetimeIndex(df_sign['created']))

	# Get min/max signup date
	dmin = df_sign.created.min().split(' ')[0]
	dmax = df_sign.created.max().split(' ')[0]

	# Make 7days range
	d = pd.date_range(dmin, dmax, freq='7d')

	# Assign Cohort
	for i in xrange(len(d)-1):
		df_sign.loc[d[i].strftime('%Y-%m-%d'):(d[i+1]-pd.Timedelta(days=1)).strftime('%Y-%m-%d'),'cid'] = i
	df_sign.loc[d[-1].strftime('%Y-%m-%d'):dmax,'cid'] = len(d)-1

	# Construct Cohort dataframe
	df_cohort = df_sign[['id','cid']].groupby('cid').agg('count').rename(columns={'id': 'Customers'})
	df_cohort['Cohort'] = d[-1].strftime('%Y-%m-%d')+ ' ~ ' + dmax
	for i in xrange(len(d)-1):
		df_cohort['Cohort'][i] = d[i].strftime('%Y-%m-%d')+ ' ~ ' + (d[i+1]-pd.Timedelta(days=1)).strftime('%Y-%m-%d')

	df_cohort.set_index('Cohort')

	# Analyze order data
	# Count order from distinct customers
	# count first order
	Nuser_list = []
	order_cnt = [] 
	for i in xrange(len(d)):
		if i < (len(d)-1):
			sub_df = df_order[df_order['user_id'].isin(df_sign.loc[d[i].strftime('%Y-%m-%d'):(d[i+1]-pd.Timedelta(days=1)).strftime('%Y-%m-%d')]['id'])]
		else:
			sub_df = df_order[df_order['user_id'].isin(df_sign.loc[d[-1].strftime('%Y-%m-%d'):dmax]['id'])]
		uids = sub_df['user_id'].drop_duplicates(['user_id']).values
		Nuser_list.append(len(uids))
		dorder_di = {}
		for uid in uids:
			orders = (pd.to_datetime(df_order.loc[df_order['user_id'] == uid]['created']) - pd.to_datetime(df_sign.loc[df_sign['id']==uid]['created'].values[0])).astype('timedelta64[D]').values.astype(int)
			order_group = orders/window_size
			uniq = np.unique(order_group)
			for uq in uniq:
				if uq not in dorder_di:
					dorder_di[uq] = [1, 0]
				else:
					dorder_di[uq][0] += 1		
			first_order_grp = min(orders)/window_size
			if first_order_grp in dorder_di:
				dorder_di[first_order_grp][1] += 1
		order_cnt.append(dorder_di)
		
	dsize = max([max(a.keys()) for a in order_cnt])+1
	cols = []
	for i in range(dsize):
		cols.append(str(i*window_size)+'-'+str((i+1)*window_size-1)+' days')

	# OUTPUT Files formatting
	df_cohort[cols] = pd.DataFrame(order_cnt)
	df_cohort.to_csv(OUT_CSV)

	for c in cols:
	    df_cohort[c] = df_cohort[c].apply(formatting)

	df_cohort.to_html(OUT_HTML)

	print df_cohort

if __name__ == '__main__':
    main()