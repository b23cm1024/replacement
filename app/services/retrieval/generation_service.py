from openai import OpenAI
import os

# We can use the OpenAI library to talk to Groq because Groq uses the same API format!
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_answer(query: str, retrieved_chunks: list) -> str:
    """
    Generates an answer using an LLM based strictly on the retrieved chunks.
    """
    if not retrieved_chunks:
        return "I could not find any relevant information to answer your question."
        
    if not os.getenv("GROQ_API_KEY"):
        return "Warning: GROQ_API_KEY is missing. Please add it to your .env file."

    # Compile the context from the chunks
    context = ""
    for idx, chunk in enumerate(retrieved_chunks):
        source_name = chunk.get('source_name', 'Unknown')
        source_type = chunk.get('source_type', 'Unknown')
        
        # Extract GitHub file name if available in metadata
        metadata = chunk.get('metadata', {})
        file_name = metadata.get('file_name')
        
        if file_name:
            chunk_text = f"\n--- Source: {source_name} | File: {file_name} (Doc Type: {source_type}) ---\n"
        else:
            chunk_text = f"\n--- Source: {source_name} (Doc Type: {source_type}) ---\n"
            
        chunk_text += f"{chunk.get('chunk_text', '')}\n"
        
        # Prevent prompt from exceeding Groq free tier limits (6000 TPM limit)
        # 12000 chars is roughly 3000 tokens.
        if len(context) + len(chunk_text) > 12000:
            break
            
        context += chunk_text

    system_prompt = (
        "You are an intelligent enterprise search assistant (WorkIQ). "
        "Use the provided document excerpts below to answer the user's question. "
        "Synthesize the information provided to give a comprehensive answer. "
        "IMPORTANT: At the end of your answer, you MUST append a 'Sources:' section listing the exact document name, document type (e.g., pdf, excel, github repo), and the specific page number(s) or file names that your answer was derived from. Page numbers are embedded in the text like [--- Page X ---].\n"
        "If the excerpts are completely unrelated and do not contain enough information to form an answer, say 'I cannot answer this based on the retrieved documents.'\n\n"
        f"CONTEXT:\n{context}"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"
