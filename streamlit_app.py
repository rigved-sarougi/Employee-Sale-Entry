import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import uuid
from PIL import Image

# Display Title and Description
st.title("Biolume: Sales & Visit Management System")

# Constants
SALES_SHEET_COLUMNS = [
    "Invoice Number", "Invoice Date", "Employee Name", "Employee Code", "Designation",
    "Discount Category", "Transaction Type", "Outlet Name", "Outlet Contact",
    "Outlet Address", "Outlet State", "Outlet City", "Distributor Firm Name",
    "Distributor ID", "Distributor Contact Person", "Distributor Contact Number",
    "Distributor Email", "Distributor Territory", "Product ID", "Product Name",
    "Product Category", "Quantity", "Unit Price", "Total Price", "GST Rate",
    "CGST Amount", "SGST Amount", "Grand Total", "Overall Discount (%)",
    "Amount Discount (INR)", "Discounted Price", "Payment Status", "Amount Paid",
    "Payment Receipt Path", "Employee Selfie Path", "Invoice PDF Path"
]

VISIT_SHEET_COLUMNS = [
    "Visit ID", "Employee Name", "Employee Code", "Designation", "Outlet Name",
    "Outlet Contact", "Outlet Address", "Outlet State", "Outlet City", "Visit Date",
    "Entry Time", "Exit Time", "Visit Duration (minutes)", "Visit Purpose",
    "Visit Notes", "Visit Selfie Path", "Visit Status"
]

ATTENDANCE_SHEET_COLUMNS = [
    "Attendance ID", "Employee Name", "Employee Code", "Designation", "Date",
    "Status", "Location Link", "Leave Reason", "Check-in Time"
]

# Establishing a Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Load data
Products = pd.read_csv('Invoice - Products.csv')
Outlet = pd.read_csv('Invoice - Outlet.csv')
Person = pd.read_csv('Invoice - Person.csv')
Distributors = pd.read_csv('Invoice - Distributors.csv')

# Company Details
company_name = "BIOLUME SKIN SCIENCE PRIVATE LIMITED"
company_address = """Ground Floor Rampal Awana Complex,
Rampal Awana Complex, Indra Market,
Sector-27, Atta, Noida, Gautam Buddha Nagar,
Uttar Pradesh 201301
GSTIN/UIN: 09AALCB9426H1ZA
State Name: Uttar Pradesh, Code: 09
"""
company_logo = 'ALLGEN TRADING logo.png'
bank_details = """
Disclaimer: This Proforma Invoice is for estimation purposes only and is not a demand for payment. 
Prices, taxes, and availability are subject to change. Final billing may vary. 
Goods/services will be delivered only after confirmation and payment. No legal obligation is created by this document.
"""

# Create directories for storing uploads
os.makedirs("employee_selfies", exist_ok=True)
os.makedirs("payment_receipts", exist_ok=True)
os.makedirs("invoices", exist_ok=True)
os.makedirs("visit_selfies", exist_ok=True)

# Custom PDF class
class PDF(FPDF):
    def header(self):
        if company_logo:
            self.image(company_logo, 10, 8, 33)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, company_name, ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, company_address, align='C')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Proforma Invoice', ln=True, align='C')
        self.line(10, 50, 200, 50)
        self.ln(1)

def generate_invoice_number():
    return f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

def generate_visit_id():
    return f"VISIT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

def generate_attendance_id():
    return f"ATT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

