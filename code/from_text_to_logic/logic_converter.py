#!/usr/bin/env python3
"""
logic_converter.py - LLM-Based Logic Structure Extractor

This module handles Stage 2 of the text-to-logic pipeline:
converting natural language text (augmented with OpenIE triples) into
structured propositional logic using an LLM.
"""

import json
from typing import Dict, Any
from openai import OpenAI


class LogicConverter:
    """Converts text + OpenIE triples to structured propositional logic using LLM."""

    def __init__(self, api_key: str, model: str = "gpt-5.2", temperature: float = 0.1, max_tokens: int = 32000, reasoning_effort: str = "xhigh"):
        """
        Initialize the logic converter with API key and model.

        Args:
            api_key (str): OpenAI API key (or OpenRouter key starting with sk-or-)
            model (str): Model to use (default: gpt-5.2)
            temperature (float): Sampling temperature for LLM (default: 0.1, ignored for reasoning models)
            max_tokens (int): Maximum tokens in response (default: 4000)
            reasoning_effort (str): Reasoning effort level for GPT-5.2/o3 models (none, low, medium, high, xhigh). Default: xhigh
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
        prompt_path = "/workspace/repo/code/prompts/prompt_logify2"
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
            raise FileNotFoundError(f"System prompt file not found at {prompt_path}")

    def convert(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Convert input text to structured logic using OpenIE triples and LLM.

        Args:
            text (str): Original natural language text
            formatted_triples (str): Pre-formatted OpenIE triples (tab-separated)

        Returns:
            Dict[str, Any]: JSON structure with primitive props, hard/soft constraints
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

            print(f"Sending to LLM for logical structure extraction (model: {self.model})...")

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
                print(f"  Using reasoning effort: {self.reasoning_effort}")
            else:
                # Standard models (gpt-4o, gpt-4-turbo, etc.)
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
            print(f"  Response received. Parsing...")
            print(f"  DEBUG - Full response object:")
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
            print(f"  DEBUG - Complete response dict: {response.model_dump() if hasattr(response, 'model_dump') else str(response)}")

            response_text = response.choices[0].message.content
            if response_text is None:
                print(f"  WARNING: Response content is None.")
                print(f"  Full response: {response}")
                raise ValueError("LLM returned empty response")

            response_text = response_text.strip()
            print(f"  Response length: {len(response_text)} characters")

            # Parse the JSON response
            try:
                logic_structure = json.loads(response_text)
                return logic_structure
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON from response
                print(f"  WARNING: JSON parse failed: {e}")
                print(f"  Attempting to extract and repair JSON...")

                # Save raw response for debugging
                debug_file = "debug_llm_response.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response_text)
                print(f"  Raw response saved to: {debug_file}")

                if "{" in response_text and "}" in response_text:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    json_text = response_text[json_start:json_end]
                    try:
                        logic_structure = json.loads(json_text)
                        return logic_structure
                    except json.JSONDecodeError as e2:
                        print(f"  Failed to extract valid JSON: {e2}")
                        raise ValueError(f"Failed to parse JSON response: {e}. Raw response saved to {debug_file}")
                else:
                    raise ValueError(f"Failed to parse JSON response: {e}. Raw response saved to {debug_file}")

        except Exception as e:
            raise RuntimeError(f"Error in LLM conversion: {e}")

    def save_output(self, logic_structure: Dict[str, Any], output_path: str = "logified2.JSON"):
        """
        Save the logic structure to a JSON file.

        Args:
            logic_structure (Dict[str, Any]): The converted logic structure
            output_path (str): Path to save the JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logic_structure, f, indent=2, ensure_ascii=False)
        print(f"Output saved to {output_path}")
