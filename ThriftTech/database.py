# import the libraries we need to connect to sql server database
import os
import pyodbc

def get_db_connection():
    """
    figure out how to connect to our database using different methods
    tries environment variables first, then local files, then default database
    this makes it easy for different people to run the project on their computers
    """

    # first check if someone set a custom connection string in environment variables
    conn_str = os.getenv('THRIFTTECH_SQLSERVER_CONN')

    # if no custom connection, try to find a database file in the project folder
    if not conn_str:
        # let people override where the database file is located
        mdf_override = os.getenv('THRIFTTECH_MDF_PATH')
        project_root = os.path.dirname(os.path.abspath(__file__))
        candidate_paths = []
        if mdf_override:
            candidate_paths.append(mdf_override)
        # look for TTDb.mdf in the main project folder
        candidate_paths.append(os.path.join(project_root, 'TTDb.mdf'))
        # or maybe it's in a db subfolder
        candidate_paths.append(os.path.join(project_root, 'db', 'TTDb.mdf'))

        # check each possible location for the database file
        for mdf_path in candidate_paths:
            if os.path.exists(mdf_path):
                # found a database file, so connect directly to it
                conn_str = (
                    r'DRIVER={ODBC Driver 17 for SQL Server};'
                    r'SERVER=(localdb)\MSSQLLocalDB;'
                    f'AttachDbFilename={mdf_path};'
                    r'Trusted_Connection=yes;'
                )
                break

    # if we still don't have a connection, use the default database name
    if not conn_str:
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=(localdb)\MSSQLLocalDB;'
            r'DATABASE=TTDb;'
            r'Trusted_Connection=yes;'
        )

    # actually connect to the database and return the connection
    return pyodbc.connect(conn_str)