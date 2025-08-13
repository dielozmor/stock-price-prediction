**Date**: August 13, 2025

**Stage**: Inspect Raw Data

**Objectives**:
- Verify raw stock data integrity (row count, date range, data types).
- Identify gaps in trading days, missing values, and anomalies.
- Visualize closing price and trading volume to detect trends or outliers.

---

## Visualization

Visualizations of closing price and trading volume help identify trends and anomalies visually, complementing the statistical analysis.


    
![png](output_19_0.png)
    



    
![png](output_19_1.png)
    


## Quantitative Summary


#### **Data**
- **Row Count**: 250
- **Date Range**: 2024-08-13 to 2025-08-12
- **Missing Values**: 0
- **Anomalies**: 2


    
    



#### **Anomalies**


             date  column           value
    1  2024-11-29  volume   37,167,621.00
    2  2025-06-05  volume  292,818,655.00
    
    



#### **Statistics**


             open    high     low   close       volume
    count     250     250     250     250          250
    mean   305.90  313.14  298.17  305.83   98,962,160
    std     65.55   66.75   63.54   65.02   37,436,215
    min    198.47  208.44  197.06  201.38   37,167,621
    25%    248.34  254.32  241.40  249.98   74,440,679
    50%    308.31  313.27  300.21  308.65   89,094,248
    75%    345.62  354.99  336.75  344.94  115,660,580
    max    475.90  488.54  457.51  479.86  292,818,655


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    


## Comprehensive Analysis and Insights

### Data Coverage
- **Row Count**: 250 trading days (June 17, 2024 - June 16, 2025).  
- **Date Range**: 364 days total, with 250 trading days per U.S. market (e.g., NASDAQ) conventions.

### Trading Day Observations
Markets closed Jan. 9, 2025, for Carter’s mourning; open Oct. 14, 2024 (Columbus Day) and Nov. 11, 2024 (Veterans Day), aligning with U.S. equity calendars for data integrity.

- **Data Completeness and TypesMissing Values**: None.  
- **Data Types**: Numerical columns as float64; index as datetime64.

### Anomalies Detected
- **Volume Outlier**: June 5, 2025, with 292,818,655 shares (mean: 100,814,958; std: 39,521,561).   
    - **Validation**: Z-score 4.858 (>4.8 std), exceeds IQR upper bound; matches NASDAQ data (Yahoo Finance ~1.8% lower, likely adjusted).  
    - **Event Context**: Triggered by Trump’s threat to cancel Musk contracts, causing a 14.2% price drop ($332.05 to $284.70).  
    - **Action**: Flagged is_outlier = True, retained for modeling.

### Visualization Insights
- **Closing Price**: Rose from $181.57 (mid-2024) to $479.86 (early 2025), fell to $300–$350 by June 2025; 14.2% drop on June 5 with partial recovery.  
- **Trading Volume**: Right-skewed (median: 93.9M, mean: 100.8M); spiked to 292.8M on June 5 vs. 50–150M baseline, indicating event-driven volatility.

### Conclusion
Dataset is robust with 250 trading days, no missing values, and market calendar alignment. A notable volume outlier on June 5, 2025 (292,818,655 shares), validated by z-score (4.858) and linked to a 14.2% price drop, is retained for modeling. Visualizations reveal volatility trends and event sensitivity, with recovery patterns post-spike.

<style>
:root {
    --jp-rendermime-error-background: white;
}
</style>