def save_uploaded_file(uploaded_file, folder):
    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1]
        file_path = os.path.join(folder, f"{str(uuid.uuid4())}{file_ext}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

def log_sales_to_gsheet(conn, sales_data):
    try:
        existing_sales_data = conn.read(worksheet="Sales", usecols=list(range(len(SALES_SHEET_COLUMNS))), ttl=5)
        existing_sales_data = existing_sales_data.dropna(how="all")
        updated_sales_data = pd.concat([existing_sales_data, sales_data], ignore_index=True)
        conn.update(worksheet="Sales", data=updated_sales_data)
        st.success("Sales data successfully logged to Google Sheets!")
    except Exception as e:
        st.error(f"Error logging sales data: {e}")

def log_visit_to_gsheet(conn, visit_data):
    try:
        existing_visit_data = conn.read(worksheet="Visits", usecols=list(range(len(VISIT_SHEET_COLUMNS))), ttl=5)
        existing_visit_data = existing_visit_data.dropna(how="all")
        updated_visit_data = pd.concat([existing_visit_data, visit_data], ignore_index=True)
        conn.update(worksheet="Visits", data=updated_visit_data)
        st.success("Visit data successfully logged to Google Sheets!")
    except Exception as e:
        st.error(f"Error logging visit data: {e}")

def log_attendance_to_gsheet(conn, attendance_data):
    try:
        existing_attendance_data = conn.read(worksheet="Attendance", usecols=list(range(len(ATTENDANCE_SHEET_COLUMNS))), ttl=5)
        existing_attendance_data = existing_attendance_data.dropna(how="all")
        updated_attendance_data = pd.concat([existing_attendance_data, attendance_data], ignore_index=True)
        conn.update(worksheet="Attendance", data=updated_attendance_data)
        st.success("Attendance data successfully logged to Google Sheets!")
    except Exception as e:
        st.error(f"Error logging attendance data: {e}")

def check_attendance_submitted(employee_name):
    try:
        existing_attendance = conn.read(worksheet="Attendance", ttl=5)
        today = datetime.now().strftime("%d-%m-%Y")
        if not existing_attendance.empty:
            existing_attendance = existing_attendance.dropna(how="all")
            today_attendance = existing_attendance[
                (existing_attendance['Employee Name'] == employee_name) & 
                (existing_attendance['Date'] == today)
            ]
            return not today_attendance.empty
        return False
    except Exception as e:
        st.error(f"Error checking attendance: {e}")
        return False

def get_employee_sales(employee_name):
    try:
        sales_data = conn.read(worksheet="Sales", ttl=5)
        if not sales_data.empty:
            sales_data = sales_data.dropna(how="all")
            return sales_data[sales_data['Employee Name'] == employee_name]
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching sales data: {e}")
        return pd.DataFrame()

def authenticate_employee(employee_name, passkey):
    try:
        employee_code = Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0]
        return str(passkey) == str(employee_code)
    except:
        return False

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'selected_mode' not in st.session_state:
        st.session_state.selected_mode = None
    if 'employee_name' not in st.session_state:
        st.session_state.employee_name = None

    if not st.session_state.authenticated:
        st.title("Employee Authentication")
        
        mode = st.radio("Select Mode", ["Sales", "Visit", "Attendance", "Sales History"], key="mode_selection")
        employee_names = Person['Employee Name'].tolist()
        employee_name = st.selectbox("Select Your Name", employee_names, key="employee_select")
        passkey = st.text_input("Enter Your Employee Code", type="password", key="passkey_input")
        
        if st.button("Authenticate"):
            if authenticate_employee(employee_name, passkey):
                st.session_state.authenticated = True
                st.session_state.selected_mode = mode
                st.session_state.employee_name = employee_name
                st.rerun()
            else:
                st.error("Invalid Employee Code. Please try again.")
    else:
        if st.session_state.selected_mode == "Sales":
            sales_page()
        elif st.session_state.selected_mode == "Visit":
            visit_page()
        elif st.session_state.selected_mode == "Attendance":
            attendance_page()
        else:
            sales_history_page()

