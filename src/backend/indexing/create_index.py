import os

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
import glob
from pathlib import Path
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndex
)

credential = DefaultAzureCredential()

AZURE_AI_SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
AZURE_AI_SEARCH_INDEX_NAME = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
AZURE_OPENAI_ACCOUNT = os.getenv("AZURE_OPENAI_ACCOUNT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Create a search index  
index_name = AZURE_AI_SEARCH_INDEX_NAME
index_client = SearchIndexClient(endpoint=AZURE_AI_SEARCH_ENDPOINT, credential=credential)  
fields = [
    SearchField(name="id", type=SearchFieldDataType.String, key=True, retrievable=True),  
    SearchField(name="drive_id", type=SearchFieldDataType.String, retrievable=True),
    SearchField(name="site_id", type=SearchFieldDataType.String, retrievable=True),
    SearchField(name="item_id", type=SearchFieldDataType.String, retrievable=True),
    SearchField(name="chunk", type=SearchFieldDataType.String, retrievable=True, sortable=False, filterable=False, facetable=False, analyzer_name="ja.microsoft")
]
  
# Configure the vector search configuration  
vector_search = VectorSearch(  
    algorithms=[  
        HnswAlgorithmConfiguration(name="myHnsw"),
    ],  
    profiles=[  
        VectorSearchProfile(  
            name="myHnswProfile",  
            algorithm_configuration_name="myHnsw",  
            vectorizer_name="myOpenAI",  
        )
    ],
    vectorizers=[  
        AzureOpenAIVectorizer(  
            vectorizer_name="myOpenAI",  
            kind="azureOpenAI",  
            parameters=AzureOpenAIVectorizerParameters(  
                resource_url=AZURE_OPENAI_ACCOUNT,
                deployment_name=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                model_name=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            ),
        ),  
    ], 
)
  
# Create the search index
index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)  
result = index_client.create_or_update_index(index)  
print(f"{result.name} created")

# Upload documents to the search index
markdown_directory = os.path.join(os.path.dirname(__file__), "files", "markdown")
markdown_files = glob.glob(os.path.join(markdown_directory, "*.md"))
documents = []
for file_path in markdown_files:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
        for idx, chunk in enumerate(chunks):
            documents.append({
                "id": f"{Path(file_path).stem}_{idx}",
                "drive_id": "drive_id_placeholder",
                "site_id": "site_id_placeholder",
                "item_id": "item_id_placeholder",
                "chunk": chunk
            })

search_client = SearchClient(
    endpoint=AZURE_AI_SEARCH_ENDPOINT,
    index_name=AZURE_AI_SEARCH_INDEX_NAME,
    credential=credential
)
search_client.upload_documents(documents)
