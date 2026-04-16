import pymysql
from config import Config

def get_db_connection():
    """
    Create and return a database connection
    """
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=True):
    """
    Execute a query and return results
    
    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit transaction (for INSERT/UPDATE/DELETE)
    
    Returns:
        Result based on fetch parameters or lastrowid for INSERT
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
                return result
            elif fetch_all:
                result = cursor.fetchall()
                return result
            else:
                if commit:
                    connection.commit()
                return cursor.lastrowid
    except Exception as e:
        connection.rollback()
        print(f"Query execution error: {e}")
        raise
    finally:
        connection.close()

def call_procedure(proc_name, params):
    """
    Call a stored procedure
    
    Args:
        proc_name: Name of the stored procedure
        params: List of parameters
    
    Returns:
        Procedure results
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc(proc_name, params)
            
            # Fetch all result sets
            results = []
            while True:
                result = cursor.fetchall()
                if result:
                    results.append(result)
                if not cursor.nextset():
                    break
            
            connection.commit()
            return results if len(results) > 1 else results[0] if results else None
    except Exception as e:
        connection.rollback()
        print(f"Procedure execution error: {e}")
        raise
    finally:
        connection.close()

def test_connection():
    """Test database connection"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        connection.close()
        return True, "Database connection successful!"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"