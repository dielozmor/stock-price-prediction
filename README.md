# Stock Price Prediction Project

**Authors**: Diego Lozano  
**Last Updated**: August 15, 2025  

---

## Table of Contents

- [Overview](#overview)
- [Project Goals](#project-goals)
- [Data Source](#data-source)
- [Model](#model)
- [Directory Structure](#directory-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Automation](#automation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project develops a dynamic pipeline to predict next-day closing stock prices using machine learning, with Tesla (TSLA) as the primary focus. Designed for flexibility, it supports any stock symbol via command-line arguments. Built with Python, it leverages Random Forest models, machine learning techniques, and automation tools like cron, producing predictions and PDF reports. It serves as a robust demonstration of data science and DevOps skills. Notifications for failures are handled via file-based alerts in `logs/alerts.txt`.

---

## Project Goals

- Predict next-day closing stock prices using Random Forest.  
- Support dynamic stock selection with TSLA as the initial stock.  
- Build an automated pipeline for data retrieval, processing, modeling, prediction, performance monitoring, and reporting.  
- Generate detailed evaluation reports (PDF) to assess model performance.

---

## Data Source

- **Source**: Alpha Vantage API (free tier, daily stock data).  
- **Time Frame**: One year of daily data (June 17, 2024–June 16, 2025 for TSLA, ~250 rows after holidays).  
  - *Note*: The time frame and stock can be adjusted via command-line arguments.  
- **Features**: Previous day's closing price, daily trading volume, 5-day moving average (`prev_close`, `volume`, `ma5`).  
- **Target**: Next day's closing price (`next_close`).

---

## Model

- **Algorithm**: Random Forest Regressor, with two versions:  
  - Including outliers (RMSE=19.30, MAE=14.16, R²=0.772).  
  - Excluding outliers (RMSE=19.54, MAE=14.25, R²=0.776).  
  - *Note*: Random Forest was chosen over Linear Regression (R² ~0.78) for better generalization and robustness to non-linear patterns and outliers in TSLA data.  
  - Hyperparameters: `n_estimators=300`, `max_depth=20`, `min_samples_split=5`, `min_samples_leaf=2`, `random_state=42`.  
- **Output**: Models saved as `.pkl` files in `models/` with timestamped names (e.g., `model_tsla_20250815_170544_with_outliers.pkl`).  
- **Prediction**: Use `scripts/predict.py` to make predictions with the trained models.  
- **Performance Monitoring**: `monitor_performance.py` tracks R², RMSE, and MAE, saving results to `docs/model_evaluation/performance_summary_tsla_TIMESTAMP.csv` and flagging degradation (R² < 0.75). Failure alerts are logged to `logs/alerts.txt`.

---

## Directory Structure

- `config/`: Configuration file (`config.json`) for settings (auto-generated).  
- `data/`: Raw (`raw/`), processed (`processed/`), intermediate (`intermediate/`), outlier (`outliers/`) data and a Fetch history file (`fetch_history.jsonl`) for storing data fetches.  
- `docs/`:  
  - `data_evaluation/`: Reports on data inspection (Markdown and PDF exports from notebooks).  
  - `model_evaluation/`: Reports on model performance, including `performance_summary_tsla_TIMESTAMP.csv`.  
  - `reports/`: Final evaluation report (PDF only, e.g., `final_report_tsla_TIMESTAMP.pdf`).  
- `logs/`: Log files for debugging and tracking (`pipeline.log`), and failure alerts (`alerts.txt`).  
- `models/`: Trained models and history (`models_history.jsonl`).  
- `notebooks/`: Data inspection (`inspect_data.ipynb`) and model analysis (`model_analysis.ipynb`).  
- `plots/`: Visualizations from notebooks.  
- `scripts/`: Core scripts (`initialize_config.py`, `fetch_data.py`, `process_data.py`, `model.py`, `export_notebook.py`, `combine_report.py`, `predict.py`, `monitor_performance.py`).  
- `spp/`: Utility modules (`data_utils.py`, `logging_utils.py`, `plot_utils.py`).  

---

## Setup and Installation

Follow these steps to set up and run the stock price prediction project on your local machine.

1. **Clone the Repository**:  
   - Clone the project repository to your local machine and navigate to the project directory:  
     ```bash  
     git clone https://github.com/dielozmor/stock-price-prediction.git  
     cd stock-price-prediction  
     ```

2. **Set Up the Virtual Environment**:  
   - Create a Python virtual environment to manage dependencies:  
     ```bash  
     python3 -m venv venv  
     ```  
   - Activate the virtual environment:  
     - On Unix/Linux/MacOS:  
       ```bash  
       source venv/bin/activate  
       ```  
     - On Windows:  
       ```bash  
       venv\Scripts\activate  
       ```

3. **Install Dependencies**:  
   - Install the required Python packages listed in `requirements.txt`:  
     ```bash  
     pip install -r requirements.txt  
     ```  
   - Install `papermill` for notebook automation:  
     ```bash  
     pip install papermill  
     ```

4. **Configuration**:  
   - The configuration file (`config.json`) is auto-generated by running `initialize_config.py`. To set it up:  
     ```bash  
     python scripts/initialize_config.py  
     ```  
   - Create a `.env` file in the project root and add your Alpha Vantage API key:  
     ```bash  
     echo "ALPHA_VANTAGE_API_KEY=YOUR_API_KEY_HERE" > .env  
     ```  
   - You can obtain a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).  
   - *Note*: The stock symbol must be provided via command-line arguments when running the pipeline, not set in `config.json`.

5. **Run the Pipeline Manually**:  
   - Execute the pipeline script with a stock symbol of your choice:  
     ```bash  
     ./run_pipeline.sh <stock_symbol>  
     ```  
   - Replace `<stock_symbol>` with a valid stock ticker (e.g., `TSLA` for Tesla). Example:  
     ```bash  
     ./run_pipeline.sh TSLA  
     ```  
   - **After running**, check `docs/reports/` for the final report (PDF only) and `plots/` for visualizations. Failure alerts are in `logs/alerts.txt`.

---

## Usage

- **Run the Full Pipeline**:  
  ```bash  
  ./run_pipeline.sh <stock_symbol>  
  ```  
  Example:  
  ```bash  
  ./run_pipeline.sh TSLA  
  ```

- **Run Individual Scripts**:  
  - Initialize Configuration file:
    ```bash
    python scripts/initialize_config.py
    ```
  - Fetch data:  
    ```bash  
    python scripts/fetch_data.py TSLA  
    ```
  - Inspect data:

    (Automated by pipeline; for manual execution, use papermill with parameters from run_pipeline.sh or execute cells manually in inspect_data.ipynb) 

  - Export inspect_data Notebook:
    ``` bash
    python scripts/export_notebook.py --notebook inspect_data.ipynb
    ```  
  - Clean data:  
    ```bash  
    python scripts/process_data.py --step clean  
    ```
  - Add Features:
    ```bash
    python scripts/process_data.py --step feature
    ```  
  - Train models:  
    ```bash  
    python scripts/model.py TSLA  
    ```
  - Analyze models:
    ```bash
    papermill notebooks/model_analysis.ipynb
    ```
  - Analyze Models:

    (Automated by pipeline; for manual execution, use papermill with parameters from run_pipeline.sh or execute cells manually in model_analysis.ipynb)

  - Export model_analysis notebook
    ``` bash
    python scripts/export_notebook.py --notebook model_analysis.ipynb
    ``` 

  - Generate predictions:  
    ```bash  
    python scripts/predict.py TSLA  
    ```  
  - Monitor performance:  
    ```bash  
    python scripts/monitor_performance.py  
    ```  
  - Combine reports:  
    ```bash  
    python scripts/combine_report.py  
    ```

- **View Outputs**:  
  - Predictions: `data/predictions/` (e.g., `tsla_predictions_20250816_070849.csv`)  
  - Performance summaries: `docs/model_evaluation/` (e.g., `performance_summary_tsla_20250815_170544.csv`)  
  - Reports: `docs/reports/` (PDF only, e.g., `final_report_tsla_20250815_170544.pdf`)  
  - Visualizations: `plots/` (e.g., `tsla_model_20250815_170544_with_outliers_predictions.png`)  
  - Logs: `logs/pipeline.log`, `train_model.log`, etc.
  - Alerts: `logs/alerts.txt` (for failures)

---

## Automation

The pipeline can be automated to run at regular intervals using cron (for Unix/Linux/MacOS) or Task Scheduler (for Windows). This ensures iterative model updates with the latest stock data. For detailed steps, refer to [docs/automation.md](docs/automation.md).

---

## Contributing

Contributions are welcome! To contribute:  
1. Fork the repository.  
2. Create a new branch (`git checkout -b feature/your-feature`).  
3. Commit your changes (`git commit -m "Add your feature"`).  
4. Push to the branch (`git push origin feature/your-feature`).  
5. Open a pull request.  

Please ensure your code follows the project’s style and includes appropriate documentation.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.