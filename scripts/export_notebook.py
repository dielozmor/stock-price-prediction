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

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logger = setup_logging(logger_name="export_notebook", log_dir="logs")

def load_notebook(
    notebook_path: str
) -> nbformat.NotebookNode:
    if not os.path.exists(notebook_path):
        error_msg = f"Notebook {notebook_path} not found"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return nbformat.read(f, as_version=4)

def export_markdown(
    nb: nbformat.NotebookNode, 
    output_path: str, 
    config: Config = None
) -> None:
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

def export_pdf(
    nb: nbformat.NotebookNode, 
    output_path: str, 
    config: Config = None
) -> None:
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
    mandatory_args = ["notebook"]
    args = parse_arguments(mandatory_args=mandatory_args)

    try:
        config_path = os.path.join(PROJECT_ROOT, args.config)
        config = load_config(config_path=config_path, logger=logger)

        notebook_to_dir = {
            "inspect_data.ipynb": "docs_data_eval_dir",
            "model_analysis.ipynb": "docs_model_eval_dir",
            "final_report.ipynb": "docs_reports_dir",
            "final_report_executed.ipynb": "docs_reports_dir"
        }

        if args.notebook not in notebook_to_dir:
            logger.warning(f"Notebook {args.notebook} not in known list: {list(notebook_to_dir.keys())}. Using default output directory.")
            output_dir = "docs/default"
        else:
            dir_key = notebook_to_dir[args.notebook]
            output_dir = config.get(dir_key, "docs/default")
            logger.info(f"Using mapped output directory from config[{dir_key}]: {output_dir}")

        current_fetch = config.get("current_fetch")
        if not current_fetch:
            logger.error("current_fetch not found in config file")
            raise ValueError("current_fetch not found in config file")

        fetch_id = current_fetch.get("fetch_id")
        stock_symbol = current_fetch.get("stock_symbol", "").upper()
        if not fetch_id or not stock_symbol:
            logger.error(f"fetch_id or stock_symbol missing in current_fetch", extra={"fetch_id": fetch_id or "N/A"})
            raise ValueError("fetch_id or stock_symbol missing in current_fetch")

        # Use a clean base name for final report
        base_name = "final_report" if "final_report" in args.notebook else os.path.splitext(args.notebook)[0]
        output_md_file = os.path.join(PROJECT_ROOT, output_dir, f"{base_name}_{stock_symbol.lower()}_{fetch_id}.md")
        output_pdf_file = os.path.join(PROJECT_ROOT, output_dir, f"{base_name}_{stock_symbol.lower()}_{fetch_id}.pdf")

        c = Config()
        c.MarkdownExporter.preprocessors = [TagFilterPreprocessor]
        c.WebPDFExporter.preprocessors = [TagFilterPreprocessor]
        c.MarkdownExporter.exclude_input = True
        c.WebPDFExporter.exclude_input = True
        c.MarkdownExporter.enable_math = False
        c.WebPDFExporter.enable_math = False

        nb = load_notebook(os.path.join(PROJECT_ROOT, "notebooks", args.notebook))
        current_date = datetime.now().strftime("%B %d, %Y")
        date_cell = nbformat.v4.new_markdown_cell(f"**Date**: {current_date}")
        date_cell.metadata['tags'] = ['export']
        nb.cells.insert(0, date_cell)

        export_markdown(nb, output_md_file, config=c)
        export_pdf(nb, output_pdf_file, config=c)

        logger.info("Notebook export completed successfully", extra={"fetch_id": fetch_id})

    except Exception as e:
        logger.error(f"Script failed: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)

if __name__ == "__main__":
    main()