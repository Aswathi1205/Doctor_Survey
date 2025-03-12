from flask import Flask, request, render_template, send_file
import pandas as pd
import io

app = Flask(__name__)

# Load the dataset
data = pd.read_excel('dummy_npi_data.xlsx')
data.columns = data.columns.str.strip()  # Remove any leading/trailing spaces from column names
data['Login Time'] = pd.to_datetime(data['Login Time'])
data['Logout Time'] = pd.to_datetime(data['Logout Time'])

# Debugging: Print column names to verify
print("Dataset Columns:", data.columns.tolist())

def get_available_doctors(input_time):
    input_time = pd.to_datetime(input_time, format='%H:%M').time()
    available_doctors = data[(data['Login Time'].dt.time <= input_time) & 
                              (data['Logout Time'].dt.time >= input_time)]
    
    # Verify column name for 'Time spent' (handle case sensitivity and missing column)
    expected_columns = ['NPI', 'Speciality', 'Region', 'Time spent']
    available_columns = [col for col in expected_columns if col in available_doctors.columns]
    
    if not available_columns:
        print("No matching columns found! Available columns:", available_doctors.columns.tolist())
        return available_doctors  # Return without filtering columns if none found
    
    # Check if 'Time spent' is in the available columns before accessing it
    if 'Time spent' in available_doctors.columns:
        return available_doctors[['NPI', 'Speciality', 'Region', 'Time spent']]
    else:
        print("Column 'Time spent' is not available.")
        # Return available doctors without 'Time spent' column
        return available_doctors[['NPI', 'Speciality', 'Region']]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_doctors', methods=['POST'])
def get_doctors():
    input_time = request.form['time']
    available_doctors = get_available_doctors(input_time)
    
    # Ensure at least one row is returned
    if available_doctors.empty:
        print("No doctors available at this time.")
        return "No doctors available at the selected time. Please try a different time."
    
    # Save to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        available_doctors.to_excel(writer, index=False, sheet_name='Available Doctors')
    output.seek(0)
    
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                     as_attachment=True, download_name='available_doctors.xlsx')

if __name__ == '__main__':
    app.run(debug=True)
