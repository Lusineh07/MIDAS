# https://huggingface.co/google/flan-t5-small#TL;DR
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from transformers import pipeline

summarizer = pipeline(
    "text2text-generation",
    model="google/flan-t5-small"
)
from transformers import pipeline

# Load the model and tokenizer
summarizer = pipeline(
    "text2text-generation", 
    model="google/flan-t5-small"
)

# Example input: headline + article summary
headline = ("OpenAI releases new multimodal AI model capable of understanding images and text"
    "Google DeepMind announces breakthrough in protein-folding prediction accuracy"
    "Anthropic debuts Claude 3, an AI assistant focused on safety and transparency"
    "Microsoft integrates generative AI tools directly into Office productivity suite"
    "Meta open-sources lightweight AI model optimized for mobile devices")
summary = (
    "OpenAI introduced a next-generation model that processes both images and text, expanding the scope of AI applications across creative and analytical fields."
    "DeepMind researchers unveiled an upgraded AlphaFold system that improves protein-structure prediction and accelerates drug-discovery research."
    "Anthropic launched Claude 3, emphasizing ethical reasoning and reduced hallucination rates to advance safe conversational AI."
    "Microsoft added built-in AI copilots to Word, Excel, and PowerPoint, enabling automated content generation and data summarization features."
    "Meta announced an open-source AI model designed for smartphones and edge devices, delivering efficient on-device performance with minimal power use."
)

# Combine and format prompt for guide the model
prompt = f"Summarize this into one concise line:\nHeadline: {headline}\nSummary: {summary}\nOne-liner:"

# Generate the result
result = summarizer(
    prompt,
    max_new_tokens=25,     # keeps output short (a single sentence)
    num_beams=4,           # balances quality vs. speed
    length_penalty=1.2,
    early_stopping=True
)

# Print the generated summary
print("📰 One-liner summary:")
print(result[0]["generated_text"])
