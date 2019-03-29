import pandas as pd
import requests
import simplejson as json
from datetime import datetime
from flask import Flask, render_template, request, redirect
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, NumeralTickFormatter
from bokeh.palettes import Set1
from bokeh.embed import components

app = Flask(__name__)

app.vars= {}

f = open('key/alphavantage_key.txt')
key = f.read()

# Dict to map API price labels with prettier ones for display
price_disp_map = {'1. open': 'Open', '2. high': 'High',
                  '3. low' : 'Low', '4. close': 'Close'}

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        app.vars['ticker'] = request.form['ticker']
        app.vars['start_date'] = request.form['start_date']
        app.vars['end_date'] = request.form['end_date']
        app.vars['prices'] = request.form.getlist('prices')
        
        return redirect('/plot')


@app.route('/error')
def error():
    if len(app.vars['prices']) == 0:
        return render_template('no_prices.html')
    if app.vars['end_date'] < app.vars['start_date']:
        return render_template('invalid_dates.html')
    
    
@app.route('/plot')
def about():
    # Do some error checking here - no check boxes, start after end
    # Maybe add check for end date after current date
    if (len(app.vars['prices']) == 0) or \
      app.vars['end_date'] < app.vars['start_date']:
        return redirect('/error')
    else:
        
        # Housekeeping for display of prices
        prices_display = [price_disp_map[x] for x in app.vars['prices']]
        
        # Parameters for API request
        stock_params = {'function':'TIME_SERIES_DAILY',
                        'symbol': app.vars['ticker'],
                        'outputsize': 'full',
                        'apikey': key}
        
        # Get data from Quandl API
        r = requests.get("https://www.alphavantage.co/query?",
                         params = stock_params)
        
        # Return error if API call is unsuccessful
        if r.status_code != 200:
            return render_template('api_error.html', 
                                   error_code = r.status_code)
        
        # Convert to JSON, then to pandas DataFrame, and make date the index
        json_dict = json.loads(r.text)['Time Series (Daily)']

        stock_panda = pd.DataFrame.from_dict(json_dict, dtype = 'float').transpose().sort_index()
        
        stock_panda.index = pd.to_datetime(stock_panda.index)
        stock_panda['Date'] = stock_panda.index

        # Subset into only the time period of interest
        start_dt = datetime.strptime(app.vars['start_date'], "%Y-%m-%d")
        end_dt = datetime.strptime(app.vars['end_date'], "%Y-%m-%d")
        
        plot_panda = stock_panda.loc[start_dt : end_dt]
        
        plot_panda = plot_panda.loc[:, ['Date'] + app.vars['prices']]
        
        plot_panda = plot_panda.rename(columns = price_disp_map)
        
        # Create plot     
        plot_source = ColumnDataSource(plot_panda)
        
        p = figure(x_axis_type = 'datetime',
                   x_axis_label = 'Date',
                   y_axis_label = 'Price',
                   tools='pan, box_zoom, wheel_zoom, reset, save')
        
        for i in range(len(prices_display)):
            p.line(x = 'Date', y = prices_display[i],
                   legend = app.vars['ticker'] + '-' + prices_display[i],
                   color = Set1[9][i],
                   source = plot_source)
            
        p.title.text = 'AlphaVantage Stock Prices - ' + app.vars['ticker']
        p.yaxis.formatter = NumeralTickFormatter(format = '$0,0')
        
        # Split bokeh plot into components for html and make iterable
        script, div = components(p)
        
        plots = [(script, div)]
        
        return render_template('dashboard.html', 
                               tick_sym = app.vars['ticker'],
                               start_date = app.vars['start_date'],
                               end_date = app.vars['end_date'],
                               plots = plots)
        

if __name__ == '__main__':
  app.run(port=33507)