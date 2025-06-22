# Data Inspection for TSLA Stock Data
**Project**: Stock Price Trend Prediction<br>
**Phase 3, Step 3.1**: Inspect raw data from `data/raw_tsla_data.csv`. Verify row count, date range, gaps, missing values, and anomalies.<br>
**Date**: June 17, 2025<br>
**Authors**: Diego Lozano, Sebastian Lozano

## Objective
- Confirm 249 rows vs. trading days (June 17, 2024 to june 16, 2025), any difference likely due to holidays (e.g., July 4, 2024) or API gaps.
- Verify date range: June 17, 2024 to June 16, 2025.
- Identify gaps in trading days.
- Check for missing values (NaNs) and anomalies (e.g., negative prices/volumes).
- Visualize closing price and volume to detect trends/outliers.

## Setup
Import libraries and load `data/raw_tsla_data.csv` using `stock_symbol` from `data/config.json`, matching `fetch_data.py` dynamic naming.


```python

```


    
![png](output_21_0.png)
    



    
![png](output_21_1.png)
    


## Summary of findings
- **Row Count**: The DataFrame contains 250 trading days from June 17, 2024, to June 16, 2025, representing approximately one year of market activity. This aligns with the typical number of trading days (around 252) in a year, adjusted for holidays and closures.

- **Date Range**: The DataFrame’s index spans from June 17, 2024, to June 16, 2025, covering a total of 364 days, including weekends and non-trading days. The 250 trading days reflect the exclusion of weekends and specific holidays, consistent with U.S. stock market conventions (e.g., NASDAQ). This range provides a comprehensive dataset for analyzing Tesla’s price and volume trends over the period.

- **Date Gaps**: The index correctly excludes two non-trading holidays: January 9, 2025 (National Day of Mourning for former President James Earl Carter, Jr., following his passing on December 29, 2024) and April 18, 2025 (Good Friday, a traditional market closure). It appropriately includes October 14, 2024 (Columbus Day) and November 11, 2024 (Veterans Day), which are trading days for equity markets like NASDAQ, though bond markets may close. These inclusions and exclusions validate the dataset’s adherence to market-specific trading calendars, ensuring data integrity for modeling.

- **Missing Values**: No missing values were detected across all columns (open, high, low, close, volume, mo5), ensuring a complete dataset for analysis and prediction.

- **Data Types**: All numerical columns (open, high, low, close, volume, mo5) are stored as float64, providing sufficient precision for financial data. The index is of type datetime64, enabling time-series operations and accurate date-based slicing (e.g., 2025-06-05).

- **Anomalies**: A significant outlier was identified in the volume column on June 5, 2025, with a value of 292,818,655 for TSLA (mean: 100,814,958, std: 39,521,561). This outlier was validated with:

    - **Z-Score**: 4.858, indicating it is over 4.8 standard deviations above the mean (100,814,958.224), confirming its extremity.

    - **IQR**: Exceeds the upper bound (Q3 + 1.5 * IQR), consistent with initial outlier detection.

    - **Data Validation**: Matches NASDAQ’s reported volume, while Yahoo Finance reported 287,499,800 (~1.8% lower), likely due to an adjustment or error. The NASDAQ alignment prioritizes the dataset’s value.

    - **Event Context**: Driven by a major event—U.S. President Donald Trump’s threat to pull government contracts from Elon Musk's companies, and Tesla being one of his companies caused a high-volume sell-off and a ~14.2% price drop (close: 332.05 to 284.70).

    - **Action Taken**: Flagged with a boolean column `is_outlier` (True for June 5, 2025) and retained for modeling to reflect real market dynamics.

- **Visualization**:

    - **Closing Price Trend**: The closing price trend shows a rise from $181.57 (min) in mid-2024 to a peak of $479.86 (max) in early 2025, followed by a decline to ~$300–$350 by June 2025. A sharp drop (14.2%) occurred on June 5, 2025, aligning with the volume spike, followed by partial recovery or stabilization toward June 13, 2025. This suggests event-driven volatility and potential mean-reversion patterns.

    - **Volume Trend**: The trading volume distribution is right-skewed, with a median of approximately 93.9 million shares and a mean of approximately 100.8 million shares. This suggests that while most trading days have volumes around 93.9 million, occasional days with significantly higher volumes pull the average upward.

    - **Volume Spike**: A drastic increase to ~2.9 billion on June 5, 2025, stands out against a baseline of 0.5–1.5 billion, with other minor spikes (e.g., mid-2024, early 2025). This indicates Tesla’s stock is highly sensitive to news, with June 5 as the most extreme outlier.

    - **Additional Patterns**: Periodic volume spikes and price fluctuations suggest seasonal or event-driven trends (e.g., earnings, product news), warranting further investigation of other peak dates.


**Conclusion**: 
The analysis confirms a robust dataset with 250 trading days from June 17, 2024, to June 16, 2025, with no missing values and adherence to market trading calendars. The primary anomaly, a volume outlier of 292,818,655 on June 5, 2025, is validated by a z-score of 4.858 and IQR, supported by NASDAQ data, and linked to a significant event (Trump’s threat to Tesla contracts), which triggered a ~14.2% price drop. Visualizations reveal event-driven volatility, a price peak-to-decline trend, and potential recovery patterns, with other volume spikes suggesting additional event sensitivity. The outlier is flagged as is_outlier and retained for modeling to capture real market behavior. Future steps include testing the model’s sensitivity to the outlier, exploring lagged effects, and investigating other high-volume dates for enhanced predictive accuracy.
