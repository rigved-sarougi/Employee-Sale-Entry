import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Load data
Products = pd.read_csv('Invoice - Products.csv')
Outlet = pd.read_csv('Invoice - Outlet.csv')
Person = pd.read_csv('Invoice - Person.csv')

# Company Details
company_name = "BIOLUME SKIN SCIENCE PRIVATE LIMITED"
company_address = """Ground Floor Rampal Awana Complex,
Rampal Awana Complex, Indra Market,
Sector-27, Atta, Noida, Gautam Buddha Nagar,
Uttar Pradesh 201301
GSTIN/UIN: 09AALCB9426H1ZA
State Name: Uttar Pradesh, Code: 09
"""
company_logo = 'ALLGEN TRADING logo.png'  # Ensure the logo file is in the same directory
bank_details = """
Bank Name: Example Bank
Account Number: 1234567890
IFSC Code: EXMP0001234
Branch: Noida Branch
"""

# Custom PDF class
class PDF(FPDF):
    def header(self):
        # Add company logo
        if company_logo:
            self.image(company_logo, 10, 8, 33)
        
        # Company name and address
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, company_name, ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, company_address, align='C')
        
        # Invoice title
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Proforma Invoice', ln=True, align='C')
        self.line(10, 50, 200, 50)  # Horizontal line
        self.ln(1)

# Generate Invoice
def generate_invoice(customer_name, gst_number, contact_number, address, selected_products, quantities, discount_category, employee_name):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Sales Person
    pdf.ln(0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"Sales Person: {employee_name}", ln=True, align='L')
    pdf.ln(0)

    # Customer details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Bill To:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, f"Name: {customer_name}")
    pdf.cell(90, 6, f"Date: {current_date}", ln=True, align='R')
    pdf.cell(100, 6, f"GSTIN/UN: {gst_number}")
    pdf.cell(90, 6, f"Contact: {contact_number}", ln=True, align='R')
    pdf.cell(100, 6, "Address: ", ln=True)
    pdf.multi_cell(0, 6, address)
    pdf.ln(1)
    
    # Table header
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(10, 10, "S.No", border=1, align='C', fill=True)
    pdf.cell(70, 10, "Product Name", border=1, align='C', fill=True)
    pdf.cell(20, 10, "HSN/SAC", border=1, align='C', fill=True)
    pdf.cell(20, 10, "GST Rate", border=1, align='C', fill=True)
    pdf.cell(20, 10, "Qty", border=1, align='C', fill=True)
    pdf.cell(25, 10, "Rate (INR)", border=1, align='C', fill=True)
    pdf.cell(25, 10, "Amount (INR)", border=1, align='C', fill=True)
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", '', 10)
    total_price = 0
    for idx, (product, quantity) in enumerate(zip(selected_products, quantities)):
        product_data = Products[Products['Product Name'] == product].iloc[0]

        if discount_category in product_data:
            unit_price = float(product_data[discount_category])  # Use discount category price
        else:
            unit_price = float(product_data['Price'])

        item_total_price = unit_price * quantity

        pdf.cell(10, 8, str(idx + 1), border=1)
        pdf.cell(70, 8, product, border=1)
        pdf.cell(20, 8, "3304", border=1, align='C')
        pdf.cell(20, 8, "18%", border=1, align='C')
        pdf.cell(20, 8, str(quantity), border=1, align='C')
        pdf.cell(25, 8, f"{unit_price:.2f}", border=1, align='R')
        pdf.cell(25, 8, f"{item_total_price:.2f}", border=1, align='R')
        total_price += item_total_price
        pdf.ln()

    # Tax and Grand Total
    pdf.ln(10)
    tax_rate = 0.18
    tax_amount = total_price * tax_rate
    grand_total = math.ceil(total_price + tax_amount)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(160, 10, "Subtotal", border=0, align='R')
    pdf.cell(30, 10, f"{total_price:.2f}", border=1, align='R')
    pdf.ln()
    pdf.cell(160, 10, "CGST (9%)", border=0, align='R')
    pdf.cell(30, 10, f"{tax_amount / 2:.2f}", border=1, align='R')
    pdf.ln()
    pdf.cell(160, 10, "SGST (9%)", border=0, align='R')
    pdf.cell(30, 10, f"{tax_amount / 2:.2f}", border=1, align='R')
    pdf.ln()
    pdf.cell(160, 10, "Grand Total", border=0, align='R')
    pdf.cell(30, 10, f"{grand_total} INR", border=1, align='R', fill=True)
    pdf.ln(20)

    return pdf, total_price, tax_amount, grand_total

