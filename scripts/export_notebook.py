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
from spp.data_utils import load_config, parse_arguments, extract_timestamp
from spp.logging_utils import setup_logging
from tag_filter import TagFilterPreprocessor

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logger = setup_logging(logger_name="export_notebook", log_dir="logs")

def load_notebook(
    notebook_path: str
) -> nbformat.NotebookNode:
    logger.info(f"Attempting to load notebook: {notebook_path}")
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
        logger.info(f"Exporting to Markdown: {output_path}")
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
        logger.info(f"Exporting to PDF: {output_path}")
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

        # Extract base notebook name without path or extension for mapping
        notebook_base = os.path.splitext(os.path.basename(args.notebook))[0]

        notebook_to_dir = {
            "inspect_data": "docs_data_eval_dir",
            "model_analysis": "docs_model_eval_dir",
            "model_analysis_temp": "docs_model_eval_dir",  # Treat temp variant the same
            "final_report": "docs_reports_dir",
            "final_report_executed": "docs_reports_dir"
        }

        if notebook_base not in notebook_to_dir:
            logger.warning(f"Notebook base {notebook_base} not in known list: {list(notebook_to_dir.keys())}. Using default output directory.")
            output_dir = "docs/default"
        else:
            dir_key = notebook_to_dir[notebook_base]
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

        # Use model ID timestamp for model_analysis variants, else use fetch_id
        identifier = fetch_id.replace("fetch_", "")
        if "model_analysis" in notebook_base:
            current_models = config.get("current_models", {})
            model_id = current_models.get("without_outliers") or current_models.get("with_outliers")
            if model_id:
                try:
                    identifier = extract_timestamp(model_id)
                    logger.info(f"Using model timestamp {identifier} for {args.notebook}")
                except ValueError as e:
                    logger.warning(f"Failed to extract timestamp from model_id {model_id}: {str(e)}. Falling back to fetch_id {identifier}.")
            else:
                logger.warning(f"No model_id found in current_models. Using fetch_id {identifier}.")

        # Use a clean base name for final report
        base_name = "final_report" if "final_report" in notebook_base else notebook_base
        output_md_file = os.path.join(PROJECT_ROOT, output_dir, f"{base_name}_{stock_symbol.lower()}_{identifier}.md")
        output_pdf_file = os.path.join(PROJECT_ROOT, output_dir, f"{base_name}_{stock_symbol.lower()}_{identifier}.pdf")

        # Configure exporters to include outputs and filter by 'export' tag
        c = Config()
        c.MarkdownExporter.preprocessors = [TagFilterPreprocessor]
        c.WebPDFExporter.preprocessors = [TagFilterPreprocessor]
        c.MarkdownExporter.exclude_input = True
        c.WebPDFExporter.exclude_input = True
        c.MarkdownExporter.exclude_output = False
        c.WebPDFExporter.exclude_output = False
        c.MarkdownExporter.enable_math = False
        c.WebPDFExporter.enable_math = False

        # Load notebook
        notebook_path = os.path.join(PROJECT_ROOT, "notebooks", args.notebook)
        nb = load_notebook(notebook_path)

        # Log cells with 'export' tag and their outputs
        export_cells = [cell for cell in nb.cells if 'export' in cell.metadata.get('tags', [])]
        cells_with_output = [cell for cell in export_cells if cell.get('outputs', [])]
        logger.info(f"Found {len(export_cells)} cells with 'export' tag, {len(cells_with_output)} with outputs")

        # Add dynamic date cell
        current_date = datetime.now().strftime("%B %d, %Y")
        date_cell = nbformat.v4.new_markdown_cell(f"**Date**: {current_date}")
        date_cell.metadata['tags'] = ['export']
        nb.cells.insert(0, date_cell)

        # Export to Markdown and PDF
        export_markdown(nb, output_md_file, config=c)
        export_pdf(nb, output_pdf_file, config=c)

        logger.info("Notebook export completed successfully", extra={"identifier": identifier})

    except Exception as e:
        logger.error(f"Script failed: {str(e)}", extra={"identifier": identifier if 'identifier' in locals() else "N/A"})
        raise SystemExit(1)

if __name__ == "__main__":
    main()