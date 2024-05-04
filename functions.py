from langchain.pydantic_v1 import BaseModel, Field
import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta
from langchain.tools import tool
import streamlit as st
import plotly.graph_objects as go
from langchain_core.utils.function_calling import convert_to_openai_function
import ast
import os
import uuid

class gethistoricalprice(BaseModel):
    symbol: str = Field(description="The stock symbol/symbols to get the historical price for. Can be a single stock symbol or multiple stock symbols separated by a comma. Example: AAPL,MSFT")
    days: str = Field(description="The number of days to get the historical price for.")

@tool("historicalprice-tool", args_schema=gethistoricalprice)
def get_historical_price(symbol: str, days: str) -> str:
    """
    Returns the price information of stock/stocks and corresponding timestamps for the last n days.
    """
    end_date = datetime.now()
    start_date = end_date - relativedelta(days=int(days))  # Convert days to an integer
    data = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    data = data.dropna()
    close_prices = data['Close'].astype(int).to_dict()
    return str(close_prices)

class plotlinechart(BaseModel):
    x_values: str = Field(description="The x values represented as a string. Example format: ['2024-04-02', '2024-04-03', '2024-04-04', '2024-04-05']")
    y_values: str = Field(description="The y values represented as a string. Example format: [166, 168, 171, 164]")
    symbol: str = Field(description="The stock symbol to plot the line chart for.")
    

@tool("line-chart-tool", args_schema=plotlinechart)
def plot_line_chart(x_values: str, y_values: str, symbol: str) -> str:
    """
    Plots a line chart to screen and also saves it under images\ folder using the x and y values provided.
    Supports only one stock symbol at a time.
    """
    print(x_values) #['2024-04-08', '2024-04-09', '2024-04-10', '2024-04-11']
    print(y_values) #[168, 169, 167, 175]
    print(symbol)
    x_values = ast.literal_eval(x_values)
    y_values = ast.literal_eval(y_values)
    # Check if the strings start with a single quote and replace with double quotes if they do

    # Create a line chart using Plotly
    fig = go.Figure(data=go.Scatter(x=x_values, y=y_values, mode='lines'))

    xaxis_title = "Date"
    yaxis_title = "Price of " + symbol 

    # Set the descriptions for the x and y axes
    fig.update_layout(xaxis_title=xaxis_title, yaxis_title=yaxis_title)

    st.plotly_chart(fig)

    if not os.path.exists('images'):
            os.makedirs('images')

        #generate a random file name
    filename = f"images/fig_{uuid.uuid4().hex}.png"
    
    fig.write_image(filename)
    return f"Line chart has been plotted to screen and saved successfully to {filename}"

def get_functions_dict():
    return {
        "historicalprice-tool": get_historical_price,
        "line-chart-tool": plot_line_chart
    }

def get_openai_functions_definitions():
    tools = [get_historical_price, plot_line_chart]
    functions = [convert_to_openai_function(t) for t in tools]

    return functions