import sqlite3

def show_rows(table_name: str, database_cursor: sqlite3.Cursor):
    print(table_name)
    database_cursor.execute(f"SELECT * FROM {table_name}")
    rows = database_cursor.fetchall()
    for row in rows:
        print(row)


# Connect to the database
connection = sqlite3.connect('parking_db.sqlite')
cursor = connection.cursor()

# Query to fetch all data from the aktualne_wjazdy table
show_rows("aktualne_wjazdy", cursor)
show_rows("archiwum", cursor)

# Close the connection
connection.close()
