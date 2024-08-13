import os
import sys
import argparse
import chromadb

from tqdm import tqdm
from misc import param_init

params = param_init()
persist_directory = params['chromadb'].get('persist_directory')
client = chromadb.PersistentClient(path=persist_directory)

# Get the collection
collection_name = params['chromadb'].get('collection_name')
collection = client.get_collection(name=collection_name)

documents_directory = params['chromadb'].get('documents_directory')


def update(doc_files: str):
    for doc_file in doc_files.split(','):
        result = collection.get(include=["metadatas"], where={"filename": doc_file})
        if len(result.get('metadatas')) == 0:
            print(f"{doc_file} file doesn't exist in chroma database!")
            continue

        tmp_list = [int(i) for i in result.get('ids')]
        tmp_list.sort()
        ids_list = [str(i) for i in tmp_list]

        documents = [] 
        metadatas = []
        with open(f"{documents_directory}/{doc_file}", "r") as file:
            for line_number, line in enumerate(
                tqdm((file.readlines()), desc=f"Reading {doc_file}"), 1
            ):
                # Strip whitespace and append the line to the documents list
                line = line.strip()
                # Skip empty lines
                if len(line) == 0:
                    continue
                documents.append(line)
                metadatas.append({"filename": doc_file, "line_number": line_number})

        if len(documents) == len(ids_list):
            # No change about the lines in the file
            collection.update(ids=ids_list, documents=documents)
        else:
            # If the lines have been increased or decreased in the file,
            # delete the original file first and then add the new one
            collection.delete(where={"filename": doc_file})

            # Seek the maximum id value and create new ids by following it
            ids_only_result = collection.get(include=[]).get('ids')
            tmp_list = [int(i) for i in ids_only_result]
            tmp_list.sort()
            id_max = tmp_list[len(tmp_list) - 1]
            ids = [str(i) for i in range(id_max + 1, id_max + 1 + len(documents))]
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"Updated {doc_file} file!")

def delete(doc_files: str):
    for doc_file in doc_files.split(','):
        result = collection.get(include=["metadatas"], where={"filename": doc_file})
        if len(result.get('metadatas')) == 0:
            print(f"{doc_file} file doesn't exist in chroma database!")
            continue
        collection.delete(where={"filename": doc_file})
        print(f"{doc_file} file has been deleted!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Modify document files from a Chroma collection"
    )

    # Add arguments
    parser.add_argument(
        "-u",
        "--update",
        type=str,
        default=None,
        help="The document files (comma-delimited format) you want to update in collection",
    )
    parser.add_argument(
        "-d",
        "--delete",
        type=str,
        default=None,
        help="The document files (comma-delimited format) you want to delete in collection",
    )

    # Parse arguments
    args = parser.parse_args()
    
    if args.update is None and args.delete is None:
        print("The parameter is insufficient!")
        sys.exit(0)
    elif args.update:
        update(args.update)
    elif args.delete:
        delete(args.delete)
