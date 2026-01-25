#!/usr/bin/env python3
"""
logify2.py - Text to Logic Pipeline Orchestrator

This module orchestrates the two-stage text-to-logic pipeline:
  Stage 1: Extract relation triples using OpenIE (openie_extractor.py)
  Stage 2: Convert text + triples to logic using LLM (logic_converter.py)
"""

import json
import os
import argparse
from typing import Dict, Any

from openie_extractor import OpenIEExtractor
from logic_converter import LogicConverter


class LogifyConverter2:
    """Orchestrates the two-stage text-to-logic conversion pipeline."""

    def __init__(self, api_key: str, model: str = "gpt-5.2", reasoning_effort: str = "high"):
        """
        Initialize the pipeline with both stages.

        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: gpt-5.2)
            reasoning_effort (str): Reasoning effort for GPT-5.2/o3 models (default: high)
        """
        # Stage 1: OpenIE extraction
        self.extractor = OpenIEExtractor()

        # Stage 2: LLM-based logic conversion
        self.converter = LogicConverter(api_key=api_key, model=model, reasoning_effort=reasoning_effort)

    def convert_text_to_logic(self, text: str) -> Dict[str, Any]:
        """
        Convert input text to structured logic using the two-stage pipeline.

        Args:
            text (str): Input text to convert

        Returns:
            Dict[str, Any]: JSON structure with primitive props, hard/soft constraints
        """
        # Stage 1: Extract OpenIE triples
        openie_triples = self.extractor.extract_triples(text)
        formatted_triples = self.extractor.format_triples_json(openie_triples, indent=-1)

        # Stage 2: Convert to logic using LLM
        logic_structure = self.converter.convert(text, formatted_triples)

        return logic_structure

    def save_output(self, logic_structure: Dict[str, Any], output_path: str = "logified2.JSON"):
        """
        Save the logic structure to a JSON file.

        Args:
            logic_structure (Dict[str, Any]): The converted logic structure
            output_path (str): Path to save the JSON file
        """
        self.converter.save_output(logic_structure, output_path)

    def close(self):
        """Clean up resources from both stages."""
        self.extractor.close()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()


def main():
    """Main function to handle command line usage."""
    parser = argparse.ArgumentParser(description="Convert text to structured propositional logic using OpenIE + LLM")
    parser.add_argument("input_text", help="Input text to convert (or path to text file)")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument("--model", default="gpt-5.2", help="Model to use (default: gpt-5.2)")
    parser.add_argument("--reasoning-effort", default="high", help="Reasoning effort for GPT-5.2/o3 models: none, low, medium, high, xhigh (default: high)")
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
        converter = LogifyConverter2(api_key=args.api_key, model=args.model, reasoning_effort=args.reasoning_effort)

        # Convert text to logic
        print(f"Converting text using model: {args.model} (reasoning effort: {args.reasoning_effort})")
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