# ref: https://github.com/chroma-core/chroma/blob/main/examples/chat_with_your_documents/load_data.py
import os
import argparse

from tqdm import tqdm

import chromadb


def main(
    documents_directory: str = "docs",
    collection_name: str = "docs_collection",
    persist_directory: str = ".",
) -> None:
    # Instantiate a persistent chroma client in the persist_directory.
    # Learn more at docs.trychroma.com
    client = chromadb.PersistentClient(path=persist_directory)

    # Clean and reset the database
    # client.reset()

    # If the collection already exists, we just return it. This allows us to add more
    # data to an existing collection.
    collection = client.get_or_create_collection(name=collection_name)

    # Read all files in the data directory
    documents = []
    metadatas = []
    files = os.listdir(documents_directory)
    for filename in files:
        result = collection.get(include=["metadatas"], where={"filename": filename})
        if len(result.get('metadatas')) > 0:
            print(f"{filename} file already exists in chroma database, skip it!")
            continue
        with open(f"{documents_directory}/{filename}", "r") as file:
            for line_number, line in enumerate(
                tqdm((file.readlines()), desc=f"Reading {filename}"), 1
            ):
                # Strip whitespace and append the line to the documents list
                line = line.strip()
                # Skip empty lines
                if len(line) == 0:
                    continue
                documents.append(line)
                metadatas.append({"filename": filename, "line_number": line_number})

    count = collection.count()
    if count == 0:
        ids = [str(i) for i in range(count, count + len(documents))]
    else:
        # Seek the maximum id value and create new ids by following it
        ids_only_result = collection.get(include=[]).get('ids')
        tmp_list = [int(i) for i in ids_only_result]
        tmp_list.sort()
        id_max = tmp_list[len(tmp_list) - 1]
        ids = [str(i) for i in range(id_max + 1, id_max + 1 + len(documents))]

    print(f"Collection already contains {count} documents")

    # Load the documents in batches of 100
    for i in tqdm(
        range(0, len(documents), 100), desc="Adding documents", unit_scale=100
    ):
        collection.add(
            ids=ids[i : i + 100],
            documents=documents[i : i + 100],
            metadatas=metadatas[i : i + 100],  # type: ignore
        )

    new_count = collection.count()
    print(f"Added {new_count - count} documents")


if __name__ == "__main__":
    # Read the data directory, collection name, and persist directory
    parser = argparse.ArgumentParser(
        description="Load documents from a directory into a Chroma collection"
    )

    # Add arguments
    parser.add_argument(
        "--data_directory",
        type=str,
        default="docs",
        help="The directory where your text files are stored",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        default="docs_collection",
        help="The name of the Chroma collection",
    )
    parser.add_argument(
        "--persist_directory",
        type=str,
        default="chroma_storage",
        help="The directory where you want to store the Chroma collection",
    )

    # Parse arguments
    args = parser.parse_args()

    main(
        documents_directory=args.data_directory,
        collection_name=args.collection_name,
        persist_directory=args.persist_directory,
    )
