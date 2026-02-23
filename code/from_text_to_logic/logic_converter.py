#!/usr/bin/env python3
"""


"""

import json
from typing import Dict, Any
from openai import OpenAI

from config.retrieval_config import MAX_TOKENS, TEMPERATURE_LOGIC_CONVERTER,  REASONING_EFFORT, PROMPT_EXTRACTION, TRANSLATE_MODEL

class LogicConverter:
    """Converts text + OpenIE triples to structured propositional logic using LLM."""

    def __init__(self, api_key: str, 
                 model: str = TRANSLATE_MODEL, 
                 temperature: float = TEMPERATURE_LOGIC_CONVERTER, 
                 max_tokens: int = MAX_TOKENS,
                 reasoning_effort: str = REASONING_EFFORT
                 ):
        """

        """
        # Detect OpenRouter keys and use appropriate base URL
        # OpenRouter keys start with 'sk-or-v1-'
        if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
            self.client = OpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1')
            # Prefix model with openai/ for OpenRouter
            if not model.startswith('openai/'):
                model = f'openai/{model}'
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.api_key = api_key  # Store for later reference
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the prompt file."""
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(script_dir, "..", "prompts", PROMPT_EXTRACTION)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract only the SYSTEM part (remove the INPUT FORMAT section)
                if "INPUT FORMAT" in content:
                    content = content.split("INPUT FORMAT")[0].strip()
                # Remove the "SYSTEM" header if present
                if content.startswith("SYSTEM"):
                    content = content[6:].strip()
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"[logic_converter]: System prompt file not found at {prompt_path}")

    def convert(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """

        """
        try:
            # Format the combined input for the LLM
            combined_input = f"""ORIGINAL TEXT:
            <<<
            {text}
            >>>

            RELATION TRIPLES:
            <<<
            {formatted_triples}
            >>>"""

            print(f"Sending to LLM for logical structure extraction (model: {self.model}). Prompt: {self.system_prompt}")

            # Determine if this is a reasoning model (GPT-5.x, o1, o3, etc.)
            # Check base model name (strip openai/ prefix if present for OpenRouter)
            base_model = self.model.replace("openai/", "")
            is_reasoning_model = base_model.startswith("gpt-5") or base_model.startswith("o1") or base_model.startswith("o3")


            # Build API call parameters based on model type
            if is_reasoning_model:
                # Reasoning models use different parameters
                # OpenRouter uses nested 'reasoning' object via extra_body, OpenAI uses top-level 'reasoning_effort'
                if self.api_key.startswith('sk-or-v1-') or self.api_key.startswith('sk-or-'):
                    # OpenRouter format - use extra_body for custom parameters
                    api_params = {
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": self.system_prompt + "\n\n" + combined_input}  # Combine system + user for OpenRouter
                        ],
                        "max_tokens": self.max_tokens,
                        "extra_body": {
                            "reasoning": {
                                "effort": self.reasoning_effort,
                                "enabled": True
                            }
                        }
                    }
                else:
                    # Direct OpenAI API format
                    api_params = {
                        "model": self.model,
                        "messages": [
                            {"role": "developer", "content": self.system_prompt},  # Use "developer" role for GPT-5.2
                            {"role": "user", "content": combined_input}
                        ],
                        "reasoning_effort": self.reasoning_effort,  # Top-level parameter for OpenAI
                        "max_completion_tokens": self.max_tokens
                    }
                print(f"[logic_converter] Using reasoning effort: {self.reasoning_effort}")
            else:
                api_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": combined_input}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }

            # Send to LLM with the enhanced prompt
            response = self.client.chat.completions.create(**api_params)

            # Debug: print the raw response
            print(f" [logic_converter] Response received. Parsing...")
            print(f" DEBUG - Full response object:")
            print(f"    Model: {response.model if hasattr(response, 'model') else 'N/A'}")
            print(f"    Choices: {len(response.choices) if hasattr(response, 'choices') else 0}")
            if hasattr(response, 'choices') and len(response.choices) > 0:
                print(f"    Message role: {response.choices[0].message.role if hasattr(response.choices[0].message, 'role') else 'N/A'}")
                print(f"    Content type: {type(response.choices[0].message.content)}")
                print(f"    Finish reason: {response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else 'N/A'}")
                # Check for refusal
                if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
                    print(f"    REFUSAL: {response.choices[0].message.refusal}")
            # Print full response for debugging
            print(f" [logic_converter] DEBUG - Complete response dict: {response.model_dump() if hasattr(response, 'model_dump') else str(response)}")

            response_text = response.choices[0].message.content
            if response_text is None:
                print(f"[logic_converter]  WARNING: Response content is None.")
                print(f"[logic_converter]  Full response: {response}")
                raise ValueError("[logic_converter] LLM returned empty response")

            response_text = response_text.strip()

            # Check for empty response after stripping
            if not response_text:
                print(f"[logic_converter]  ERROR: LLM returned empty response or an error after stripping whitespace.")
                print(f"[logic_converter] This may indicate API timeout, rate limiting, or model error.")
                raise ValueError("[logic_converter] LLM returned empty or a non string response. This may indicate API timeout, rate limiting, or model error.")

            print(f"[logic_converter] Response length: {len(response_text)} characters")

            # Parse the JSON response
            try:
                logic_structure = json.loads(response_text)
                if "primitive_props" not in logic_structure or "constraints" not in logic_structure:
                    raise ValueError("[logic_converter] LLM output missing required keys: primitive_props, constraints")
                for c in logic_structure.get("constraints", []):
                    if "id" not in c or "formula" not in c or "translation" not in c:
                        raise ValueError("[logic_converter] Constraint missing required fields: id, formula, translation")
                return logic_structure
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON from response
                print(f" [logic_converter] WARNING: JSON parse failed: {e}")
                print(f" [logic_converter] Attempting to extract and repair JSON...")

                # Save raw response for debugging
                debug_file = "debug_llm_response.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response_text)
                print(f"  Raw response saved to: {debug_file}")

                # Try to extract JSON from markdown code fences or other wrapping text
                # First, try to strip markdown code fences
                cleaned_text = response_text
                if response_text.strip().startswith("```"):
                    # Remove opening code fence (```json or ```)
                    lines = response_text.strip().split('\n')
                    if lines[0].startswith("```"):
                        lines = lines[1:]  # Remove first line
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]  # Remove last line
                    cleaned_text = '\n'.join(lines)

                    # Try parsing cleaned text
                    try:
                        logic_structure = json.loads(cleaned_text)
                        print(f"  Successfully extracted JSON from markdown code fence")
                        return logic_structure
                    except json.JSONDecodeError:
                        pass  # Fall through to bracket extraction

                # Fallback: extract between first { and last }
                if "{" in cleaned_text and "}" in cleaned_text:
                    json_start = cleaned_text.find("{")
                    json_end = cleaned_text.rfind("}") + 1
                    json_text = cleaned_text[json_start:json_end]
                    try:
                        logic_structure = json.loads(json_text)
                        return logic_structure
                    except json.JSONDecodeError as e2:
                        print(f"[logic_converter] Failed to extract valid JSON: {e2}")
                        raise ValueError(f"[logic_converter] Failed to parse JSON response: {e}. Raw response saved to {debug_file}")
                else:
                    raise ValueError(f"[logic_converter] Failed to parse JSON response: {e}. Raw response saved to {debug_file}")

        except Exception as e:
            raise RuntimeError(f"[logic_converter] Error in LLM conversion: {e}")

    def save_output(self, logic_structure: Dict[str, Any], output_path: str = "logified.JSON"):
        """


        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logic_structure, f, indent=2, ensure_ascii=False)
        print(f"[logic_converter] Output saved to {output_path}")
