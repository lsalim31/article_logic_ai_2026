#!/usr/bin/env python3
"""
Demo script for logify2.py without requiring OpenAI API key.
Shows the OpenIE extraction and prompt formatting.
"""

import json
from logify2 import LogifyConverter2


class MockLogifyConverter2(LogifyConverter2):
    """Mock version that doesn't call OpenAI API."""

    def __init__(self):
        # Skip OpenAI initialization
        self.system_prompt = self._load_system_prompt()

        # Initialize spaCy for relation extraction
        print("Initializing spaCy for relation extraction...")
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("spaCy initialization complete.")
        except OSError:
            print("Warning: spaCy model not found. Please install with: python3 -m spacy download en_core_web_sm")
            raise

    def convert_text_to_logic(self, text: str) -> dict:
        """Demo version that shows the process but returns mock results."""
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

        print("=" * 60)
        print("FORMATTED INPUT FOR LLM:")
        print("=" * 60)
        print(combined_input)
        print("=" * 60)

        # Return a mock result showing the structure
        return {
            "demo_note": "This is a demo without actual LLM call",
            "original_text": text,
            "extracted_triples": openie_triples,
            "formatted_input": combined_input,
            "system_prompt_preview": self.system_prompt[:500] + "...",
        }


def main():
    """Test with Alice example."""
    alice_text = """Alice is a student who loves mathematics. If Alice studies hard, she will pass the exam. Alice usually studies hard, but sometimes she gets distracted by social media. When Alice is focused, she always completes her homework. Alice's professor recommends that students attend office hours if they want to excel. Alice prefers studying in the library because it is quiet there."""

    print("Testing logify2 with Alice example:")
    print("=" * 60)
    print("INPUT TEXT:")
    print(alice_text)
    print("=" * 60)

    try:
        # Initialize mock converter
        converter = MockLogifyConverter2()

        # Process the text
        result = converter.convert_text_to_logic(alice_text)

        print("\nEXTRACTED OPENIE TRIPLES:")
        print("-" * 40)
        for i, triple in enumerate(result['extracted_triples'], 1):
            print(f"{i}. Subject: {triple['subject']}")
            print(f"   Predicate: {triple['predicate']}")
            print(f"   Object: {triple['object']}")
            print(f"   Confidence: {triple['confidence']}")
            print()

        # Save demo output
        with open('/workspace/repo/artifacts/logify2_demo_output.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("Demo output saved to: /workspace/repo/artifacts/logify2_demo_output.json")

    except Exception as e:
        print(f"Error in demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()