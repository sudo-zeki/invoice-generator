# invoice_app.py

import json
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
INVOICE_DIR = ROOT / "invoices"
INVOICE_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "business_name": "Your Biz Name",
    "address": "Addis Ababa, Ethiopia",
    "phone": "+251 900 000 000",
    "vat_rate": 0.15,
    "currency": "ETB"
}

def load_or_create_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    print("Created config.json — edit it to add your real info.")
    return DEFAULT_CONFIG

class InvoicePDF(FPDF):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        logo_path = "logo.jpg"
        try:
            self.image(logo_path, x=10, y=8, w=30)
        except Exception as e:
            print("⚠️ Logo not found or failed to load:", e)

        self.set_font("Helvetica", "B", 14)
        self.set_xy(50, 10)
        self.cell(0, 8, self.config["business_name"], ln=1)

        self.set_font("Helvetica", "", 10)
        self.set_x(50)
        self.multi_cell(0, 5, f'{self.config["address"]}\nPhone: {self.config["phone"]}')
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def format_money(x, currency="ETB"):
    return f"{x:,.2f} {currency}"

def prompt_customer():
    print("\n=== Customer Info ===")
    name = input("Customer name: ").strip() or "Unknown"
    phone = input("Customer phone (optional): ").strip()
    return {"name": name, "phone": phone}

def prompt_items():
    print("\n=== Add Items (leave name empty to finish) ===")
    items = []
    while True:
        name = input("Item name: ").strip()
        if not name:
            break
        qty = float(input("Quantity: "))
        price = float(input("Unit price: "))
        items.append({"name": name, "qty": qty, "price": price})
    if not items:
        print("No items entered. Exiting.")
        exit(0)
    return items

def generate_invoice_number(customer_name=""):
    name_part = customer_name.strip().replace(" ", "_")[:10] or "Unknown"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{name_part}_invoice_{timestamp}"

def generate_invoice_pdf(config, invoice_no, customer, items, output_path):
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

    pdf.output(output_path)

def main():
    config = load_or_create_config()
    customer = prompt_customer()
    items = prompt_items()
    invoice_no = generate_invoice_number(customer["name"])

    # Create monthly subfolder: invoices/YYYY-MM
    month_folder = INVOICE_DIR / datetime.now().strftime("%Y-%m")
    month_folder.mkdir(parents=True, exist_ok=True)

    # Save invoice inside that folder
    filename = month_folder / f"{invoice_no}.pdf"
    generate_invoice_pdf(config, invoice_no, customer, items, str(filename))
    print(f"\n✅ Invoice saved to: {filename.resolve()}")

if __name__ == "__main__":
    main()