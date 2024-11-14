from flask import Flask, render_template, request, jsonify, send_file
import os
import pandas as pd
import sqlite3
from io import StringIO
app = Flask(__name__)

# Specifying directory where uploaded files will go
app.config['UPLOAD_FOLDER'] = 'uploads'

# Home route to upload the CSV
@app.route('/')
def index():
    return render_template('index.html', uploaded=False)

# Handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        # Process CSV
        process_csv(file.filename)
        return render_template('index.html', uploaded=True)  # Show the button to proceed to scan page

# Route for barcode scanner page
@app.route('/scanner')
def scanner():
    # Fetch last 5 scanned records to display
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM records WHERE scanned = 'Found' ORDER BY Record_Locator DESC LIMIT 5")
    last_scans = cursor.fetchall()
    conn.close()
    
    return render_template('scanner.html', last_scans=last_scans)

# Route to update the database with barcode scan results
@app.route('/update_scan', methods=['POST'])
def update_scan():
    scanned_code = request.json.get('code')
    
    # Connect to SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Update the record in the database
    cursor.execute("UPDATE records SET scanned = 'Found' WHERE record_locator = ?", (scanned_code,))
    if cursor.rowcount == 0:
        result = 'Not Found'
    else:
        # Get the person's name after marking as 'Found'
        cursor.execute("SELECT first_name, last_name FROM records WHERE record_locator = ?", (scanned_code,))
        person = cursor.fetchone()
        result = f"Found {person[0]} {person[1]}"
    
    conn.commit()
    conn.close()

    return {"result": result}, 200

# Process the uploaded CSV file and save to database
def process_csv(file_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    
    try:
        df = pd.read_csv(file_path, header=0)
    except pd.errors.ParserError:
        return "Error parsing CSV file. Please ensure the file is correctly formatted."

    if df.empty or all(col.startswith('Unnamed') for col in df.columns):
        print("First row has no valid headers, trying the second row as headers...")
        try:
            df = pd.read_csv(file_path, header=1)
        except pd.errors.ParserError:
            return "Error parsing CSV file."

        if df.empty or all(col.startswith('Unnamed') for col in df.columns):
            return "No valid column headers found in the CSV file."

    print("CSV Headers: ", df.columns)

    conn = sqlite3.connect('database.db')
    df.to_sql('records', conn, if_exists='replace', index=False)
    conn.close()




# @app.route('/download_csv')
# def download_csv():
#     output = StringIO()
#     writer = csv.writer(output)
#     output.write(u'\ufeff')  # Add UTF-8 BOM for Excel compatibility

#     # Fetch data from the database
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM records")  # Adjust this as needed
#         records = cursor.fetchall()

#         # Write header
#         writer.writerow(['Record Locator', 'First Name', 'Last Name', 'Email', 'Scanned'])  # Adjust according to your schema
#         # Write data rows
#         for row in records:
#             writer.writerow(row)

#     output.seek(0)
#     return send_file(output, mimetype='text/csv', as_attachment=True, attachment_filename='records.csv')

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
