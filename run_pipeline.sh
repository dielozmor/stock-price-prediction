#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Ensure log directory exists
mkdir -p logs

# Define LOG_FILE
LOG_FILE="logs/pipeline.log"

# Function to send notifications
send_notification() {
    local message="$1"
    # Write alert to file
    echo "$(date): ALERT - $message" >> logs/alerts.txt
    echo "$(date): ALERT - $message" >> "$LOG_FILE"
}

# Get stock symbol from command-line argument
if [ -z "$1" ]; then
    echo "Error: Stock symbol not provided" | tee -a logs/pipeline.log
    send_notification "Stock symbol not provided"
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
    send_notification "Pipeline failed at initialize_config.py"
    exit 1
fi

# Run fetch_data.py
echo "Running fetch_data.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/fetch_data.py --stock_symbol $stock_symbol 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in fetch_data.py at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at fetch_data.py"
    exit 1
fi

# Get fetch_id from config.json
fetch_id=$(python3 -c "import json; f = open('config/config.json'); data = json.load(f); f.close(); print(data['current_fetch']['fetch_id'])")
if [ -z "$fetch_id" ]; then
    echo "Error: Failed to retrieve fetch_id from config.json" | tee -a logs/pipeline.log
    send_notification "Failed to retrieve fetch_id from config.json"
    exit 1
fi

# Run inspect_data.ipynb with parameters
echo "Running inspect_data.ipynb at $(date)" | tee -a logs/pipeline.log
cd "$(dirname "$0")"
pwd | tee -a logs/pipeline.log
papermill notebooks/inspect_data.ipynb notebooks/temp/inspect_data_temp.ipynb \
    -p stock_symbol $stock_symbol \
    -p fetch_id $fetch_id \
    -p config_path "config/config.json" \
    -p auto_confirm_outliers "True" \
    --log-output \
    2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in inspect_data.ipynb at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at inspect_data.ipynb"
    exit 1
fi

# Run export_notebook.py for inspect_data_temp.ipynb
echo "Running export_notebook.py for inspect_data_temp.ipynb at $(date)" | tee -a logs/pipeline.log
python3 scripts/export_notebook.py --notebook notebooks/temp/inspect_data_temp.ipynb --original_notebook inspect_data.ipynb 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in export_notebook.py for inspect_data_temp.ipynb at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at export_notebook.py (inspect_data_temp)"
    exit 1
fi

# Run process_data.py --step clean
echo "Running process_data.py --step clean at $(date)" | tee -a logs/pipeline.log
python3 scripts/process_data.py --step clean 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in process_data.py --step clean at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at process_data.py --step clean"
    exit 1
fi

# Run process_data.py --step feature
echo "Running process_data.py --step feature at $(date)" | tee -a logs/pipeline.log
python3 scripts/process_data.py --step feature 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in process_data.py --step feature at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at process_data.py --step feature"
    exit 1
fi

# Run model.py
echo "Running model.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/model.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in model.py at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at model.py"
    exit 1
fi

# Run model_analysis.ipynb with parameters
echo "Running model_analysis.ipynb at $(date)" | tee -a logs/pipeline.log
cd "$(dirname "$0")"
pwd | tee -a logs/pipeline.log
papermill notebooks/model_analysis.ipynb notebooks/temp/model_analysis_temp.ipynb \
    -p stock_symbol $stock_symbol \
    -p fetch_id $fetch_id \
    -p config_path "config/config.json" \
    --log-output \
    2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in model_analysis.ipynb at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at model_analysis.ipynb"
    exit 1
fi

# Run export_notebook.py for model_analysis_temp.ipynb
echo "Running export_notebook.py for model_analysis_temp.ipynb at $(date)" | tee -a logs/pipeline.log
python3 scripts/export_notebook.py --notebook notebooks/temp/model_analysis_temp.ipynb --original_notebook model_analysis.ipynb 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in export_notebook.py for model_analysis_temp.ipynb at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at export_notebook.py (model_analysis_temp)"
    exit 1
fi

# Run monitor_performance.py
echo "Running monitor_performance.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/monitor_performance.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in monitor_performance.py at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at monitor_performance.py"
    exit 1
fi

# Run combine_reports.py
echo "Running combine_reports.py at $(date)" | tee -a logs/pipeline.log
python3 scripts/combine_reports.py 2>&1 | tee -a logs/pipeline.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Error in combine_reports.py at $(date)" | tee -a logs/pipeline.log
    send_notification "Pipeline failed at combine_reports.py"
    exit 1
fi

# Log completion
echo "Pipeline completed at $(date)" | tee -a logs/pipeline.log

# Deactivate the virtual environment
deactivate