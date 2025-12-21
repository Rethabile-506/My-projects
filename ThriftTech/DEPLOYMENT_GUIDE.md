# ThriftTech - Deployment Guide

### 1. **Python 3.10 or newer**
- Download from: https://python.org
- Make sure "Add Python to PATH" is checked during installation

### 2. **SQL Server LocalDB** (Windows only)
- Download: SQL Server Express with LocalDB
- OR install SQL Server Developer Edition (free)
- This provides the (localdb)\MSSQLLocalDB instance your app uses

### 3. **ODBC Driver 17 for SQL Server**
- Download from Microsoft's website
- Required for pyodbc to connect to SQL Server
- Usually comes with SQL Server installation, but may need separate download

## Setup instructions for the recipient:

### Step 1: Extract and navigate
```powershell
# Extract the zip file
cd path\to\ThriftTech
```

### Step 2: Create virtual environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.\.venv\Scripts\activate
```

### Step 3: Install Python dependencies
```powershell
# Install all required packages
pip install -r requirements.txt
```

### Step 4: Set up database
The app will automatically use the included database files (TTDb.mdf)  in the db/ folder

**Alternative: If database files don't work:**
```powershell
# Create fresh database using SQL script
sqlcmd -S (localdb)\MSSQLLocalDB -i .\TTDb.sql
```

### Step 5: Run the application
```powershell
# Make sure virtual environment is active
python app.py
```

Then open browser and go to: http://127.0.0.1:5000
