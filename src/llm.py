
import os
from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# 1. Detect the LLM provider
# --------------------------------------------------

def get_provider():

    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()

    if provider != "auto":
        return provider

    # Automatic detection priority
    if os.getenv("GROQ_API_KEY"):
        return "groq"

    if os.getenv("GEMINI_API_KEY"):
        return "gemini"

    if os.getenv("OPENAI_API_KEY"):
        return "openai"

    raise ValueError("No LLM API key found in .env file.")


# --------------------------------------------------
# 2. Load response model
# --------------------------------------------------

class LLMResponse:

    def __init__(self, text):
        self.text = text


# --------------------------------------------------
# 3. Shared LLM function
# --------------------------------------------------

def generate_llm_response(
    prompt,
    system_instruction=None,
    temperature=0.2,
    max_output_tokens=4000,
    response_mime_type=None
):

    provider = get_provider()

    print(f"Using LLM provider: {provider.upper()}")

    # ---------------- GROQ ----------------

    if provider == "groq":

        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found.")

        client = Groq(api_key=api_key)

        model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

        messages = []

        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        config = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_output_tokens
        }

        if response_mime_type == "application/json":
            config["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**config)

        return LLMResponse(
            response.choices[0].message.content or ""
        )

    # ---------------- GEMINI ----------------

    elif provider == "gemini":

        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        client = genai.Client(api_key=api_key)

        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        config = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens
        }

        if system_instruction:
            config["system_instruction"] = system_instruction

        if response_mime_type:
            config["response_mime_type"] = response_mime_type

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config)
        )

        return LLMResponse(response.text or "")

    # ---------------- OPENAI ----------------

    elif provider == "openai":

        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY not found.")

        client = OpenAI(api_key=api_key)

        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini"
        )

        messages = []

        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        config = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_output_tokens
        }

        if response_mime_type == "application/json":
            config["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**config)

        return LLMResponse(
            response.choices[0].message.content or ""
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )


# --------------------------------------------------
# 4. Backward-compatible function
# --------------------------------------------------

# Existing agents can continue using this function.
def generate_gemini_response(
    prompt,
    system_instruction=None,
    temperature=0.2,
    max_output_tokens=4000,
    response_mime_type=None
):

    response = generate_llm_response(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type=response_mime_type
    )

    if not response.text:
        raise RuntimeError("LLM returned an empty response.")

    return response


# --------------------------------------------------
# 5. Research report generation
# --------------------------------------------------

def generate_research_report(question, results):

    if not question or not question.strip():
        raise ValueError("Research question cannot be empty.")

    if not results:
        return "Insufficient evidence to answer this question."

    evidence_parts = []

    for result in results:

        chunk = result["chunk"]

        evidence = f"""
Source ID: {chunk['chunk_id']}
Paper ID: {chunk['paper_id']}
Paper Title: {chunk['paper_title']}
Section: {chunk['section']}
Page Number: {chunk['page_number']}

Passage:
{chunk['text']}
"""

        evidence_parts.append(evidence)

    evidence_text = "\n\n".join(evidence_parts)

    instructions = """
You are an academic research assistant.

Answer the research question using ONLY the
provided research paper evidence.

1. Use only the provided evidence.
2. Cite every factual claim using exact Source IDs.
3. Never invent citations, titles or page numbers.
4. Compare findings across papers when possible.
5. Identify conflicting evidence.
6. Clearly state uncertainty and limitations.
7. Abstain when evidence is insufficient.

Generate the report using these headings:

## 1. Direct Answer
## 2. Evidence from Research Papers
## 3. Comparison of Findings
## 4. Conflicting Evidence
## 5. Limitations and Uncertainty
## 6. Conclusion
"""

    prompt = f"""
Research Question:
{question}

Retrieved Research Evidence:
{evidence_text}

Generate the structured research report.
"""

    response = generate_llm_response(
        prompt=prompt,
        system_instruction=instructions,
        temperature=0.2,
        max_output_tokens=4000
    )

    return response.text
