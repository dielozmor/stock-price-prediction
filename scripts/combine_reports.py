#!/usr/bin/env python3
"""
Combines multiple PDF reports into a single final report with a dynamically generated cover page.
The script merges PDFs for data inspection, model analysis, and a cover page, using configuration
details from a JSON file. Filenames are adjusted to remove 'fetch_' prefixes for consistency.
"""

import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfMerger
from spp.data_utils import load_config, extract_timestamp

# Define project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def generate_cover_page(config, cover_pdf_path, author="Diego Lozano"):
    """
    Generate a cover page PDF with project details and an executive summary.

    Args:
        config (dict): Configuration dictionary containing fetch and model details.
        cover_pdf_path (str): Path where the cover page PDF will be saved.
        author (str, optional): Name of the report author. Defaults to "Diego Lozano".

    Raises:
        Exception: If there is an error during PDF generation or text rendering.
    """
    c = canvas.Canvas(cover_pdf_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 100, "Stock Price Prediction Pipeline Evaluation")

    # Extract details from config
    stock_symbol = config["current_fetch"]["stock_symbol"].upper()
    fetch_id = config["current_fetch"]["fetch_id"]
    model_id_with = config["current_models"]["with_outliers"]
    timestamp = extract_timestamp(model_id_with)
    base_model_id = f"model_{stock_symbol.lower()}_{timestamp}"

    # Get the current date dynamically
    current_date = datetime.now().strftime("%B %d, %Y")

    # Define the details to display
    details = [
        ("Stock:", stock_symbol),
        ("Fetch ID:", fetch_id),
        ("Model ID:", base_model_id),
        ("Variants:", "with_outliers, without_outliers"),
        ("Date:", current_date),
        ("Author:", author)
    ]

    # Draw details with deliberations
    y = height - 150
    for label, value in details:
        c.setFont("Helvetica-Bold", 14)
        label_width = c.stringWidth(label, "Helvetica-Bold", 14)
        c.drawString(width / 2 - label_width - 55, y, label)
        c.setFont("Helvetica", 14)
        c.drawString(width / 2 - 45, y, value)
        y -= 30

    # Project Overview
    c.setFont("Helvetica-Bold", 18)
    y -= 50
    c.drawCentredString(width / 2, y, "Project Overview")
    y -= 24  # Added 24-point line space after title
    c.setFont("Helvetica", 14)
    project_overview = (
        "This report examines a machine learning pipeline designed to predict stock price movements, "
        "adaptable to any stock symbol. The pipeline leverages historical data and key market features "
        "to assess predictive performance across various conditions. Visualizations illustrate the "
        "accuracy and limitations of the predictions, particularly during volatile periods."
    )
    text = c.beginText(width / 2 - (width - 100) / 2, y)
    text.setFont("Helvetica", 14)
    text.setLeading(16)
    lines = project_overview.split()
    current_line = ""
    for word in lines:
        if c.stringWidth(current_line + word, "Helvetica", 14) < (width - 100):
            current_line += word + " "
        else:
            text.textLine(current_line)
            current_line = word + " "
            y -= 16
    text.textLine(current_line)
    c.drawText(text)

    c.showPage()
    c.save()

def merge_pdfs(cover_pdf, inspect_pdf, model_pdf, final_pdf):
    """
    Merge the cover page, data inspection, and model analysis PDFs into a single final report.

    Args:
        cover_pdf (str): Path to the cover page PDF.
        inspect_pdf (str): Path to the data inspection PDF.
        model_pdf (str): Path to the model analysis PDF.
        final_pdf (str): Path where the final merged PDF will be saved.

    Raises:
        FileNotFoundError: If any input PDF file is missing.
        Exception: If there is an error during PDF merging.
    """
    merger = PdfMerger()
    try:
        merger.append(cover_pdf)
        merger.append(inspect_pdf)
        merger.append(model_pdf)
        with open(final_pdf, "wb") as fout:
            merger.write(fout)
    except FileNotFoundError as e:
        print(f"PDF file not found: {e}")
        exit(1)
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        exit(1)

if __name__ == "__main__":
    """
    Main execution block to generate and merge PDFs for the stock price prediction pipeline report.
    Loads configuration, generates a cover page, and combines it with data inspection and model
    analysis PDFs. Removes temporary files after merging.
    """
    # Load config using utility function
    config = load_config(config_path=os.path.join(PROJECT_ROOT, "config/config.json"))

    stock_symbol = config["current_fetch"]["stock_symbol"].lower()
    fetch_id = config["current_fetch"]["fetch_id"]
    model_id_with = config["current_models"]["with_outliers"]
    timestamp = extract_timestamp(model_id_with)

    # Strip 'fetch_' from fetch_id for filename consistency
    fetch_timestamp = fetch_id.replace("fetch_", "")

    # Define reports directory
    reports_dir = os.path.join(PROJECT_ROOT, "docs", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Define PDF file paths
    inspect_pdf = os.path.join(PROJECT_ROOT, config["docs_data_eval_dir"], f"inspect_data_{stock_symbol}_{fetch_timestamp}.pdf")
    model_pdf = os.path.join(PROJECT_ROOT, config["docs_model_eval_dir"], f"model_analysis_{stock_symbol}_{timestamp}.pdf")
    cover_pdf = os.path.join(reports_dir, "cover_page.pdf")
    final_pdf = os.path.join(reports_dir, f"final_report_{stock_symbol}_{timestamp}.pdf")

    # Generate dynamic cover page with executive summary
    generate_cover_page(config, cover_pdf)

    # Merge all PDFs into the final report
    merge_pdfs(cover_pdf, inspect_pdf, model_pdf, final_pdf)

    # Clean up temporary files
    os.remove(cover_pdf)

    print(f"Final report generated: {final_pdf}")