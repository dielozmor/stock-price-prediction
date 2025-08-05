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

def plot_predictions(Y_true: pd.Series, Y_pred: pd.Series, stock_symbol: str, timestamp: str, save: bool = False, directory: str = "../plots") -> None:
    """Plot actual vs predicted values with optional saving.
    
    Args:
        Y_true (pd.Series): Series of actual values with a datetime index.
        Y_pred (pd.Series): Series of predicted values with the same index as Y_true.
        stock_symbol (str): The stock symbol (e.g., 'TSLA').
        timestamp (str): A timestamp or identifier for the model run.
        save (bool, optional): Whether to save the plot. Defaults to False.
        directory (str, optional): The directory to save the plot in. Defaults to "../plots".
    
    Returns:
        None
    """
    plt.figure(figsize=(10, 5))
    plt.plot(Y_true.index, Y_true, label='Actual', color='blue')
    plt.plot(Y_true.index, Y_pred, label='Predicted', color='red')
    plt.title(f'Actual vs Predicted Prices for {stock_symbol} ({timestamp})')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    if save:
        filename = f"{stock_symbol.lower()}_{timestamp}_predictions"
        save_and_show_plot(filename, directory)
    else:
        plt.show()
        plt.close()

def plot_residuals(y_true: pd.Series, y_pred: pd.Series, title: str, outlier_dates: Optional[List[pd.Timestamp]] = None, save: bool = False, directory: str = "../plots") -> None:
    """Plot residuals over time with optional outlier markers and saving.
    
    Args:
        y_true (pd.Series): Series of actual values with a datetime index.
        y_pred (pd.Series): Series of predicted values with the same index as y_true.
        title (str): The title of the plot.
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
    plt.title(title)
    if outlier_dates:
        plt.legend()
    if save:
        filename = f"{title.lower().replace(' ', '_')}_residuals"
        save_and_show_plot(filename, directory)
    else:
        plt.show()
        plt.close()