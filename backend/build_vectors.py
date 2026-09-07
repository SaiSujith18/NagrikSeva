from ai.vector_db import build_vector_database


if __name__ == "__main__":

    count = build_vector_database()

    print(
        "Vector database built successfully."
    )

    print(
        f"Total documents: {count}"
    )