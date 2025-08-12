#!/bin/bash

# Navigate to the project directory (adjust this path to your setup)
cd /home/dielozmor/dev/projects/portfolio/stock-price-prediction

# Activate the virtual environment
source venv/bin/activate

# Ensure log directory exists
mkdir -p logs

# Get stock symbol from command-line argument
if [ -z "$1" ]; then
    echo "Error: Stock symbol not provided" | tee -a logs/pipeline.log
    exit 1
fi
stock_symbol=$1

# Run the pipeline scripts with error handling
echo "Starting pipeline at $(date)" | tee -a logs/pipeline.log

# Run initialize_config.py
echo "Running initialize_config.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/initialize_config.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in initialize_config.py at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run fetch_data.py
echo "Running fetch_data.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/fetch_data.py --stock_symbol $stock_symbol 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in fetch_data.py at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Get fetch_id from config.json
fetch_id=$(python3 -c "import json; f = open('config/config.json'); data = json.load(f); f.close(); print(data['current_fetch']['fetch_id'])")
if [ -z "$fetch_id" ]; then
    echo "Error: Failed to retrieve fetch_id from config.json" | tee -a logs/pipeline.log
    exit 1
fi

# Run inspect_data.ipynb with parameters
echo "Running inspect_data.ipynb at $(date)" | tee -a logs/pipeline.log
papermill notebooks/inspect_data.ipynb docs/data_evaluation/inspect_data_executed.ipynb \
    -p stock_symbol $stock_symbol \
    -p fetch_id $fetch_id \
    -p config_path "config/config.json" \
    -p auto_confirm_outliers "True" \
    2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in inspect_data.ipynb at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run export_notebook.py for inspect_data.ipynb
echo "Running export_notebook.py for inspect_data.ipynb at $(date)" | tee -a logs/pipeline.log
python3 scripts/export_notebook.py --notebook inspect_data.ipynb 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in export_notebook.py for inspect_data.ipynb at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run process_data.py --step clean
echo "Running process_data.py --step clean at $(date)" | tee -a logs/pipeline.log
python3 scripts/process_data.py --step clean 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in process_data.py --step clean at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run process_data.py --step feature
echo "Running process_data.py --step feature at $(date)" | tee -a logs/pipeline.log
python3 scripts/process_data.py --step feature 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in process_data.py --step feature at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run model.py
echo "Running model.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/model.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in model.py at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run predict.py
echo "Running predict.py at $(date)" | tee -1 logs/pipeline.log
python3 scripts/predict.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in predict.py at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run model_analysis.ipynb with parameters
echo "Running model_analysis.ipynb at $(date)" | tee -a logs/pipeline.log
papermill notebooks/model_analysis.ipynb docs/model_evaluation/model_analysis_executed.ipynb \
    -p stock_symbol $stock_symbol \
    -p fetch_id $fetch_id \
    -p config_path "config/config.json" \
    -p auto_generate_summary "True" \
    2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in model_analysis.ipynb at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run export_notebook.py for model_analysis.ipynb
echo "Running export_notebook.py for model_analysis.ipynb at $(date)" | tee -a logs/pipeline.log
python3 scripts/export_notebook.py --notebook model_analysis.ipynb 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in export_notebook.py for model_analysis.ipynb at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Run combine_reports.py
echo "Running combine_reports.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/combine_reports.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in combine_reports.py at $(date)" | tee -a logs/pipeline.log
    exit 1
fi

# Log completion
echo "Pipeline completed at $(date)" | tee -a logs/pipeline.log

# Deactivate the virtual environment
deactivate