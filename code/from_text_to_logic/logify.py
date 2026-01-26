#!/usr/bin/env python3
"""
logify.py - Text to Logic Pipeline Orchestrator

This module orchestrates the two-stage text-to-logic pipeline:
  Stage 1: Extract relation triples using OpenIE (openie_extractor.py)
  Stage 2: Convert text + triples to logic using LLM (logic_converter.py)

Supports multiple document formats: PDF, DOCX, TXT, and plain text input.
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from openie_extractor import OpenIEExtractor
from logic_converter import LogicConverter


def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from various document formats.

    Args:
        file_path: Path to document file (PDF, DOCX, TXT)

    Returns:
        Extracted text content

    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    # Plain text file
    if suffix in ['.txt', '.text']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    # PDF file
    elif suffix == '.pdf':
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF support. "
                "Install with: pip install PyMuPDF"
            )

        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)

    # DOCX file
    elif suffix in ['.docx', '.doc']:
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX support. "
                "Install with: pip install python-docx"
            )

        doc = Document(file_path)
        text_parts = [para.text for para in doc.paragraphs]
        return "\n".join(text_parts)

    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: .txt, .pdf, .docx"
        )


class LogifyConverter:
    """Orchestrates the two-stage text-to-logic conversion pipeline."""

    def __init__(self, api_key: str, model: str = "gpt-5.2", temperature: float = 0.1, reasoning_effort: str = "medium", max_tokens: int = 64000):
        """
        Initialize the pipeline with both stages.

        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: gpt-5.2 with extended thinking)
            temperature (float): Sampling temperature for LLM (default: 0.1, ignored for reasoning models)
            reasoning_effort (str): Reasoning effort for gpt-5.2/o1/o3 models (default: medium)
            max_tokens (int): Maximum tokens in response (default: 64000)
        """
        # Stage 1: OpenIE extraction
        self.extractor = OpenIEExtractor()

        # Stage 2: LLM-based logic conversion
        self.converter = LogicConverter(api_key=api_key, model=model, temperature=temperature, reasoning_effort=reasoning_effort, max_tokens = max_tokens)

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

    def save_output(self, logic_structure: Dict[str, Any], output_path: str = "logified.JSON"):
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
    parser = argparse.ArgumentParser(
        description="Convert documents/text to structured propositional logic using OpenIE + LLM",
        epilog="Supported formats: PDF (.pdf), Word (.docx), Text (.txt), or raw text string"
    )
    parser.add_argument(
        "input",
        help="Path to document file (PDF/DOCX/TXT) or raw text string"
    )
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument(
        "--model",
        default="gpt-5.2",
        help="Model to use (default: gpt-5.2). Options: gpt-5.2, o1, gpt-4o, gpt-4-turbo, etc."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature for LLM (default: 0.1, ignored for reasoning models)"
    )
    parser.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=["none", "low", "medium", "high", "xhigh"],
        help="Reasoning effort for gpt-5.2/o1/o3 models (default: medium)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=64000,
        help="Maximum tokens in response (default: 64000)"
    )
    parser.add_argument("--output", default="logified.JSON", help="Output JSON file path")

    args = parser.parse_args()

    try:
        # Determine if input is a file path or raw text
        # If it's a valid file path, extract text from document
        # Otherwise, treat as raw text string
        if os.path.exists(args.input):
            print(f"Reading document: {args.input}")
            text = extract_text_from_document(args.input)
            print(f"  ✓ Extracted {len(text)} characters")
        else:
            # Treat as raw text input
            text = args.input
            print(f"Using raw text input ({len(text)} characters)")

        # Initialize converter
        converter = LogifyConverter(
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature,
            reasoning_effort=args.reasoning_effort,
            max_tokens=args.max_tokens
        )

        # Convert text to logic
        print(f"\nConverting to logic structure...")
        print(f"  Model: {args.model}")
        print(f"  Temperature: {args.temperature}")
        print(f"  Reasoning effort: {args.reasoning_effort}")
        print(f"  Max tokens: {args.max_tokens}")
        logic_structure = converter.convert_text_to_logic(text)

        # Save output
        converter.save_output(logic_structure, args.output)

        print(f"\n✓ Conversion completed successfully!")
        print(f"  Output saved to: {args.output}")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
