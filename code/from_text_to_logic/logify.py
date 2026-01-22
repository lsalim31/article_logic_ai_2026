#!/usr/bin/env python3
"""
logify.py - Text to Logic Converter

This module converts natural language text to structured propositional logic
using an LLM call with a specialized system prompt.
"""

import json
import os
import argparse
from typing import Dict, Any, Optional
from openai import OpenAI


class LogifyConverter:
    """Converts text to logic using LLM with modular model selection."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the converter with API key and model.

        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: gpt-4)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the prompt file."""
        prompt_path = "/workspace/repo/code/prompts/prompt_logify"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract only the SYSTEM part (remove the INPUT USER TEXT section)
                if "INPUT USER TEXT" in content:
                    content = content.split("INPUT USER TEXT")[0].strip()
                # Remove the "SYSTEM" header if present
                if content.startswith("SYSTEM"):
                    content = content[6:].strip()
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"System prompt file not found at {prompt_path}")

    def convert_text_to_logic(self, text: str) -> Dict[str, Any]:
        """
        Convert input text to structured logic using the LLM.

        Args:
            text (str): Input text to convert

        Returns:
            Dict[str, Any]: JSON structure with primitive props, hard/soft constraints
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=4000   # Sufficient for complex logic structures
            )

            response_text = response.choices[0].message.content.strip()

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

    def save_output(self, logic_structure: Dict[str, Any], output_path: str = "logified.JSON"):
        """
        Save the logic structure to a JSON file.

        Args:
            logic_structure (Dict[str, Any]): The converted logic structure
            output_path (str): Path to save the JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logic_structure, f, indent=2, ensure_ascii=False)
        print(f"Output saved to {output_path}")


def main():
    """Main function to handle command line usage."""
    parser = argparse.ArgumentParser(description="Convert text to structured propositional logic")
    parser.add_argument("input_text", help="Input text to convert (or path to text file)")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument("--model", default="gpt-4", help="Model to use (default: gpt-4)")
    parser.add_argument("--output", default="logified.JSON", help="Output JSON file path")
    parser.add_argument("--file", action="store_true", help="Treat input_text as file path")

    args = parser.parse_args()

    # Get input text
    if args.file:
        if not os.path.exists(args.input_text):
            print(f"Error: Input file '{args.input_text}' not found")
            return 1
        with open(args.input_text, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = args.input_text

    try:
        # Initialize converter
        converter = LogifyConverter(api_key=args.api_key, model=args.model)

        # Convert text to logic
        print(f"Converting text using model: {args.model}")
        logic_structure = converter.convert_text_to_logic(text)

        # Save output
        converter.save_output(logic_structure, args.output)

        print("Conversion completed successfully!")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())