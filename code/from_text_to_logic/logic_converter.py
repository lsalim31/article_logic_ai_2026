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

    def __init__(self, api_key: str, model: str = "gpt-5.2", temperature: float = 0.1, max_tokens: int = 4000, reasoning_effort: str = "high"):
        """
        Initialize the logic converter with API key and model.

        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: gpt-5.2)
            temperature (float): Sampling temperature for LLM (default: 0.1, ignored for reasoning models)
            max_tokens (int): Maximum tokens in response (default: 4000)
            reasoning_effort (str): Reasoning effort level for GPT-5.2/o3 models (none, low, medium, high, xhigh). Default: high
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
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

OPENIE TRIPLES:
<<<
{formatted_triples}
>>>"""

            print(f"Sending to LLM for logical structure extraction (model: {self.model})...")

            # Determine if this is a reasoning model (GPT-5.2, o3-mini, etc.)
            is_reasoning_model = self.model.startswith("gpt-5") or self.model.startswith("o3")

            # Build API call parameters based on model type
            if is_reasoning_model:
                # Reasoning models use different parameters
                api_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "developer", "content": self.system_prompt},  # Use "developer" role for GPT-5.2
                        {"role": "user", "content": combined_input}
                    ],
                    "reasoning_effort": self.reasoning_effort,  # Set reasoning effort (top-level parameter)
                    "max_completion_tokens": self.max_tokens  # Use max_completion_tokens for reasoning models
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

            response_text = response.choices[0].message.content
            if response_text is None:
                print(f"  WARNING: Response content is None. Full response: {response}")
                raise ValueError("LLM returned empty response")

            response_text = response_text.strip()
            print(f"  Response length: {len(response_text)} characters")

            # Parse the JSON response
            try:
                logic_structure = json.loads(response_text)
                return logic_structure
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON from response
                if "{" in response_text and "}" in response_text:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    json_text = response_text[json_start:json_end]
                    logic_structure = json.loads(json_text)
                    return logic_structure
                else:
                    raise ValueError(f"Failed to parse JSON response: {e}")

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
