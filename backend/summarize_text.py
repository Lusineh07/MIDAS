# https://huggingface.co/google/flan-t5-small#TL;DR
import os


def summarize_text (text, keyword):
    # Ensure that the model and tokenizer are loaded from local cache only
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # Import the Hugging Face Transformers pipeline function
    from transformers import pipeline

    # Load Hugging Face model and tokenizer
    summarizer = pipeline(
        "text2text-generation", 
        model="google/flan-t5-small"
    )

    # Combine and format prompt for guide the model
    prompt = f"Summarize these articles into one concise line focusing on the keyword{keyword}:\n{text}"

    # Generate the result
    result = summarizer(
        prompt,
        max_new_tokens=25,
        num_beams=3,
        length_penalty=1.2,
        early_stopping=True
    )

    # Return generate summary text
    return result[0]["generated_text"]
