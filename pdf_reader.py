import re
import PyPDF2
import psycopg2
import json
from datetime import datetime

def extract_text_from_pdf(pdf_file: str) -> str:
    """Open and read the PDF file and extract its text."""
    with open(pdf_file, 'rb') as pdf:
        reader = PyPDF2.PdfReader(pdf)
        content = ''
        for page in reader.pages:
            content += page.extract_text()
        return content

def parse_invoice_data(text: str) -> dict:
    """Parse the extracted text and return structured invoice data."""
    data = {}

    # Extract From Address (up to GSTIN)
    from_address_match = re.search(r"From:\s*(.*?)(GSTIN:)", text, re.DOTALL)
    data['from_address'] = from_address_match.group(1).strip() if from_address_match else "N/A"
    
    # Extract From GSTIN
    from_gstin_match = re.search(r"From:.*?GSTIN:\s*(\w+)", text, re.DOTALL)
    data['from_gstin'] = from_gstin_match.group(1) if from_gstin_match else "N/A"
    
    # Extract To Address (up to GSTIN)
    to_address_match = re.search(r"To:\s*(.*?)(GSTIN:)", text, re.DOTALL)
    data['to_address'] = to_address_match.group(1).strip() if to_address_match else "N/A"
    
    # Extract To GSTIN
    to_gstin_match = re.search(r"To:.*?GSTIN:\s*(\w+)", text, re.DOTALL)
    data['to_gstin'] = to_gstin_match.group(1) if to_gstin_match else "N/A"
    
    # Extract Invoice Number, Date, PO Number, and PO Date
    invoice_number_match = re.search(r"Invoice Number:\s*(\S+)", text)
    data['invoice_number'] = invoice_number_match.group(1) if invoice_number_match else "N/A"
    
    invoice_date_match = re.search(r"Invoice Date:\s*([\d-]+)", text)
    data['invoice_date'] = invoice_date_match.group(1) if invoice_date_match else "N/A"
    
    po_number_match = re.search(r"Purchase Order Number:\s*(\S+)", text)
    data['po_number'] = po_number_match.group(1) if po_number_match else "N/A"
    
    po_date_match = re.search(r"Purchase Order Date:\s*([\d-]+)", text)
    data['po_date'] = po_date_match.group(1) if po_date_match else "N/A"
    
    # Extract Grand Total
    grand_total_match = re.search(r"Grand Total:\s*([\d.]+)", text)
    data['grand_total'] = grand_total_match.group(1) if grand_total_match else "N/A"
    
    # Extract Purchase Order Items (Description, Quantity, Unit Price, Total)
    items = []
    item_pattern = re.compile(r"(Product|Service)\s+([A-Za-z0-9\s]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)")
    item_matches = item_pattern.findall(text)
    
    for match in item_matches:
        item = {
            'description': match[1].strip(),
            'quantity': int(match[2]),
            'unit_price': float(match[3]),
            'total_price': float(match[4])
        }
        items.append(item)

    data['items'] = items
    
    return data


def create_company_table(cursor, company_name):
    """Create a table for the company if it does not exist."""
    table_name = company_name.replace(" ", "_").replace(",", "").replace(".", "")  # Clean table name
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            from_address TEXT,
            from_gstin VARCHAR(15),
            to_address TEXT,
            to_gstin VARCHAR(15),
            invoice_number VARCHAR(50),
            invoice_date DATE,
            po_number VARCHAR(50),
            po_date DATE,
            grand_total DECIMAL,
            items JSONB
        );
    """)

def insert_invoice_data(data):
    """Insert the invoice data into the appropriate company table."""
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(
            dbname='invoice_db',  # Replace with your database name
            user='**********',  # Replace with your PostgreSQL username
            password='**********',  # Replace with your PostgreSQL password
            host='localhost',  # or your server's IP address
            port='5432'  # Default PostgreSQL port
        )
        cursor = conn.cursor()

        # Extract only the company name for the table
        company_name = data['from_address'].splitlines()[0]  # Get only the first line (company name)
        create_company_table(cursor, company_name)

        # Validate and convert dates to the correct format
        try:
            if data['invoice_date'].isdigit():  # Check if it's just a year
                invoice_date = datetime.strptime(data['invoice_date'], '%Y').date().replace(month=1, day=1)
            else:
                invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date() if data['invoice_date'] != "N/A" else None
            
            if data['po_date'].isdigit():  # Check if it's just a year
                po_date = datetime.strptime(data['po_date'], '%Y').date().replace(month=1, day=1)
            else:
                po_date = datetime.strptime(data['po_date'], '%Y-%m-%d').date() if data['po_date'] != "N/A" else None
        except ValueError as ve:
            print("Date format error:", ve)
            return  # Exit if date format is incorrect

        # Insert the invoice data
        table_name = company_name.replace(" ", "_").replace(",", "").replace(".", "")  # Clean table name
        insert_query = f"""
        INSERT INTO {table_name} (from_address, from_gstin, to_address, to_gstin, 
                                  invoice_number, invoice_date, po_number, po_date, 
                                  grand_total, items)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            data['from_address'], data['from_gstin'], data['to_address'], 
            data['to_gstin'], data['invoice_number'], invoice_date, 
            data['po_number'], po_date, 
            data['grand_total'], 
            json.dumps(data['items'])  # Convert items list to JSON
        ))

        # Commit the changes
        conn.commit()
        cursor.close()
        conn.close()
        print("Invoice data inserted successfully.")

    except Exception as e:
        print("Error inserting data:", e)


def main():
    """Main function to execute the workflow."""
    # Extract text from the invoice PDF
    extracted_text = extract_text_from_pdf("invoice_parallel.pdf")
    
    # Parse the extracted text to categorize data
    invoice_data = parse_invoice_data(extracted_text)
    
    # Print the parsed data
    for key, value in invoice_data.items():
        if key == 'items':
            print(f"{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")
    
    # Insert data into the PostgreSQL database
    insert_invoice_data(invoice_data)

if __name__ == '__main__':
    main()
