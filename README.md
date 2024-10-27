# Invoice PDF Data Extraction and Storage in PostgreSQL

This project reads information from PDF invoices, extracts relevant data fields, and uploads the structured information to a PostgreSQL database. It automates the data extraction process from invoices, reducing the need for manual entry and ensuring a consistent storage format for easy querying and analysis.

## Features

- **PDF Parsing:** Uses `PyPDF2` to extract text data from PDF invoices.
- **Data Parsing:** Extracts fields like `from_address`, `to_address`, `GSTIN`, `invoice number`, `invoice date`, `purchase order details`, `grand total`, and `items`.
- **Database Insertion:** Creates and populates tables in PostgreSQL dynamically based on the invoice's `from_address` (company name).
- **Structured Storage:** Ensures data is well-organized, with items stored in JSONB format within PostgreSQL for easy access and analysis.

## Project Structure

- `extract_text_from_pdf`: Reads and extracts text from the PDF file.
- `parse_invoice_data`: Extracts and structures specific data fields from the extracted text.
- `create_company_table`: Dynamically creates a table for each company if it does not already exist.
- `insert_invoice_data`: Inserts extracted data into the PostgreSQL database in the appropriate company table.

## Prerequisites

1. **Python Libraries**  
   Install the required libraries:
   ```bash
   pip install PyPDF2 psycopg2-binary

   
## PostgreSQL Database

Ensure you have a PostgreSQL database set up and running. Update the connection details in `insert_invoice_data` to match your configuration.

## Limitations

- The script assumes a consistent invoice format.
- Date parsing may require adjustments for different formats.

## Contributing

Feel free to submit issues, fork the repository, and make pull requests for improvements. Contributions are welcome!
