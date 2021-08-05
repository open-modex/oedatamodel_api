import requests
import pandas as pd
import json

url = 'http://0.0.0.0:8000/scenario/id/39?source=modex&mapping=IAMC_aggregated_series'

resp = requests.get(url=url)
data = resp.json()
# print(data['IAMC_timeseries'])

df = pd.read_json(json.dumps(data['IAMC_timeseries']))
print(df.head())

# process_df = df.pivot_table(index=['variable', 'scenario', 'region', 'unit', 'year'], columns=['year'], values='series', fill_value=0)
process_df = df.pivot_table(index=['year'], columns=['variable'], values='series', fill_value=0)
print(process_df.head())

final_json = process_df.to_json(orient='columns')
print(final_json)

# process_df.to_csv('test.csv')