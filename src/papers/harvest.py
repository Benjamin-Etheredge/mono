# This module handles the retrieval and processing of academic papers from arXiv using OAI-PMH.
# It includes functions to fetch metadata, download papers, and parse them into a structured format.

import pymilvus
from ollama import Client
import os
import requests
import time
from xml.etree import ElementTree as ET
ARXIV_OAI_URL = "http://export.arxiv.org/oai2"
from datetime import datetime, timedelta

START_DATE = os.getenv('START_DATE', '1960-01-01') 
END_DATE = os.getenv('END_DATE', datetime.now().strftime('%Y-%m-%d'))  # Current date by default
SET_NAME = os.getenv('SET_NAME', None)
# SET_NAME = os.getenv('SET_NAME', 'cs')  # Default to Computer Science Artificial Intelligence

OLLAMA_URI = os.getenv('OLLAMA_URI', 'http://ollama.k8s.lan') 
ollama_client = Client(host=OLLAMA_URI)
EMBED_MODEL = os.getenv('EMBED_MODEL', 'nomic-embed-text')

MILVUS_URI = os.getenv('MILVUS_URI', 'http://milvus.k8s.lan:80')
client = pymilvus.connections.connect(uri=MILVUS_URI)


def create_collection(colleciton_name):
    if not pymilvus.utility.has_collection(colleciton_name):
        print(f"Creating collection {colleciton_name}")
    else:
        print(f"Collection {colleciton_name} already exists")
        # delete collection
        # pymilvus.utility.drop_collection(colleciton_name)
        # print(f"Collection {colleciton_name} deleted")
        # return create_collection(colleciton_name)  # Recreate the collection
        collection = pymilvus.Collection(colleciton_name)  # Get an existing collection.
        return collection

    fields = [
        # pymilvus.FieldSchema(name="id", dtype=pymilvus.DataType.INT64, auto_id=True),
        pymilvus.FieldSchema(name="summary_embedding", dtype=pymilvus.DataType.FLOAT_VECTOR, dim=768),
        pymilvus.FieldSchema(name="title_embedding", dtype=pymilvus.DataType.FLOAT_VECTOR, dim=768),
        pymilvus.FieldSchema(name="both_embedding", dtype=pymilvus.DataType.FLOAT_VECTOR, dim=768),
        pymilvus.FieldSchema(name="title", dtype=pymilvus.DataType.VARCHAR, max_length=1024),
        pymilvus.FieldSchema(name="type", dtype=pymilvus.DataType.VARCHAR, max_length=32),
        pymilvus.FieldSchema(name="summary", dtype=pymilvus.DataType.ARRAY, element_type=pymilvus.DataType.VARCHAR, max_capacity=128, max_length=8192),
        pymilvus.FieldSchema(name="authors", dtype=pymilvus.DataType.ARRAY, element_type=pymilvus.DataType.VARCHAR, max_capacity=512, max_length=256),
        pymilvus.FieldSchema(name="subject", dtype=pymilvus.DataType.ARRAY, element_type=pymilvus.DataType.VARCHAR, max_capacity=64, max_length=256),
        pymilvus.FieldSchema(name="date", dtype=pymilvus.DataType.ARRAY, element_type=pymilvus.DataType.VARCHAR, max_capacity=256, max_length=64),
        pymilvus.FieldSchema(name="identifier", is_primary=True, dtype=pymilvus.DataType.VARCHAR, max_length=256),
        pymilvus.FieldSchema(name="identifiers", dtype=pymilvus.DataType.ARRAY, element_type=pymilvus.DataType.VARCHAR, max_capacity=128, max_length=256),
        pymilvus.FieldSchema(name="last_date_epoch", dtype=pymilvus.DataType.INT64),
    ]
    schema = pymilvus.CollectionSchema(fields, "arXiv papers")
    collection = pymilvus.Collection(colleciton_name, schema)
    index_params = {
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
        "metric_type": "L2"
    }
    collection.create_index(field_name="summary_embedding", index_params=index_params)
    collection.create_index(field_name="title_embedding", index_params=index_params)
    collection.create_index(field_name="both_embedding", index_params=index_params)
    return collection


