from app.database import SessionLocal
from app.services.retrieval.retrieval_service import search_documents

def run_test():
    db = SessionLocal()
    try:
        # Since we don't know exactly what's in the test PDF, 
        # let's just search for a generic term like "data" or "process"
        # or we can just try "workiq"
        query = "What is the project about?"
        print(f"Searching for: '{query}'")
        
        results = search_documents(query, db, top_k=3)
        
        if not results:
            print("No results found. Maybe the database is empty or connection failed.")
        else:
            print(f"Found {len(results)} results:")
            for idx, res in enumerate(results):
                print(f"\n--- Result {idx+1} ---")
                print(f"Score: {res['score']}")
                print(f"Source: {res['source_name']}")
                print(f"Chunk Text:\n{res['chunk_text'][:200]}...")
                
    except Exception as e:
        print(f"Error during search: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
