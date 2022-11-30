#%%

import numpy as np
import pandas as pd
import yfinance as yf
import warnings
import requests
import riskfolio as rp
import urllib as urllib
from zipfile import ZipFile
import io
from io import StringIO
from io import BytesIO
from openpyxl import load_workbook

#########################################Parameters##########################################
Model='Classic' # Could be Classic (historical), BL (Black Litterman) or FM (Factor Model)
Rm = 'MV' # Risk measure used, this time will be variance
Obj = 'MaxRet' # Objective function, could be MinRisk, MaxRet, Utility or Sharpe
Hist = True # Use historical scenarios for risk measures that depend on scenarios
Rf = 0.04 # Risk free rate
L = 1 # Risk aversion factor, only useful when obj is 'Utility'
Points = 50 # Number of points of the frontier
Start = '2019-10-01'
End = '2019-11-01'


warnings.filterwarnings("ignore")
pd.options.display.float_format = '{:.4%}'.format



# Downloading parameters
def excel_download():
    holdings_url = "https://github.com/ra6it/RiskParity/blob/main/RiskParity_Holdings_Constraints.xlsx?raw=true"
    holdings_url = requests.get(holdings_url).content
    assets = pd.read_excel(holdings_url,'Holdings',usecols="A:B", engine='openpyxl')
    assets = assets.reindex(columns=['Asset', 'Industry'])
    asset_classes = {'Asset': assets['Asset'].values.tolist(), 
                     'Industry': assets['Industry'].values.tolist()}
    asset_classes = pd.DataFrame(asset_classes)
    asset_classes = asset_classes.sort_values(by=['Asset'])
    asset = assets['Asset'].values.tolist()
    asset = [x for x in asset if str(x) != 'nan']
    constraint_url = "https://github.com/ra6it/RiskParity/blob/main/RiskParity_Holdings_Constraints.xlsx?raw=true"
    constraint_url = requests.get(constraint_url).content
    constraints = pd.read_excel(holdings_url,'Constraints',usecols="B:K", engine='openpyxl')
    constraints=pd.DataFrame(constraints)
    print(constraints)
    prices = prices = yf.download(asset, start=Start, end=End)
    return asset_classes, constraints, prices, asset
        
# Downloading data
def data_download(asset_classes):
    print("Downloading data...")
    asset = asset_classes['Asset'].to_string(index=False)
    data = yf.download(asset, start = Start, end = End)
    data = data.loc[:,('Adj Close', slice(None))]
    Y = data.pct_change().dropna()
    return Y
    
# Select method and estimate input parameters:
def method():
    method_mu='hist' # Method to estimate expected returns based on historical data.
    method_cov='hist' # Method to estimate covariance matrix based on historical data.
    return method_mu, method_cov

def portfolio_object(assets,method_mu, method_cov):
    Port = rp.Portfolio(returns=data_download(assets))
    Port.assets_stats(method_mu=method_mu, method_cov=method_cov, d=0.94)
    return Port

def create_pie(w):
    ax = rp.plot_pie(w=w, title='Sharpe Mean Variance', others=0.05, nrow=25, cmap = "tab20",
                 height=6, width=10, ax=None)

def constraints_weightings(constraints,asset_classes):
    asset_classes = pd.DataFrame(asset_classes)
    constraints = pd.DataFrame(constraints)
    data = constraints.fillna("")
    data = data.values.tolist()
    A, B = rp.assets_constraints(constraints, asset_classes)
    return A, B

def ainequality(A,B,Port):
    Port.ainequality = A
    Port.binequality = B
    w = Port.optimization(model=Model, rm=Rm, obj=Obj, rf=Rf, l=L, hist=Hist)
    print("Expected returns for", Start, "-", End,":",Port.mu)
    print("Holdings for", Start, "-", End,":", w.T)
    frontier_create(Port,w)

def frontier_create(Port,w):
    frontier = Port.efficient_frontier(model=Model, rm=Rm, points=Points, rf=Rf, hist=Hist)
    print(frontier.T.head())
    label = 'Max Risk Adjusted Return Portfolio' # Title of point
    mu = Port.mu # Expected returns
    cov = Port.cov # Covariance matrix
    returns = Port.returns # Returns of the assets
    ax = rp.plot_frontier(w_frontier=frontier, mu=mu, cov=cov, returns=returns, rm=Rm,
                      rf=Rf, alpha=0.05, cmap='viridis', w=w, label=label,
                      marker='*', s=16, c='r', height=6, width=10, ax=None)

def runner():
    asset_classes, constraints, prices, asset = excel_download()
    method_mu, method_cov = method()
    Port = portfolio_object(asset_classes,method_mu, method_cov)
    A,B = constraints_weightings(constraints,asset_classes)
    ainequality(A,B,Port)
    returns(prices, asset_classes)

def returns(prices, asset_classes):
    pd.options.display.float_format = '{:.4%}'.format
    data = prices.loc[:, ('Adj Close', slice(None))]
    data.columns = asset_classes
    returner = data.pct_change().dropna()
    print(returner.head())
    rebalance_dates(returner)

def rebalance_dates(returner):
    index = returner.groupby([returner.index.year, returner.index.month]).tail(1).index
    index_2 = returner.index

    # Quarterly Dates
    index = [x for x in index if float(x.month) % 3.0 == 0 ] 

    # Dates where the strategy will be backtested
    index_ = [index_2.get_loc(x) for x in index if index_2.get_loc(x) > 1000]

runner()

asset_classes, constraints, prices, asset = excel_download()




# %%
