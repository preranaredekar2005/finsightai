from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"

engine = create_engine(DATABASE_URL)

connection = engine.connect()

print("Database connected successfully!")

connection.close()