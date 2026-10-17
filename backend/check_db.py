
from app.db.session import test_database_connection


if __name__ == "__main__":
    try:
        print(test_database_connection())
    except Exception as error:
        print("Database connection failed.")
        print(f"Error: {error}")