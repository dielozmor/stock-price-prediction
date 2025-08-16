**Date**: August 15, 2025

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
- **Date Range**: 2024-06-17 to 2025-06-16
- **Missing Values**: 0
- **Anomalies**: 1


    
    



#### **Anomalies**


             date  column           value
    1  2025-06-05  volume  292,818,655.00
    
    



#### **Statistics**


             open    high     low   close       volume
    count     250     250     250     250          250
    mean   290.45  297.72  282.84  290.46  100,814,958
    std     72.62   74.00   70.21   71.99   39,521,561
    min    177.92  183.95  177.00  181.57   37,167,621
    25%    230.44  237.30  225.10  231.46   71,340,436
    50%    263.05  274.11  257.10  265.41   93,858,026
    75%    345.07  351.22  335.92  344.16  120,581,185
    max    475.90  488.54  457.51  479.86  292,818,655


<style>
:root {
    --jp-rendermime-error-background: white;
}
</style>