def sales_page():
    st.title("Sales Management")
    selected_employee = st.session_state.employee_name

    st.subheader("Employee Verification")
    employee_selfie = st.file_uploader("Upload Employee Selfie", type=["jpg", "jpeg", "png"])

    discount_category = Person[Person['Employee Name'] == selected_employee]['Discount Category'].values[0]

    st.subheader("Transaction Details")
    transaction_type = st.selectbox("Transaction Type", ["Sold", "Return", "Add On", "Damage", "Expired"])

    st.subheader("Product Details")
    product_names = Products['Product Name'].tolist()
    selected_products = st.multiselect("Select Products", product_names)

    quantities = []
    if selected_products:
        for product in selected_products:
            qty = st.number_input(f"Quantity for {product}", min_value=1, value=1, step=1)
            quantities.append(qty)

    st.subheader("Discount Options")
    col1, col2 = st.columns(2)
    with col1:
        overall_discount = st.number_input("Percentage Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    with col2:
        amount_discount = st.number_input("Amount Discount (INR)", min_value=0.0, value=0.0, step=1.0)

    st.subheader("Payment Details")
    payment_status = st.selectbox("Payment Status", ["pending", "paid", "partial paid"])

    amount_paid = 0.0
    payment_receipt = None

    if payment_status == "partial paid":
        amount_paid = st.number_input("Amount Paid (INR)", min_value=0.0, value=0.0, step=1.0)
        payment_receipt = st.file_uploader("Upload Payment Receipt", type=["jpg", "jpeg", "png", "pdf"])
    elif payment_status == "paid":
        amount_paid = st.number_input("Amount Paid (INR)", min_value=0.0, value=0.0, step=1.0)
        payment_receipt = st.file_uploader("Upload Payment Receipt", type=["jpg", "jpeg", "png", "pdf"])

    st.subheader("Distributor Details")
    distributor_option = st.radio("Distributor Selection", ["Select from list", "None"])
    
    distributor_firm_name = ""
    distributor_id = ""
    distributor_contact_person = ""
    distributor_contact_number = ""
    distributor_email = ""
    distributor_territory = ""
    
    if distributor_option == "Select from list":
        distributor_names = Distributors['Firm Name'].tolist()
        selected_distributor = st.selectbox("Select Distributor", distributor_names)
        distributor_details = Distributors[Distributors['Firm Name'] == selected_distributor].iloc[0]
        
        distributor_firm_name = selected_distributor
        distributor_id = distributor_details['Distributor ID']
        distributor_contact_person = distributor_details['Contact Person']
        distributor_contact_number = distributor_details['Contact Number']
        distributor_email = distributor_details['Email ID']
        distributor_territory = distributor_details['Territory']
        
        st.text_input("Distributor ID", value=distributor_id, disabled=True)
        st.text_input("Contact Person", value=distributor_contact_person, disabled=True)
        st.text_input("Contact Number", value=distributor_contact_number, disabled=True)
        st.text_input("Email", value=distributor_email, disabled=True)
        st.text_input("Territory", value=distributor_territory, disabled=True)

    st.subheader("Outlet Details")
    outlet_option = st.radio("Outlet Selection", ["Select from list", "Enter manually"])
    
    if outlet_option == "Select from list":
        outlet_names = Outlet['Shop Name'].tolist()
        selected_outlet = st.selectbox("Select Outlet", outlet_names)
        outlet_details = Outlet[Outlet['Shop Name'] == selected_outlet].iloc[0]
        
        customer_name = selected_outlet
        gst_number = outlet_details['GST']
        contact_number = outlet_details['Contact']
        address = outlet_details['Address']
        state = outlet_details['State']
        city = outlet_details['City']
    else:
        customer_name = st.text_input("Outlet Name")
        gst_number = st.text_input("GST Number")
        contact_number = st.text_input("Contact Number")
        address = st.text_area("Address")
        state = st.text_input("State", "Uttar Pradesh")
        city = st.text_input("City", "Noida")

    if st.button("Generate Invoice"):
        if selected_products and customer_name:
            invoice_number = generate_invoice_number()
            
            employee_selfie_path = save_uploaded_file(employee_selfie, "employee_selfies") if employee_selfie else None
            payment_receipt_path = save_uploaded_file(payment_receipt, "payment_receipts") if payment_receipt else None
            
            pdf, pdf_path = generate_invoice(
                customer_name, gst_number, contact_number, address, state, city,
                selected_products, quantities, discount_category, 
                selected_employee, overall_discount, amount_discount,
                payment_status, amount_paid, employee_selfie_path, 
                payment_receipt_path, invoice_number, transaction_type,
                distributor_firm_name, distributor_id, distributor_contact_person,
                distributor_contact_number, distributor_email, distributor_territory
            )
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download Invoice", 
                    f, 
                    file_name=f"{invoice_number}.pdf",
                    mime="application/pdf"
                )
            
            st.success(f"Invoice {invoice_number} generated successfully!")
        else:
            st.error("Please fill all required fields and select products.")

def visit_page():
    st.title("Visit Management")
    selected_employee = st.session_state.employee_name

    st.subheader("Outlet Details")
    outlet_option = st.radio("Outlet Selection", ["Select from list", "Enter manually"])
    
    if outlet_option == "Select from list":
        outlet_names = Outlet['Shop Name'].tolist()
        selected_outlet = st.selectbox("Select Outlet", outlet_names)
        outlet_details = Outlet[Outlet['Shop Name'] == selected_outlet].iloc[0]
        
        outlet_name = selected_outlet
        outlet_contact = outlet_details['Contact']
        outlet_address = outlet_details['Address']
        outlet_state = outlet_details['State']
        outlet_city = outlet_details['City']
    else:
        outlet_name = st.text_input("Outlet Name")
        outlet_contact = st.text_input("Outlet Contact")
        outlet_address = st.text_area("Outlet Address")
        outlet_state = st.text_input("Outlet State", "Uttar Pradesh")
        outlet_city = st.text_input("Outlet City", "Noida")

    st.subheader("Visit Details")
    visit_purpose = st.selectbox("Visit Purpose", ["Sales", "Product Demonstration", "Relationship Building", "Issue Resolution", "Other"])
    visit_notes = st.text_area("Visit Notes")
    
    st.subheader("Visit Verification")
    visit_selfie = st.file_uploader("Upload Visit Selfie", type=["jpg", "jpeg", "png"])

    st.subheader("Time Tracking")
    col1, col2 = st.columns(2)
    with col1:
        entry_time = st.time_input("Entry Time", value=datetime.now().time())
    with col2:
        exit_time = st.time_input("Exit Time", value=datetime.now().time())

    if st.button("Record Visit"):
        if outlet_name:
            today = datetime.now().date()
            entry_datetime = datetime.combine(today, entry_time)
            exit_datetime = datetime.combine(today, exit_time)
            
            visit_selfie_path = save_uploaded_file(visit_selfie, "visit_selfies") if visit_selfie else None
            
            visit_id = record_visit(
                selected_employee, outlet_name, outlet_contact, outlet_address,
                outlet_state, outlet_city, visit_purpose, visit_notes, 
                visit_selfie_path, entry_datetime, exit_datetime
            )
            
            st.success(f"Visit {visit_id} recorded successfully!")
        else:
            st.error("Please fill all required fields.")

