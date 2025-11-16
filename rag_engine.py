import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# --- UPDATED IMPORTS: We need JSONLoader ---
from langchain_community.document_loaders import DirectoryLoader, TextLoader, JSONLoader
# ---
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
# ▼▼▼ THIS IS THE FIX ▼▼▼
from langchain_core.runnables import RunnablePassthrough
# ▲▲▲ THIS IS THE FIX ▲▲▲
from langchain_core.output_parsers import StrOutputParser

# --- 1. LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def check_api_key():
    """Checks if the Google API key is set."""
    if "GOOGLE_API_KEY" not in os.environ or not os.environ["GOOGLE_API_KEY"]:
        print("="*50)
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        print("Please get a key from Google AI Studio.")
        print("="*50)
        return False
    return True

# ---
# ▼▼▼ THIS IS THE NEW, CORRECTED FUNCTION (v3) ▼▼▼
# ---
def create_knowledge_base(embeddings):
    """
    Loads documents from the 'knowledge_base' folder, splits them,
    and creates a FAISS vector store.
    It now correctly loads BOTH .txt and .json files.
    """
    kb_folder_path = "./knowledge_base" 
    
    if not os.path.exists(kb_folder_path) or not os.path.isdir(kb_folder_path):
        print(f"Warning: Knowledge Base folder '{kb_folder_path}' not found.")
        print("Falling back to hard-coded default documents.")
        
        documents_text = [
            "The 'prophet_weekly_v1' model is a Prophet model...",
            "The 'lightgbm_model' model is an LightGBM model...",
            "The 'lstm_v1' model is a Long Short-Term Memory (LSTM) neural network...",
            "To run a forecast, the user must first upload a CSV or Excel file...",
            "The user's data must contain a clear date or timestamp column..."
        ]
        
        try:
            vector_store = FAISS.from_texts(documents_text, embeddings)
            print("Knowledge base created successfully (using fallback).")
            return vector_store.as_retriever()
        except Exception as e:
            print(f"Error creating fallback vector store: {e}")
            return None
    
    # --- If './knowledge_base' folder *IS* found, load from it ---
    print(f"Loading documents from '{kb_folder_path}' folder...")
    try:
        # 1. Load .txt files (This way is fine)
        print("Loading .txt files...")
        txt_loader = DirectoryLoader(
            kb_folder_path, 
            glob="**/*.txt",  # Selects only .txt
            loader_cls=TextLoader,
            recursive=True,
            show_progress=True
        )
        txt_documents = txt_loader.load()
        print(f"Loaded {len(txt_documents)} .txt files.")

        # 2. Load .json files (Manual, more robust method)
        print("Loading .json files...")
        json_documents = []
        # Find all .json files in the folder and subfolders
        json_files = glob.glob(os.path.join(kb_folder_path, "**/*.json"), recursive=True)
        
        for file_path in json_files:
            try:
                # Load each file individually, forcing text conversion
                json_loader_individual = JSONLoader(
                    file_path=file_path,
                    #
                    # ▼▼▼ THIS IS THE FIX ▼▼▼
                    #
                    jq_schema='. | tojson', # Select entire object AND convert to JSON string
                    #
                    # ▲▲▲ THIS IS THE FIX ▲▲▲
                    #
                    text_content=True   # Now the content *is* text
                )
                docs = json_loader_individual.load()
                json_documents.extend(docs)
            except Exception as e:
                # This will print the error for a specific file but not crash
                print(f"Error loading file {file_path}: {e}")
                
        print(f"Loaded {len(json_documents)} .json files.")

        # 3. Load all documents
        documents = txt_documents + json_documents # Combine the lists
        
        if not documents:
            print(f"Warning: No .txt or .json documents found in '{kb_folder_path}'.")
            # Run the function again to get the fallback
            return create_knowledge_base(embeddings) 
            
        print(f"Loaded a total of {len(documents)} documents.")
        
        # 4. Split all documents into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

        # 5. Create the vector store using FAISS
        vector_store = FAISS.from_documents(chunks, embeddings)
        print("Knowledge base created successfully from all files (using FAISS).")
        return vector_store.as_retriever()
        
    except Exception as e:
        print(f"Error creating vector store from files: {e}")
        return None
# ---
# ▲▲▲ END OF THE CORRECTED FUNCTION ▲▲▲
# ---

def get_rag_chain():
    """
    Creates and returns the full RAG (Retrieval-Augmented Generation) chain.
    """
    if not check_api_key():
        return None

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-09-2025", temperature=0)
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        retriever = create_knowledge_base(embeddings)
        
        if retriever is None:
            print("Error: Failed to create retriever.")
            return None

        template = """
        You are an expert forecasting analyst agent. Your goal is to answer the user's questions.
        Use the following "Context" from the knowledge base to help answer.
        If the user asks for a model recommendation or data analysis, you MUST follow their instructions.
        If the user asks a general question, use the context to answer it.
        
        CONTEXT:
        {context}
        
        USER'S QUESTION:
        {question}
        
        YOUR ANSWER:
        """
        
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        print("RAG chain successfully built.")
        return rag_chain

    except Exception as e:
        print(f"Error building RAG chain: {e}")
        if "API key not valid" in str(e):
            print("--- PLEASE CHECK YOUR GOOGLE_API_KEY ---")
        return None

if __name__ == "__main__":
    # This allows you to test the file directly
    print("Testing RAG engine...")
    chain = get_rag_chain()
    if chain:
        print("\n--- Testing General Question ---")
        response = chain.invoke("What is the prophet_weekly_v1 model good for?")
        print(response)

