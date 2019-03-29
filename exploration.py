import pandas as pd
import requests
import simplejson as json
from datetime import datetime
from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource, NumeralTickFormatter
from bokeh.palettes import Set1

# Set parameters for API calls and plot
ticker = 'AAPL'
start_date = '2015-01-01'
end_date = '2016-01-01'
prices = ['1. open']
price_disp_map = {'1. open': 'Open', '2. high': 'High',
                  '3. low' : 'Low', '4. close': 'Close'}
prices_display = [price_disp_map[x] for x in prices]

# Read in key
f = open('documents/tdi-stock-ticker/key/alphavantage_key.txt')
key = f.read()

# Parameters for API request
stock_params = {'function':'TIME_SERIES_DAILY',
                'symbol': ticker,
                'outputsize': 'full',
                'apikey': key}

# Get data from Quandl API
r = requests.get("https://www.alphavantage.co/query?",
                 params = stock_params)
r.raise_for_status()

# Convert to JSON, then to pandas DataFrame, and make date the index
json_dict = json.loads(r.text)['Time Series (Daily)']

stock_panda = pd.DataFrame.from_dict(json_dict, dtype = 'float').transpose().sort_index()

stock_panda.index = pd.to_datetime(stock_panda.index)
stock_panda['Date'] = stock_panda.index

# Subset into only the time period of interest
start_dt = datetime.strptime(start_date, "%Y-%m-%d")
end_dt = datetime.strptime(end_date, "%Y-%m-%d")

plot_panda = stock_panda.loc[start_dt:end_dt]

plot_panda = plot_panda.loc[:, ['Date'] + prices]

plot_panda = plot_panda.rename(columns = price_disp_map)

# Create Bokeh plot of requested information
output_file('documents/test_figure11.html')

plot_source = ColumnDataSource(plot_panda)

p = figure(x_axis_type = 'datetime',
           x_axis_label = 'Date',
           y_axis_label = 'Price',
           tools='pan, box_zoom, wheel_zoom, reset, save')
for i in range(len(prices_display)):
    p.line(x = 'Date', y = prices_display[i],
           legend = ticker + '-' + prices_display[i],
           color = Set1[9][i],
           source = plot_source)
p.yaxis.formatter = NumeralTickFormatter(format = '$0,0')

show(p)