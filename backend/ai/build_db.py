from vector_db import build_vector_database


count = build_vector_database()

print("Vector database created successfully.")
print(f"Indexed services: {count}")