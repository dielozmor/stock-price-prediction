#!/usr/bin/env python3
"""
Exports a Jupyter notebook to Markdown and PDF formats, filtering for cells tagged with 'export'.
Adds a dynamic date stamp. Requires --notebook argument to specify the notebook to process.
Output directory defaults based on notebook name, overridable with --output-dir.
"""

import os
import nbformat
from nbconvert import MarkdownExporter, WebPDFExporter
from traitlets.config import Config
from datetime import datetime
from spp.data_utils import load_config, parse_arguments
from spp.logging_utils import setup_logging
from tag_filter import TagFilterPreprocessor

# Define project root to match data_utils.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Initialize logger
logger = setup_logging(logger_name="export_notebook", log_dir="logs")

def load_notebook(notebook_path: str) -> nbformat.NotebookNode:
    """Load a Jupyter notebook from the given path."""
    if not os.path.exists(notebook_path):
        error_msg = f"Notebook {notebook_path} not found"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return nbformat.read(f, as_version=4)

def export_markdown(nb: nbformat.NotebookNode, output_path: str, config: Config = None) -> None:
    """Export the notebook to Markdown using MarkdownExporter."""
    try:
        md_exporter = MarkdownExporter(config=config)
        (body, resources) = md_exporter.from_notebook_node(nb)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(body)
        logger.info(f"Markdown exported to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting Markdown: {str(e)}")
        raise

def export_pdf(nb: nbformat.NotebookNode, output_path: str, config: Config = None) -> None:
    """Export the notebook to PDF using WebPDFExporter."""
    try:
        webpdf_exporter = WebPDFExporter(config=config)
        body, resources = webpdf_exporter.from_notebook_node(nb)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(body)
        logger.info(f"PDF exported to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        raise

def main() -> None:
    """Orchestrate the export of a Jupyter notebook to Markdown and PDF formats."""
    # Define mandatory arguments: --notebook is required
    mandatory_args = ["notebook"]
    args = parse_arguments(mandatory_args=mandatory_args)

    try:
        # Load config using the provided or default config path
        config_path = os.path.join(PROJECT_ROOT, args.config)
        config = load_config(config_path=config_path, logger=logger)

        # Define mapping of notebook names to config directory keys
        notebook_to_dir = {
            "inspect_data.ipynb": "docs_data_eval_dir",
            "model_analysis.ipynb": "docs_model_eval_dir",
        }

        # Validate notebook name
        if args.notebook not in notebook_to_dir:
            logger.warning(f"Notebook {args.notebook} not in known list: {list(notebook_to_dir.keys())}. Using default output directory.")

        # Construct notebook file path (assumes notebooks are in 'notebooks/' directory)
        notebook_path = os.path.join(PROJECT_ROOT, "notebooks", args.notebook)

        # Determine output directory: use --output-dir if provided, else map from notebook name
        if hasattr(args, "output_dir") and args.output_dir:
            output_dir = args.output_dir
            logger.info(f"Using user-specified output directory: {output_dir}")
        else:
            dir_key = notebook_to_dir.get(args.notebook)
            if dir_key:
                output_dir = config.get(dir_key, "docs/default")
                logger.info(f"Using mapped output directory from config[{dir_key}]: {output_dir}")
            else:
                output_dir = "docs/default"
                logger.warning(f"No output directory mapping for notebook {args.notebook}, using default: {output_dir}")

        # Get current_fetch from config
        current_fetch = config.get("current_fetch")
        if not current_fetch:
            logger.error("current_fetch not found in config file")
            raise ValueError("current_fetch not found in config file")

        # Get fetch_id and stock_symbol
        fetch_id = current_fetch.get("fetch_id")
        if not fetch_id:
            logger.error("fetch_id not found in current_fetch", extra={"fetch_id": "N/A"})
            raise ValueError("fetch_id not found in current_fetch")

        stock_symbol = current_fetch.get("stock_symbol", "").upper()
        if not stock_symbol:
            logger.error("stock_symbol not found in current_fetch", extra={"fetch_id": fetch_id})
            raise ValueError("stock_symbol not found in current_fetch")

        # Extract base name of the notebook (without extension)
        base_name = os.path.splitext(args.notebook)[0]

        # Construct output file names with stock symbol and fetch ID
        output_md_file = os.path.join(PROJECT_ROOT, output_dir, f"{base_name}_{stock_symbol.lower()}_{fetch_id}.md")
        output_pdf_file = os.path.join(PROJECT_ROOT, output_dir, f"{base_name}_{stock_symbol.lower()}_{fetch_id}.pdf")

        # Configure exporters to filter 'export' tagged cells and exclude code input
        c = Config()
        c.MarkdownExporter.preprocessors = [TagFilterPreprocessor]
        c.WebPDFExporter.preprocessors = [TagFilterPreprocessor]
        c.MarkdownExporter.exclude_input = True
        c.WebPDFExporter.exclude_input = True
        c.MarkdownExporter.enable_math = False
        c.WebPDFExporter.enable_math = False

        # Load the notebook
        nb = load_notebook(notebook_path)

        # Add a date cell at the top with export tag
        current_date = datetime.now().strftime("%B %d, %Y")
        date_content = f"**Date**: {current_date}"
        date_cell = nbformat.v4.new_markdown_cell(date_content)
        date_cell.metadata['tags'] = ['export']
        nb.cells.insert(0, date_cell)

        # Export to Markdown and PDF
        export_markdown(nb, output_md_file, config=c)
        export_pdf(nb, output_pdf_file, config=c)

        logger.info("Notebook export completed successfully", extra={"fetch_id": fetch_id})

    except Exception as e:
        logger.error(f"Script failed: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)

if __name__ == "__main__":
    main()