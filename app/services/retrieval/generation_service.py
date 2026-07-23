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
        context += f"\n--- Source: {chunk.get('source_name', 'Unknown')} ---\n"
        context += f"{chunk.get('chunk_text', '')}\n"

    system_prompt = (
        "You are an intelligent enterprise search assistant (WorkIQ). "
        "Your task is to answer the user's question based strictly on the provided document excerpts below.\n"
        "If the answer is not contained in the provided context, say 'I cannot answer this based on the retrieved documents.' "
        "Do not invent or hallucinate information.\n\n"
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
