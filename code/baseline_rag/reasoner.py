"""
LLM reasoning module with Chain-of-Thought prompting.

This module handles the interaction with language models for reasoning over
retrieved context. It constructs prompts using a fixed Chain-of-Thought
template, calls the LLM API with temperature=0 for deterministic outputs,
and parses responses to extract structured answers.

The reasoning is performed in a single pass without self-refinement,
distinguishing this baseline from the Logify system.
"""


def construct_prompt(query, retrieved_chunks, prompt_template):
    """
    Construct the full prompt from template, query, and retrieved context.

    Args:
        query: User query string
        retrieved_chunks: List of retrieved chunk dictionaries
        prompt_template: String template with {query} and {retrieved_chunks} placeholders

    Returns:
        Formatted prompt string ready for LLM
    """
    formatted_chunks = format_chunks(retrieved_chunks)
    prompt = prompt_template.format(query=query, retrieved_chunks=formatted_chunks)
    return prompt


def format_chunks(retrieved_chunks):
    """
    Format retrieved chunks into readable context string.

    Args:
        retrieved_chunks: List of chunk dictionaries with 'text' field

    Returns:
        Formatted string concatenating all chunk texts with separators
    """
    formatted = []
    for i, chunk in enumerate(retrieved_chunks):
        formatted.append(f"[Chunk {i+1}]\n{chunk['text']}")
    return "\n\n".join(formatted)


def call_llm(prompt, model_name, temperature=0):
    """
    Call the language model API with the constructed prompt.

    Args:
        prompt: Complete prompt string
        model_name: Name of the model to use (e.g., "gpt-4", "o1-mini")
        temperature: Sampling temperature (0 for deterministic)

    Returns:
        Raw string response from the LLM
    """
    from openai import OpenAI
    import os

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY")
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )

    return response.choices[0].message.content


def parse_response(response):
    """
    Parse LLM response to extract structured answer.

    Args:
        response: Raw LLM response string

    Returns:
        Dictionary containing:
            - 'answer': One of ['True', 'False', 'Unknown'] or
                       ['Entailed', 'Contradicted', 'NotMentioned']
            - 'reasoning': Chain-of-thought reasoning steps (if extractable)
    """
    answer = None
    reasoning = response

    response_lower = response.lower()

    for label in ['true', 'false', 'unknown', 'entailed', 'contradicted', 'notmentioned']:
        if label in response_lower:
            answer = label.capitalize()
            break

    if answer is None:
        answer = 'Unknown'

    return {'answer': answer, 'reasoning': reasoning}


def reason_with_cot(query, retrieved_chunks, model_name, prompt_template, temperature=0):
    """
    Perform end-to-end reasoning with Chain-of-Thought prompting.

    This is the main entry point for the reasoning module. It orchestrates
    prompt construction, LLM calling, and response parsing.

    Args:
        query: User query string
        retrieved_chunks: List of retrieved chunk dictionaries
        model_name: LLM model name
        prompt_template: CoT prompt template
        temperature: Sampling temperature

    Returns:
        Dictionary containing:
            - 'answer': Extracted answer
            - 'reasoning': Reasoning steps
            - 'raw_response': Full LLM response
    """
    prompt = construct_prompt(query, retrieved_chunks, prompt_template)
    raw_response = call_llm(prompt, model_name, temperature)
    parsed = parse_response(raw_response)

    return {
        'answer': parsed['answer'],
        'reasoning': parsed['reasoning'],
        'raw_response': raw_response
    }