# TODO
def insert_paper(collection, paper):
    # check if paper already exists in the collection
    existing_paper = collection.query(
        expr=f"identifier == '{paper['identifier']}'",
        output_fields=["identifier"]
    )
    if existing_paper:
        print(f"Paper with identifier {paper['identifier']} already exists. Updating record.")
        # Update the existing record
        collection.delete(expr=f"identifier == '{paper['identifier']}'")
        collection.flush()
    
    collection.insert(paper)


def generate_embedding(text):
    return ollama_client.embeddings(model=EMBED_MODEL, prompt=text)['embedding']


def generate_embedding_kwargs(record):
    title = record.get('title', '')
    summary = record.get('description', '')

    if isinstance(title, list):
        title = ' '.join(title)
    if isinstance(summary, list):
        summary = ' '.join(summary)
    
    return {
        'summary_embedding': generate_embedding(summary),
        'title_embedding': generate_embedding(title),
        'both_embedding': generate_embedding(f"{title} {summary}")
    }


def prepare_records(records):
    """
    Prepares a list of records by extracting relevant information and generating embeddings.
    Args:
       records (list): A list of OAI-PMH record dictionaries.
    Returns:
       list: A list of dictionaries containing prepared paper data.
    """
    prepared_records = []
    for record in records:
        dates = record['date'] if  isinstance(record['date'], list) else [record['date']]
        epoch_dates = [int(datetime.strptime(date, '%Y-%m-%d').timestamp()) for date in dates]
        last_date_epoch = min(epoch_dates)  # min date is how the api indexes
        
        arxiv_idenitifier = record['identifier'][0] if isinstance(record['identifier'], list) else record['identifier']

        # Example datetime: "2007-03-30"
        prepared_records.append({
            'title': record['title'],
            'authors': record['creator'] if isinstance(record['creator'], list) else [record['creator']],
            'subject': record['subject'] if isinstance(record['subject'], list) else [record['subject']],
            'summary': record['description'] if isinstance(record['description'], list) else [record['description']],
            'date': record['date'] if isinstance(record['date'], list)  else [record['date']],
            'type': record['type'],
            'identifier': arxiv_idenitifier,
            'identifiers': record['identifier'] if isinstance(record['identifier'], list) else [record['identifier']],
            'last_date_epoch': last_date_epoch,
            # TODO do we embed the title? or the summary? or both?
            **generate_embedding_kwargs(record),
            # 'embedding': generate_embedding(record['description']) if record['description'] else None,
        })
    return prepared_records


def harvest_papers(collection, set_spec, from_date=None, until_date=None):
    """
    Harvests metadata for papers from arXiv using OAI-PMH.
    Args:
       set_spec (str): The OAI-PMH set specification.
        from_date (str, optional): The start date for harvesting records. Defaults to None.
        until_date (str, optional): The end date for harvesting records. Defaults to None.
    Returns:
        list: A list of dictionaries containing metadata for each paper.
    """
    resumption_token = None
    i = 0
    while True:
        i += 1
        print(f"Fetching batch {i}...")
        response_records, resumption_token = fetch_records(set_spec, from_date, until_date, resumption_token)
        prepared_records = prepare_records(response_records) 
        for record in prepared_records:  # Print each record for debugging
            try:
                collection.upsert(record)  # Insert each record into the database
            except Exception as e:
                print(f"Error inserting record {record}: {e}")
                raise e
        print(f"Inserted {len(prepared_records)} records.")  # Print the number of inserted records
        if not resumption_token:
            print("No more records to fetch.")
            break


