#!/bin/bash

# Navigate to the project directory (adjust this path to your setup)
cd /home/dielozmor/dev/projects/portfolio/stock-price-prediction

# Activate the virtual environment
source venv/bin/activate

# Set stock symbol
stock_symbol = "TSLA"

# Run the pipeline scripts with error handling
echo "Starting pipeline at $(date)" >> logs/pipeline.log

# Run initialize_config.py
echo "Running initialize_config.py at $(date)" >> logs/pipeline.log
python3 scripts/initialize_config.py >> logs/pipeline.log 2>&1 || {
	echo "Error in initialize_config.py at $(date)" >> logs/pipelin.log
	exit 1
}

# Run fetch_data.py
echo "Running fetch_data.py at $(date)" >> logs/pipeline.log
python3 scripts/fetch_data.py --stock_symbol TSLA >> logs/pipeline.log 2>&1 || {
    echo "Error in fetch_data.py at $(date)" >> logs/pipeline.log
    exit 1
}

# Run inspect_data.ipynb
echo "Running inspect_data.ipynb at $(date) >> 
papermill notebooks/inspect_data.ipynb docs/data_evaluation/inspect_data_executed.ipynb \
	-p stock_symbol "TSLA" \
	-p data_path "data/raw/" \
	>> logs/pipeline.log 2>&1 || {
	echo "Error in inspect_data.ipynb at $(date)" >> logs/pipeline.log
	exit 1
}

# Run export_notebook.py for notebook inspect_data.ipynb
python3 scripts/export_notebook.py --notebook inspect_data.ipynb >> logs/pipeline.log 2>&1 || {
    echo "Error in export_notebook.py for notebook inspect_data.ipynb at $(date)" >> logs/pipeline.log
    exit 1
}

# Run process_data for step clean
python3 scripts/process_data.py --step clean >> logs/pipeline.log 2>&1 || {
    echo "Error in process_data.py for step clean at $(date)" >> logs/pipeline.log
    exit 1
}

# Run process_data for step feature
python3 scripts/process_data.py --step feature >> logs/pipeline.log 2>&1 || {
    echo "Error in process_data.py for step feature at $(date)" >> logs/pipeline.log
    exit 1
}

# Run model.py 
python3 scripts/model.py >> logs/pipeline.log 2>&1 || {
    echo "Error in model.py at $(date)" >> logs/pipeline.log
    exit 1
}

# Run model_analysis.ipynb
papermill

# Run export_notebook.py for notebook model_analysis.ipynb
python3 scripts/export_notebook.py --notebook model_analysis.ipynb >> logs/pipeline.log 2>&1 || {
    echo "Error in export_notebook.py for notebook model_analysis.ipynb at $(date)" >> logs/pipeline.log
    exit 1
}

# Run combine_reports.py
python3 scripts/combine_reports.py >> logs/pipeline.log 2>&1 || {
    echo "Error in combine_reports.py at $(date)" >> logs/pipeline.log
    exit 1
}

# Log completion
echo "Pipeline completed at $(date)" >> logs/pipeline.log

# Deactivate the virtual environment
deactivate
