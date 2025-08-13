# Automation Guide for Stock Price Prediction Pipeline

This guide will walk you through automating your `run_pipeline.sh` script using **cron** on Linux. By the end, your stock price prediction pipeline will run automatically (e.g., weekly) to keep your models updated with fresh data. Let’s break it down into simple, manageable steps!

---

### **Step 1: Test the Automation Script Manually**

Before automating, test the script manually to confirm it works perfectly. This saves headaches later!

#### **1.1 Make the Script Executable**
- Ensure your script has executable permissions:
  ```bash
  chmod +x /home/dielozmor/dev/projects/portfolio/stock-price-prediction/run_pipeline.sh
  ```

#### **1.2 Run the Script Manually**
- Run the script with a stock symbol (e.g., TSLA):
  ```bash
  /home/dielozmor/dev/projects/portfolio/stock-price-prediction/run_pipeline.sh TSLA
  ```
  - **Note**: The script expects a stock symbol as an argument. Swap `TSLA` for another symbol if needed.

#### **1.3 Verify Each Step**
- **Check the Log File**: The script logs to `logs/pipeline.log`. Inspect it with:
  ```bash
  cat /home/dielozmor/dev/projects/portfolio/stock-price-prediction/logs/pipeline.log
  ```
  - **Look For**:
    - Success: Messages like “Running [script] at [date]” and “Pipeline completed at [date]”.
    - Errors: Lines like “Error in fetch_data.py at [date]”.
- **Verify Outputs**:
  - **Config**: Check `config/config.json` is updated.
  - **Data**: Look in `data/raw/` for files like `raw_tsla_fetch_<timestamp>.csv` and `data/processed/` for processed data.
  - **Notebooks**: Confirm executed notebooks in `docs/data_evaluation/` and `docs/model_evaluation/` (e.g., `inspect_data_executed.ipynb`).
  - **Exports**: Verify Markdown/PDF files in `docs/data_evaluation/` and `docs/model_evaluation/`.
  - **Models**: Check `models/` for new model files (e.g., `model_tsla_<timestamp>_with_outliers.pkl`) and `models/models_history.jsonl` for metrics.
  - **Reports**: Ensure `combine_reports.py` generates the combined report (PDF only in `docs/reports/`).
- **Troubleshoot Errors**: If something fails, use `pipeline.log` to pinpoint the issue (e.g., missing file, API error) and fix it before moving on.

#### **1.4 Ensure Dependencies**
- The script uses `papermill` for notebooks. Install it if missing:
  ```bash
  pip install papermill
  ```
- Check other dependencies (e.g., `pandas`, `nbconvert`, `weasyprint`) with:
  ```bash
  pip list
  ```

---

### **Step 2: Set Up the Cron Task**

Once the script works manually, let’s schedule it with cron for automation.

#### **2.1 Create a Log Directory**
- Ensure the `logs/` directory exists:
  ```bash
  mkdir -p /home/dielozmor/dev/projects/portfolio/stock-price-prediction/logs
  ```

#### **2.2 Open the Cron Editor**
- Edit your cron jobs:
  ```bash
  crontab -e
  ```

#### **2.3 Add the Cron Job**
- Add this line to run the pipeline every Monday at 8 AM:
  ```bash
  0 8 * * 1 /home/dielozmor/dev/projects/portfolio/stock-price-prediction/run_pipeline.sh TSLA >> /home/dielozmor/dev/projects/portfolio/stock-price-prediction/logs/cron.log 2>&1
  ```
- **Breakdown**:
  - `0 8 * * 1`: 8:00 AM every Monday.
  - `TSLA`: Stock symbol argument (change as needed).
  - `>> logs/cron.log 2>&1`: Logs output and errors to `cron.log`.
- **Customize the Schedule**:
  - Daily at midnight: `0 0 * * *`
  - Every 5 minutes (for testing): `*/5 * * * *`
  - Try [crontab.guru](https://crontab.guru/) for other options.
- **Save and Exit**: In `nano`, press `Ctrl+O`, `Enter`, then `Ctrl+X`.

#### **2.4 Verify Cron Setup**
- List your cron jobs to confirm:
  ```bash
  crontab -l
  ```
- Wait for the scheduled time (or test with a frequent schedule) and check `logs/cron.log`:
  ```bash
  cat /home/dielozmor/dev/projects/portfolio/stock-price-prediction/logs/cron.log
  ```

---

### **Step 3: Monitor and Troubleshoot**

After the cron job runs, ensure everything worked as expected.

- **Check Logs**:
  - `logs/cron.log`: Look for cron-specific output or errors.
  - `logs/pipeline.log`: Review detailed pipeline execution logs.
- **Verify Outputs**: Confirm all files (data, models, exports) are created in their directories.
- **Common Issues and Fixes**:
  - **Path Errors**: Cron uses absolute paths. If it fails, double-check paths in `run_pipeline.sh`.
  - **Virtual Environment**: If the script relies on a virtual environment, update the cron job:
    ```bash
    0 8 * * 1 /bin/bash -c "source /home/dielozmor/dev/projects/portfolio/stock-price-prediction/venv/bin/activate && /home/dielozmor/dev/projects/portfolio/stock-price-prediction/run_pipeline.sh TSLA" >> /home/dielozmor/dev/projects/portfolio/stock-price-prediction/logs/cron.log 2>&1
    ```
  - **API Limits**: If Alpha Vantage rate limits are hit, add delays or error handling in `fetch_data.py`.

---