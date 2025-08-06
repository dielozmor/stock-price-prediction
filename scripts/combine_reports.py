import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PyPDF2 import PdfMerger
from spp.data_utils import load_config, extract_timestamp

# Define project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def generate_cover_page(config, cover_pdf_path, author="Diego Lozano"):
    """Generate a cover page PDF dynamically using data from the config at the specified path."""
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

    # Define the details to display
    details = [
        f"Stock: {stock_symbol}",
        f"Fetch ID: {fetch_id}",
        f"Model ID: {base_model_id}",
        "Variants: with_outliers, without_outliers",
        "Date: August 06, 2025",
        f"Author: {author}"
    ]

    # Set font for details and draw each line
    c.setFont("Helvetica", 14)
    y = height - 150
    for line in details:
        c.drawCentredString(width / 2, y, line)
        y -= 20

    c.showPage()
    c.save()

def merge_pdfs(cover_pdf, inspect_pdf, model_pdf, final_pdf):
    """Merge the cover page with the inspection and model analysis PDFs."""
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
    # Load config using utility function
    config = load_config(config_path=os.path.join(PROJECT_ROOT, "config/config.json"))

    stock_symbol = config["current_fetch"]["stock_symbol"].lower()
    fetch_id = config["current_fetch"]["fetch_id"]

    # Define reports directory
    reports_dir = os.path.join(PROJECT_ROOT, "docs", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Define PDF file paths
    inspect_pdf = os.path.join(PROJECT_ROOT, config["docs_data_eval_dir"], f"inspect_data_{stock_symbol}_{fetch_id}.pdf")
    model_pdf = os.path.join(PROJECT_ROOT, config["docs_model_eval_dir"], f"model_analysis_{stock_symbol}_{fetch_id}.pdf")
    cover_pdf = os.path.join(reports_dir, "cover_page.pdf")
    final_pdf = os.path.join(reports_dir, f"final_report_{fetch_id}.pdf")

    # Generate dynamic cover page inside docs/reports/
    generate_cover_page(config, cover_pdf)

    # Merge all PDFs into the final report
    merge_pdfs(cover_pdf, inspect_pdf, model_pdf, final_pdf)

    # Clean up temporary cover page file
    os.remove(cover_pdf)

    print(f"Final report generated: {final_pdf}")