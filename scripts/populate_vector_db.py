# scripts/populate_vector_db.py
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json


class ExperienceIndexer:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text", base_url="http://localhost:11434"
        )
        self.vector_store = Chroma(
            collection_name="experience",
            embedding_function=self.embeddings,
            persist_directory="./data/embeddings/chroma_db",
        )

    def index_projects(self, projects_file):
        with open(projects_file, "r") as f:
            projects = json.load(f)

        documents = []
        for project in projects:
            doc = f"""
            Project: {project['name']}
            Description: {project['description']}
            Technologies: {', '.join(project['technologies'])}
            Role: {project['role']}
            Duration: {project['duration']}
            Key Achievements: {' '.join(project['achievements'])}
            """
            documents.append(doc)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = text_splitter.create_documents(documents)
        self.vector_store.add_documents(splits)
