import matplotlib.pyplot as plt
import os
import pandas as pd
from typing import Optional, List

def save_and_show_plot(filename: str, directory: str = "../plots") -> None:
    """Save and display a plot, then close it.
    
    Args:
        filename (str): The name of the file to save the plot as.
        directory (str, optional): The directory to save the plot in. Defaults to "../plots".
    
    Returns:
        None
    """
    os.makedirs(directory, exist_ok=True)
    plt.savefig(f"{directory}/{filename}.png")
    plt.show()
    plt.close()

def plot_time_series(df: pd.DataFrame, stock_symbol: str, fetch_id: str, column_name: str, save: bool = False, directory: str = "../plots") -> None:
    """Plot a time series for a specified column.
    
    Args:
        df (pd.DataFrame): Stock data DataFrame.
        stock_symbol (str): Stock symbol for plot titles.
        fetch_id (str): Unique identifier for the data fetch.
        column_name (str): The column to plot (e.g., 'close', 'volume').
        save (bool, optional): Whether to save the plot. Defaults to False.
        directory (str, optional): The directory to save the plot in. Defaults to "../plots".
    
    Returns:
        None
    
    Raises:
        ValueError: If the specified column is not in the DataFrame.
    """
    if column_name not in df:
        raise ValueError(f"Column '{column_name}' not found in DataFrame.")
    
    plt.figure(figsize=(12, 5))
    df[column_name].plot(title=f"{stock_symbol} {column_name.capitalize()}")
    plt.xlabel("Date")
    plt.ylabel(column_name.capitalize())
    plt.grid(True)
    
    if save:
        filename = f"{stock_symbol.lower()}_{fetch_id}_{column_name.lower()}"
        save_and_show_plot(filename, directory)
    else:
        plt.show()
        plt.close()

def plot_predictions(Y_true: pd.Series, Y_pred: pd.Series, stock_symbol: str, timestamp: str, variant: str, save: bool = False, directory: str = "../plots") -> None:
    """Plot actual vs predicted values with optional saving.
    
    Args:
        Y_true (pd.Series): Series of actual values with a datetime index.
        Y_pred (pd.Series): Series of predicted values with the same index as Y_true.
        stock_symbol (str): The stock symbol (e.g., 'TSLA').
        timestamp (str): A timestamp or identifier for the model run (e.g., '20250730_102338').
        variant (str): The model variant (e.g., 'with_outliers', 'without_outliers').
        save (bool, optional): Whether to save the plot. Defaults to False.
        directory (str, optional): The directory to save the plot in. Defaults to "../plots".
    
    Returns:
        None
    """
    plt.figure(figsize=(10, 5))
    plt.plot(Y_true.index, Y_true, label='Actual', color='blue')
    plt.plot(Y_true.index, Y_pred, label='Predicted', color='red')
    plt.title(f'Actual vs Predicted Prices for {stock_symbol} ({variant})')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    if save:
        filename = f"{stock_symbol.lower()}_model_{timestamp}_{variant}_predictions"
        save_and_show_plot(filename, directory)
    else:
        plt.show()
        plt.close()

def plot_residuals(y_true: pd.Series, y_pred: pd.Series, stock_symbol: str, timestamp: str, variant: str, outlier_dates: Optional[List[pd.Timestamp]] = None, save: bool = False, directory: str = "../plots") -> None:
    """Plot residuals over time with optional outlier markers and saving.
    
    Args:
        y_true (pd.Series): Series of actual values with a datetime index.
        y_pred (pd.Series): Series of predicted values with the same index as y_true.
        stock_symbol (str): The stock symbol (e.g., 'TSLA').
        timestamp (str): A timestamp or identifier for the model run (e.g., '20250730_102338').
        variant (str): The model variant (e.g., 'with_outliers', 'without_outliers').
        outlier_dates (Optional[List[pd.Timestamp]], optional): List of dates to mark as outliers. Defaults to None.
        save (bool, optional): Whether to save the plot. Defaults to False.
        directory (str, optional): The directory to save the plot in. Defaults to "../plots".
    
    Returns:
        None
    """
    residuals = y_true - y_pred
    plt.figure(figsize=(10, 5))
    plt.scatter(y_true.index, residuals, color='purple')
    if outlier_dates:
        for date in outlier_dates:
            plt.axvline(date, color='red', label='Outlier Day')
    plt.axhline(0, color='black', linestyle='--')
    plt.xlabel('Date')
    plt.ylabel('Residuals (Actual - Predicted)')
    plt.title(f'Residuals for {stock_symbol} ({variant})')
    if outlier_dates:
        plt.legend()
    if save:
        filename = f"{stock_symbol.lower()}_model_{timestamp}_{variant}_residuals"
        save_and_show_plot(filename, directory)
    else:
        plt.show()
        plt.close()