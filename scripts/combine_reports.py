import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PyPDF2 import PdfMerger
from spp.data_utils import load_config, extract_timestamp

# Define project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def generate_cover_page(config, cover_pdf_path, author="Diego Lozano"):
    """Generate a cover page PDF dynamically with an automation-friendly executive summary."""
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

    # Draw details with bold labels and regular values on the same line
    y = height - 150
    for label, value in details:
        # Set bold font for label
        c.setFont("Helvetica-Bold", 14)
        label_width = c.stringWidth(label, "Helvetica-Bold", 14)
        c.drawString(width / 2 - label_width - 55, y, label)  # Label to the left

        # Set regular font for value
        c.setFont("Helvetica", 14)
        value_width = c.stringWidth(value, "Helvetica", 14)
        c.drawString(width / 2 - 45, y, value)  # Value to the right

        y -= 30  # Vertical spacing between lines

    # Add extra space before Project Overview
    y -= 50  # Added 50 points of extra space

    # Project Overview
    c.setFont("Helvetica-Bold", 16)
    y -= 30
    c.drawCentredString(width / 2, y, "Project Overview")  # Centered title
    c.setFont("Helvetica", 12)
    y -= 20
    project_overview = (
        "This report examines a machine learning pipeline designed to predict stock price movements, adaptable to any stock symbol. The pipeline leverages historical data and key market features to assess predictive performance across various conditions. Visualizations illustrate the accuracy and limitations of the predictions, particularly during volatile periods. Future enhancements could involve exploring advanced techniques and additional features to improve robustness."
    )
    # Wrap text to fit page width
    text = c.beginText(width / 2 - (width - 100) / 2, y)  # Centered text block
    text.setFont("Helvetica", 12)
    text.setLeading(14)  # Line spacing
    lines = project_overview.split()
    current_line = ""
    for word in lines:
        if c.stringWidth(current_line + word, "Helvetica", 12) < (width - 100):
            current_line += word + " "
        else:
            text.textLine(current_line)
            current_line = word + " "
            y -= 14
    text.textLine(current_line)
    c.drawText(text)

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

    # Generate dynamic cover page with executive summary
    generate_cover_page(config, cover_pdf)

    # Merge all PDFs into the final report
    merge_pdfs(cover_pdf, inspect_pdf, model_pdf, final_pdf)

    # Clean up temporary cover page file
    os.remove(cover_pdf)

    print(f"Final report generated: {final_pdf}")