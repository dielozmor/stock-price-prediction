**Date**: August 15, 2025

**Stage**: Model Performance Analysis

**Objectives**:
- Visualize predictions and residuals to assess model accuracy.
- Evaluate linear regression model performance (with/without outliers) using RMSE, MAE, and R².
- Analyze the impact of outliers on model performance.

---

## Visualization

Prediction vs. actual plots compare predicted and actual values, showing alignment with occasional deviations during volatile periods. Residual plots illustrate prediction error distribution, highlighting potential over- or underprediction, especially during market shifts. These visualizations are available for review.


    
![png](output_13_0.png)
    



    
![png](output_13_1.png)
    



    
![png](output_13_2.png)
    



    
![png](output_13_3.png)
    


<br>

## Model performance and outliers impact


- **Model with Outliers**:
  - RMSE: 19.30
  - MAE: 14.16
  - R²: 0.77


- **Model without Outliers**:
  - RMSE: 19.39
  - MAE: 14.07
  - R²: 0.78


- **Outlier Impact**:
  - Date 2025-06-05: Error with outliers: 28.45, Error without outliers: 28.37


<style>
:root {
    --jp-rendermime-error-background: white;
}
</style>