def attendance_page():
    st.title("Attendance Management")
    selected_employee = st.session_state.employee_name
    today = datetime.now().strftime("%d-%m-%Y")

    # Check if attendance already submitted today
    if check_attendance_submitted(selected_employee):
        st.warning(f"You have already submitted attendance for {today}")
        return

    st.subheader("Attendance Status")
    status = st.radio("Select Status", ["Working", "Leave"])

    if status == "Working":
        live_location = st.text_input("Enter Live Location Link (Google Maps or similar)")
        
        if st.button("Submit Attendance"):
            if live_location:
                attendance_id = record_attendance(
                    employee_name=selected_employee,
                    status="Working",
                    location_link=live_location
                )
                st.success(f"Attendance recorded successfully! ID: {attendance_id}")
            else:
                st.error("Please provide your live location link")
    else:
        leave_reason = st.text_area("Leave Reason")
        if st.button("Submit Leave"):
            if leave_reason:
                attendance_id = record_attendance(
                    employee_name=selected_employee,
                    status="Leave",
                    leave_reason=leave_reason
                )
                st.success(f"Leave recorded successfully! ID: {attendance_id}")
            else:
                st.error("Please provide a leave reason")

def sales_history_page():
    st.title("Your Sales History")
    selected_employee = st.session_state.employee_name

    # Search options
    st.subheader("Search Your Sales")
    col1, col2, col3 = st.columns(3)
    with col1:
        invoice_number = st.text_input("Search by Invoice Number")
    with col2:
        invoice_date = st.date_input("Search by Date")
    with col3:
        outlet_name = st.text_input("Search by Outlet Name")

    # Get employee's sales data
    sales_data = get_employee_sales(selected_employee)
    
    if sales_data.empty:
        st.info("No sales records found")
        return

    # Apply filters
    if invoice_number:
        sales_data = sales_data[sales_data['Invoice Number'].str.contains(invoice_number, case=False)]
    if invoice_date:
        search_date = invoice_date.strftime("%d-%m-%Y")
        sales_data = sales_data[sales_data['Invoice Date'] == search_date]
    if outlet_name:
        sales_data = sales_data[sales_data['Outlet Name'].str.contains(outlet_name, case=False)]

    if sales_data.empty:
        st.info("No records match your search criteria")
        return

    # Display results
    st.subheader("Matching Sales Records")
    
    # Show simplified view
    display_cols = ["Invoice Number", "Invoice Date", "Outlet Name", "Transaction Type", "Grand Total"]
    st.dataframe(
        sales_data[display_cols].sort_values("Invoice Date", ascending=False),
        use_container_width=True
    )

    # Option to view details
    st.subheader("View Details")
    selected_invoice = st.selectbox(
        "Select Invoice to View Details",
        sales_data['Invoice Number'].unique()
    )
    
    if selected_invoice:
        invoice_details = sales_data[sales_data['Invoice Number'] == selected_invoice].iloc[0]
        
        st.write(f"**Invoice Date:** {invoice_details['Invoice Date']}")
        st.write(f"**Outlet:** {invoice_details['Outlet Name']}")
        st.write(f"**Transaction Type:** {invoice_details['Transaction Type']}")
        st.write(f"**Grand Total:** ₹{invoice_details['Grand Total']:.2f}")
        
        # Show products (for invoices with multiple products)
        if 'Product Name' in sales_data.columns:
            products = sales_data[sales_data['Invoice Number'] == selected_invoice][
                ['Product Name', 'Quantity', 'Unit Price', 'Total Price']
            ]
            st.write("**Products:**")
            st.dataframe(products, use_container_width=True)

def record_attendance(employee_name, status, location_link="", leave_reason=""):
    attendance_id = generate_attendance_id()
    current_date = datetime.now().strftime("%d-%m-%Y")
    check_in_time = datetime.now().strftime("%H:%M:%S")
    
    attendance_data = {
        "Attendance ID": attendance_id,
        "Employee Name": employee_name,
        "Employee Code": Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0],
        "Designation": Person[Person['Employee Name'] == employee_name]['Designation'].values[0],
        "Date": current_date,
        "Status": status,
        "Location Link": location_link,
        "Leave Reason": leave_reason,
        "Check-in Time": check_in_time
    }
    
    attendance_df = pd.DataFrame([attendance_data])
    log_attendance_to_gsheet(conn, attendance_df)
    
    return attendance_id

if __name__ == "__main__":
    main()
