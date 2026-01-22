#!/usr/bin/env python3
"""
logify2.py - Enhanced Text to Logic Converter with OpenIE

This module converts natural language text to structured propositional logic
using OpenIE preprocessing followed by an LLM call with a specialized system prompt.
"""

import json
import os
import argparse
import time
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
from openie import StanfordOpenIE


class LogifyConverter2:
    """Enhanced converter that uses OpenIE preprocessing before LLM conversion."""

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

        # Initialize Stanford OpenIE
        print("Initializing Stanford OpenIE...")
        self.openie = StanfordOpenIE()
        print("OpenIE initialization complete.")

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

    def extract_openie_triples(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract OpenIE relation triples from the input text.

        Args:
            text (str): Input text to extract relations from

        Returns:
            List[Dict[str, Any]]: List of relation triples with confidence scores
        """
        print("Extracting OpenIE triples...")
        try:
            # Use Stanford OpenIE to extract triples
            triples_raw = self.openie.annotate(text)

            triples = []
            for triple in triples_raw:
                # Parse the triple format - Stanford OpenIE returns structured data
                if isinstance(triple, dict):
                    triples.append({
                        'subject': triple.get('subject', ''),
                        'predicate': triple.get('relation', ''),
                        'object': triple.get('object', ''),
                        'confidence': triple.get('confidence', 1.0)
                    })
                elif isinstance(triple, tuple) and len(triple) >= 3:
                    # Handle tuple format (subject, relation, object)
                    triples.append({
                        'subject': str(triple[0]).strip(),
                        'predicate': str(triple[1]).strip(),
                        'object': str(triple[2]).strip(),
                        'confidence': 1.0  # Default confidence if not provided
                    })
                else:
                    # Handle string format if returned
                    parts = str(triple).split('\t')
                    if len(parts) >= 3:
                        triples.append({
                            'subject': parts[0].strip(),
                            'predicate': parts[1].strip(),
                            'object': parts[2].strip(),
                            'confidence': float(parts[3]) if len(parts) > 3 else 1.0
                        })

            print(f"Extracted {len(triples)} OpenIE triples")
            return triples

        except Exception as e:
            print(f"Warning: OpenIE extraction failed: {e}")
            print("Continuing without OpenIE preprocessing...")
            return []

    def format_triples_for_prompt(self, triples: List[Dict[str, Any]]) -> str:
        """
        Format OpenIE triples for inclusion in the LLM prompt.

        Args:
            triples (List[Dict[str, Any]]): List of relation triples

        Returns:
            str: Formatted string of triples
        """
        if not triples:
            return "No OpenIE triples extracted."

        formatted_lines = []
        for triple in triples:
            line = f"{triple['subject']}\t{triple['predicate']}\t{triple['object']}\t{triple['confidence']:.4f}"
            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def convert_text_to_logic(self, text: str) -> Dict[str, Any]:
        """
        Convert input text to structured logic using OpenIE + LLM.

        Args:
            text (str): Input text to convert

        Returns:
            Dict[str, Any]: JSON structure with primitive props, hard/soft constraints
        """
        try:
            # Step 1: Extract OpenIE triples
            openie_triples = self.extract_openie_triples(text)
            formatted_triples = self.format_triples_for_prompt(openie_triples)

            # Step 2: Format the combined input for the LLM
            combined_input = f"""ORIGINAL TEXT:
<<<
{text}
>>>

OPENIE TRIPLES:
<<<
{formatted_triples}
>>>"""

            print("Sending to LLM for logical structure extraction...")

            # Step 3: Send to LLM with the enhanced prompt
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": combined_input}
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

    def __del__(self):
        """Clean up OpenIE resources."""
        if hasattr(self, 'openie'):
            try:
                self.openie.close()
            except:
                pass


def main():
    """Main function to handle command line usage."""
    parser = argparse.ArgumentParser(description="Convert text to structured propositional logic using OpenIE + LLM")
    parser.add_argument("input_text", help="Input text to convert (or path to text file)")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument("--model", default="gpt-4", help="Model to use (default: gpt-4)")
    parser.add_argument("--output", default="logified2.JSON", help="Output JSON file path")
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
        converter = LogifyConverter2(api_key=args.api_key, model=args.model)

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