BASE_URL = "http://export.arxiv.org/oai2"
METADATA_PREFIX = "arXiv"
def fetch_records(set_spec=None, from_date=None, until_date=None, resumption_token=None):
    """
    Fetches a batch of records from arXiv using OAI-PMH.
    Args:
        set_spec (str): The OAI-PMH set specification.
        from_date (str, optional): The start date for harvesting records. Defaults to None.
        until_date (str, optional): The end date for harvesting records. Defaults to None.
        resumption_token (str, optional): The token used for resuming a previous request. Defaults to None.
    Returns:
        dict: A dictionary containing the batch of records and a resumption token if available.
    """
    url = f"{BASE_URL}?verb=ListRecords&metadataPrefix=oai_dc"
    # url = f"{BASE_URL}?verb=ListRecords&metadataPrefix={METADATA_PREFIX}"
    params = {}
    if set_spec:
        params["set"] = set_spec
    if from_date:
        params["from"] = from_date
    if until_date:
        params["until"] = until_date

    if resumption_token:
        # If a resumption token is provided, use it and ignore other parameters.
        url = f"{BASE_URL}?verb=ListRecords&resumptionToken={resumption_token}"
        params = {}
        print(f"Using resumption token: {resumption_token}")

    success = False
    while not success:
        response = requests.get(url, params=params)
        if response.status_code == 503:
            # Handle waiting as long as they ask
            wait_seconds = int(response.headers.get('Retry-After', 5))
            print(f"Server is busy, retrying after {wait_seconds} seconds...")
            time.sleep(wait_seconds)
        else:
            response.raise_for_status()
            success = True
    return parse_response(response.content)


def parse_response(content):
    """
    Parses the XML response from arXiv's OAI-PMH endpoint.
    Args:
        content (bytes): The XML content of the response.
    Returns:
        dict: A dictionary containing the batch of records and a resumption token if available.
    """
    root = ET.fromstring(content)
    records = []
    resumption_token = None
    for record in root.findall(".//{http://www.openarchives.org/OAI/2.0/}record"):
        metadata = record.find(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc", namespaces={'oai_dc': 'http://www.purl.org/dc/elements/1.1/'})
        if metadata is not None:
            record_dict = {}
            for element in metadata:
                tag = element.tag.split('}')[-1]
                if tag in record_dict:  # Handle multiple elements with the same tag
                    if isinstance(record_dict[tag], list):
                        record_dict[tag].append(element.text)
                    else:
                        record_dict[tag] = [record_dict[tag], element.text]
                else:
                    record_dict[tag] = element.text
            records.append(record_dict)
        else:
            print("No metadata found for record:", ET.tostring(record))
    # print("Total records parsed:", len(records))
    # print("Looking at raw record:", ET.tostring(record))
    resumption_token_element = root.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")
    if resumption_token_element is not None and resumption_token_element.text:
        resumption_token = resumption_token_element.text
        _, index = resumption_token_element.text.split('|')
        # print("Index:", index)  # This is the current index in the list of records
        resumption_token_complete_list_size = resumption_token_element.attrib.get('completeListSize', None)
        print("Complete list size:", resumption_token_complete_list_size)
        print("Got resumption token:", resumption_token)
    else:
        print("No resumption token found.")
        print("Length of records:", len(records))
    return records, resumption_token


def get_last_date(collection: pymilvus.Collection):
    """
    Fetch the last date of the most recent record in a given collection.
    """
    # Milvus makes this super hard for no reason
    collection.load()
    iterator = collection.search_iterator(
        data=[[0.0] * 768],  # Dummy data, not used for aggregation
        anns_field='summary_embedding',
        batch_size=64,
        param={"metric_type": "L2", "params": {"nprobe": 16}},
        output_fields=['last_date_epoch'],
        # limit=20_000_000,
    )

    last_time = 0
    i = 0
    while True:
        result = iterator.next()
        if not result:
            print("done")
            iterator.close()
            break
        for hit in result:
            i += 1
            print(i)
            if last_time == 0:
                last_time = hit.to_dict()['entity']['last_date_epoch']
            else:
                last_time = min(last_time, hit.to_dict()['entity']['last_date_epoch'])


    last_date = datetime.fromtimestamp(last_time)
    # Go back 7 days to be sure we don't miss anything on edges
    last_date_padded = last_date - timedelta(days=7)
    return last_date_padded.strftime('%Y-%m-%d')


if __name__ == "__main__":
    milvus_sanitized_set_name = SET_NAME.replace('.','_').replace('-','_').replace(':','_') if SET_NAME else None
    collection = create_collection(f'arxiv_{milvus_sanitized_set_name}')  # Create a collection with a timestamped name
    
    START_DATE = get_last_date(collection)
    print("Start date: ", START_DATE)
    
    # collection = create_collection(f'arxiv_{milvus_sanitized_set_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}')  # Create a collection with a timestamped name
    papers = harvest_papers(collection, SET_NAME, START_DATE, END_DATE)
