import pymysql.cursors

def get_connection():
    """Establish and return a database connection."""
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="tech_store",
        cursorclass=pymysql.cursors.DictCursor
    )