# Streamlit UI
st.title("Biolume + ALLGEN TRADING: Billing System")

# Employee Selection
st.subheader("Employee Details")
employee_names = Person['Employee Name'].tolist()
selected_employee = st.selectbox("Select Employee", employee_names)

# Fetch Discount Category
discount_category = Person[Person['Employee Name'] == selected_employee]['Discount Category'].values[0]

# Product Selection
st.subheader("Product Details")
product_names = Products['Product Name'].tolist()
selected_products = st.multiselect("Select Products", product_names)

# Input Quantities for Each Selected Product
quantities = []
if selected_products:
    for product in selected_products:
        qty = st.number_input(f"Quantity for {product}", min_value=1, value=1, step=1)
        quantities.append(qty)

# Outlet Selection
st.subheader("Outlet Details")
outlet_names = Outlet['Shop Name'].tolist()
selected_outlet = st.selectbox("Select Outlet", outlet_names)

# Fetch Outlet Details
outlet_details = Outlet[Outlet['Shop Name'] == selected_outlet].iloc[0]

# Generate Invoice button
if st.button("Generate Invoice"):
    if selected_employee and selected_products and selected_outlet:
        customer_name = selected_outlet
        gst_number = outlet_details['GST']
        contact_number = outlet_details['Contact']
        address = outlet_details['Address']

        # Generate PDF and calculate totals
        pdf, subtotal, tax_amount, grand_total = generate_invoice(customer_name, gst_number, contact_number, address, selected_products, quantities, discount_category, selected_employee)
        pdf_file = f"invoice_{customer_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf.output(pdf_file)

        # Download PDF
        with open(pdf_file, "rb") as f:
            st.download_button("Download Invoice", f, file_name=pdf_file)

        # Submit Invoice Details button
        if st.button("Submit Invoice Details"):
            try:
                # Establish Google Sheets connection
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # Fetch existing invoice data
                existing_data = conn.read(worksheet="Invoices", usecols=list(range(16)), ttl=5)
                existing_data = existing_data.dropna(how="all")

                # Create new invoice data
                invoice_data = pd.DataFrame(
                    [
                        {
                            "InvoiceID": pdf_file,
                            "InvoiceDate": datetime.now().strftime("%Y-%m-%d"),
                            "EmployeeName": selected_employee,
                            "CustomerName": customer_name,
                            "GSTNumber": gst_number,
                            "ContactNumber": contact_number,
                            "Address": address,
                            "Products": ", ".join(selected_products),
                            "Quantities": ", ".join(map(str, quantities)),
                            "DiscountCategory": discount_category,
                            "Subtotal": subtotal,
                            "CGST": tax_amount / 2,
                            "SGST": tax_amount / 2,
                            "GrandTotal": grand_total,
                            "PDFFileName": pdf_file,
                        }
                    ]
                )
                
                # Combine existing and new data
                updated_df = pd.concat([existing_data, invoice_data], ignore_index=True)
                
                # Update Google Sheets
                conn.update(worksheet="Invoices", data=updated_df)
                st.success("Invoice details successfully submitted to Google Sheets!")
            except Exception as e:
                st.error(f"Error saving to Google Sheets: {e}")
    else:
        st.error("Please fill all fields and select products.")
