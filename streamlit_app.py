import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime

# Display Title and Description
st.title("Biolume: Sales Management System")

# Constants
SALES_SHEET_COLUMNS = [
    "Invoice Date",
    "Employee Name",
    "Employee Code",
    "Designation",
    "Discount Category",
    "Outlet Name",
    "Outlet Contact",
    "Outlet Address",
    "Outlet State",
    "Outlet City",
    "Product ID",
    "Product Name",
    "Product Category",
    "Quantity",
    "Unit Price",
    "Total Price",
    "GST Rate",
    "CGST Amount",
    "SGST Amount",
    "Grand Total",
    "Overall Discount (%)",
    "Discounted Price"
]

# Establishing a Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

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

# Function to log sales data to Google Sheets
def log_sales_to_gsheet(conn, sales_data):
    try:
        # Fetch existing data
        existing_sales_data = conn.read(worksheet="Sales", usecols=list(range(len(SALES_SHEET_COLUMNS))), ttl=5)
        existing_sales_data = existing_sales_data.dropna(how="all")
        
        # Combine existing data with new data
        updated_sales_data = pd.concat([existing_sales_data, sales_data], ignore_index=True)
        
        # Update the Google Sheet
        conn.update(worksheet="Sales", data=updated_sales_data)
        st.success("Sales data successfully logged to Google Sheets!")
    except Exception as e:
        st.error(f"Error logging sales data: {e}")

# Generate Invoice
def generate_invoice(customer_name, gst_number, contact_number, address, selected_products, quantities, discount_category, employee_name, overall_discount):
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
    sales_data = []
    for idx, (product, quantity) in enumerate(zip(selected_products, quantities)):
        product_data = Products[Products['Product Name'] == product].iloc[0]

        if discount_category in product_data:
            unit_price = float(product_data[discount_category])  # Use discount category price
        else:
            unit_price = float(product_data['Price'])

        # Apply overall discount
        discounted_price = unit_price * (1 - overall_discount / 100)
        item_total_price = discounted_price * quantity

        pdf.cell(10, 8, str(idx + 1), border=1)
        pdf.cell(70, 8, product, border=1)
        pdf.cell(20, 8, "3304", border=1, align='C')
        pdf.cell(20, 8, "18%", border=1, align='C')
        pdf.cell(20, 8, str(quantity), border=1, align='C')
        pdf.cell(25, 8, f"{discounted_price:.2f}", border=1, align='R')
        pdf.cell(25, 8, f"{item_total_price:.2f}", border=1, align='R')
        total_price += item_total_price
        pdf.ln()

        # Prepare sales data for logging
        sales_data.append({
            "Invoice Date": current_date,
            "Employee Name": employee_name,
            "Employee Code": Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0],
            "Designation": Person[Person['Employee Name'] == employee_name]['Designation'].values[0],
            "Discount Category": discount_category,
            "Outlet Name": customer_name,
            "Outlet Contact": contact_number,
            "Outlet Address": address,
            "Outlet State": Outlet[Outlet['Shop Name'] == customer_name]['State'].values[0],
            "Outlet City": Outlet[Outlet['Shop Name'] == customer_name]['City'].values[0],
            "Product ID": product_data['Product ID'],
            "Product Name": product,
            "Product Category": product_data['Product Category'],
            "Quantity": quantity,
            "Unit Price": unit_price,
            "Total Price": item_total_price,
            "GST Rate": "18%",
            "CGST Amount": item_total_price * 0.09,
            "SGST Amount": item_total_price * 0.09,
            "Grand Total": item_total_price * 1.18,
            "Overall Discount (%)": overall_discount,
            "Discounted Price": discounted_price
        })

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

    # Log sales data to Google Sheets
    sales_df = pd.DataFrame(sales_data)
    log_sales_to_gsheet(conn, sales_df)

    return pdf

# Streamlit UI
st.title("")

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

# Overall Discount
st.subheader("Overall Discount")
overall_discount = st.number_input("Enter Overall Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

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

        pdf = generate_invoice(customer_name, gst_number, contact_number, address, selected_products, quantities, discount_category, selected_employee, overall_discount)
        pdf_file = f"invoice_{customer_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download Invoice", f, file_name=pdf_file)
    else:
        st.error("Please fill all fields and select products.")
