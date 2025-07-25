import streamlit as st
import json
from datetime import datetime
from fpdf import FPDF
from pathlib import Path
import os

# Config & Invoice Directory
ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
INVOICE_DIR = ROOT / "invoices"
INVOICE_DIR.mkdir(exist_ok=True)

# Load config
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# PDF Generator Class
class InvoicePDF(FPDF):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, self.config["business_name"], ln=1)

        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, f'{self.config["address"]}\nPhone: {self.config["phone"]}')
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

# Generate Invoice PDF

def generate_invoice_pdf(invoice_no, customer, items):
    subtotal = sum(i["qty"] * i["price"] for i in items)
    vat = subtotal * config["vat_rate"]
    total = subtotal + vat

    pdf = InvoicePDF(config)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(100, 6, f"Invoice No: {invoice_no}", ln=0)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "BILL TO:", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, customer["name"], ln=1)
    if customer.get("phone"):
        pdf.cell(0, 6, f"Phone: {customer['phone']}", ln=1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 8, "Item", 1)
    pdf.cell(20, 8, "Qty", 1, align="R")
    pdf.cell(30, 8, "Price", 1, align="R")
    pdf.cell(30, 8, "Total", 1, ln=1, align="R")

    pdf.set_font("Helvetica", "", 10)
    for i in items:
        line_total = i["qty"] * i["price"]
        pdf.cell(80, 8, i["name"][:35], 1)
        pdf.cell(20, 8, f'{i["qty"]:.2f}', 1, align="R")
        pdf.cell(30, 8, f'{i["price"]:.2f}', 1, align="R")
        pdf.cell(30, 8, f'{line_total:.2f}', 1, ln=1, align="R")

    pdf.ln(4)
    pdf.cell(130, 8, "Subtotal:", 0, 0, "R")
    pdf.cell(30, 8, f'{subtotal:.2f}', 0, 1, "R")
    pdf.cell(130, 8, f'VAT ({int(config["vat_rate"]*100)}%):', 0, 0, "R")
    pdf.cell(30, 8, f'{vat:.2f}', 0, 1, "R")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 8, "TOTAL:", 0, 0, "R")
    pdf.cell(30, 8, f'{total:.2f} {config["currency"]}', 0, 1, "R")

    month_folder = INVOICE_DIR / datetime.now().strftime("%Y-%m")
    month_folder.mkdir(parents=True, exist_ok=True)
    path = month_folder / f"{invoice_no}.pdf"
    pdf.output(str(path))
    return path

# UI
st.title("🧾 Invoice Generator")

with st.form("invoice_form"):
    st.subheader("Customer Info")
    customer_name = st.text_input("Customer name", max_chars=50)
    customer_phone = st.text_input("Phone number", max_chars=20)

    st.subheader("Items")
    item_names = st.text_area("Item names (one per line)")
    item_qtys = st.text_area("Quantities (same order)")
    item_prices = st.text_area("Unit Prices (same order)")

    submitted = st.form_submit_button("Generate Invoice")

if submitted:
    names = [n.strip() for n in item_names.strip().splitlines() if n.strip()]
    qtys = [float(q.strip()) for q in item_qtys.strip().splitlines() if q.strip()]
    prices = [float(p.strip()) for p in item_prices.strip().splitlines() if p.strip()]

    if not (len(names) == len(qtys) == len(prices)):
        st.error("Each item must have a quantity and price.")
    else:
        items = [{"name": n, "qty": q, "price": p} for n, q, p in zip(names, qtys, prices)]
        invoice_no = f"{customer_name.replace(' ', '_')}_invoice_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        pdf_path = generate_invoice_pdf(invoice_no, {"name": customer_name, "phone": customer_phone}, items)
        st.success(f"✅ Invoice generated: {pdf_path.name}")

        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Invoice", f, file_name=pdf_path.name, mime="application/pdf")
