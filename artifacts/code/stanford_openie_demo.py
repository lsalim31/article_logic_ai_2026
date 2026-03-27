#!/usr/bin/env python3
"""
Stanford OpenIE Demo for logify2.py
Shows the complete Stanford OpenIE + Enhanced LLM Pipeline
"""

import json
from logify2 import LogifyConverter2


class StanfordOpenIEMockConverter(LogifyConverter2):
    """Mock version that shows Stanford OpenIE extraction without LLM call."""

    def __init__(self):
        # Skip OpenAI initialization but keep Stanford OpenIE
        self.system_prompt = self._load_system_prompt()

        # Initialize Stanford OpenIE
        print("Initializing Stanford OpenIE...")
        try:
            from openie import StanfordOpenIE
            self.openie = StanfordOpenIE()
            print("Stanford OpenIE initialization complete.")
        except Exception as e:
            print(f"Error initializing Stanford OpenIE: {e}")
            raise RuntimeError(f"Failed to initialize Stanford OpenIE: {e}")

    def convert_text_to_logic(self, text: str) -> dict:
        """Demo version showing Stanford OpenIE extraction and prompt formatting."""
        # Step 1: Extract Stanford OpenIE triples
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

        print("=" * 80)
        print("STANFORD OPENIE EXTRACTION COMPLETE")
        print("=" * 80)
        print(f"Extracted {len(openie_triples)} relation triples:")
        print()

        # Group triples by subject for better readability
        subject_groups = {}
        for triple in openie_triples:
            subj = triple['subject']
            if subj not in subject_groups:
                subject_groups[subj] = []
            subject_groups[subj].append(triple)

        for subject, triples in subject_groups.items():
            print(f"Subject: {subject}")
            for triple in triples:
                print(f"  → {triple['predicate']} → {triple['object']} [conf: {triple['confidence']:.3f}]")
            print()

        print("=" * 80)
        print("FORMATTED INPUT FOR LLM")
        print("=" * 80)
        print(combined_input)
        print("=" * 80)

        # Simulate enhanced logical structure (what the LLM would produce)
        enhanced_result = self._simulate_enhanced_llm_response(text, openie_triples)

        return {
            "demo_note": "Stanford OpenIE + Enhanced LLM Pipeline Demo",
            "original_text": text,
            "openie_triples_count": len(openie_triples),
            "extracted_triples": openie_triples,
            "formatted_input": combined_input,
            "simulated_logic_structure": enhanced_result
        }

    def _simulate_enhanced_llm_response(self, text: str, triples: list) -> dict:
        """Simulate what the enhanced LLM would produce with Stanford OpenIE support."""

        # Extract key information from Stanford OpenIE triples
        alice_actions = [t for t in triples if 'Alice' in t['subject']]
        conditional_relations = [t for t in triples if 'will' in t['predicate'] or 'if' in t['object']]
        location_relations = [t for t in triples if 'library' in t['object'] or 'office hours' in t['object']]

        return {
            "primitive_props": [
                {
                    "id": "P_1",
                    "translation": "Alice is a student",
                    "evidence": "First sentence: 'Alice is a student'",
                    "explanation": "Basic identity statement about Alice",
                    "stanford_openie_support": "('Alice'; 'is'; 'student') - directly extracted"
                },
                {
                    "id": "P_2",
                    "translation": "Alice loves mathematics",
                    "evidence": "First sentence: 'who loves mathematics'",
                    "explanation": "Alice's preference for mathematics from relative clause",
                    "stanford_openie_support": "Inferred from relative clause structure"
                },
                {
                    "id": "P_3",
                    "translation": "Alice studies hard",
                    "evidence": "Multiple mentions of studying behavior",
                    "explanation": "Core study behavior proposition",
                    "stanford_openie_support": "Referenced in conditional triples about studying"
                },
                {
                    "id": "P_4",
                    "translation": "Alice passes the exam",
                    "evidence": "Conditional statement outcome",
                    "explanation": "Exam outcome proposition",
                    "stanford_openie_support": f"Multiple triples: {[t for t in triples if 'pass' in t['predicate']]}"
                },
                {
                    "id": "P_5",
                    "translation": "Alice completes her homework",
                    "evidence": "When focused statement",
                    "explanation": "Homework completion behavior",
                    "stanford_openie_support": f"Direct extraction: {[t for t in triples if 'completes' in t['predicate']]}"
                },
                {
                    "id": "P_6",
                    "translation": "Alice is focused",
                    "evidence": "Conditional context",
                    "explanation": "Mental state proposition",
                    "stanford_openie_support": f"Direct extraction: {[t for t in triples if t['subject'] == 'Alice' and 'focused' in t['object']]}"
                },
                {
                    "id": "P_7",
                    "translation": "Students attend office hours",
                    "evidence": "Professor recommendation",
                    "explanation": "General student behavior",
                    "stanford_openie_support": f"Multiple office hours triples: {len([t for t in triples if 'office hours' in t['object']])}"
                },
                {
                    "id": "P_8",
                    "translation": "Alice prefers studying in the library",
                    "evidence": "Last sentence preference statement",
                    "explanation": "Location preference for studying",
                    "stanford_openie_support": f"Direct extraction: {[t for t in triples if 'studying' in t['predicate'] and 'library' in t['object']]}"
                },
                {
                    "id": "P_9",
                    "translation": "The library is quiet",
                    "evidence": "Causal explanation for preference",
                    "explanation": "Environmental characteristic",
                    "stanford_openie_support": f"Direct extraction: {[t for t in triples if 'quiet' in t['object']]}"
                }
            ],
            "hard_constraints": [
                {
                    "id": "H_1",
                    "formula": "P_3 ⟹ P_4",
                    "translation": "If Alice studies hard, then she passes the exam",
                    "evidence": "Explicit conditional statement",
                    "reasoning": "Direct conditional with 'if...then' structure",
                    "stanford_openie_support": f"Conditional triples: {[t for t in triples if 'will pass' in t['predicate']]}"
                },
                {
                    "id": "H_2",
                    "formula": "P_6 ⟹ P_5",
                    "translation": "When Alice is focused, she always completes homework",
                    "evidence": "Universal quantifier 'always'",
                    "reasoning": "Strong conditional with 'always' indicator",
                    "stanford_openie_support": f"Focus-homework triples: {[t for t in triples if 'always completes' in t['predicate']]}"
                },
                {
                    "id": "H_3",
                    "formula": "P_8 ⟹ P_9",
                    "translation": "Alice prefers library because it is quiet",
                    "evidence": "Causal 'because' relationship",
                    "reasoning": "Explicit causal connection",
                    "stanford_openie_support": f"Preference-quiet triples: {len([t for t in triples if 'library' in t['object'] or 'quiet' in t['object']])}"
                }
            ],
            "soft_constraints": [
                {
                    "id": "S_1",
                    "formula": "P_3",
                    "translation": "Alice usually studies hard",
                    "evidence": "Frequency adverb 'usually'",
                    "reasoning": "High probability indicated by 'usually'",
                    "weight": 0.8,
                    "stanford_openie_support": "Frequency qualifier in original text"
                },
                {
                    "id": "S_2",
                    "formula": "¬P_6",
                    "translation": "Alice sometimes gets distracted",
                    "evidence": "Frequency adverb 'sometimes'",
                    "reasoning": "Moderate probability of distraction",
                    "weight": 0.3,
                    "stanford_openie_support": "Implicit from study behavior patterns"
                },
                {
                    "id": "S_3",
                    "formula": "P_7",
                    "translation": "Students should attend office hours",
                    "evidence": "Professor recommendation",
                    "reasoning": "Recommendation implies desirable behavior",
                    "weight": 0.7,
                    "stanford_openie_support": f"Office hours triples: {[t for t in triples if 'office hours' in t['object']]}"
                }
            ],
            "stanford_openie_stats": {
                "total_triples": len(triples),
                "alice_specific_triples": len([t for t in triples if 'Alice' in t['subject']]),
                "conditional_triples": len([t for t in triples if 'will' in t['predicate']]),
                "location_triples": len([t for t in triples if 'library' in t['object']])
            }
        }


def main():
    """Run Stanford OpenIE demonstration with Alice example."""
    alice_text = """Alice is a student who loves mathematics. If Alice studies hard, she will pass the exam. Alice usually studies hard, but sometimes she gets distracted by social media. When Alice is focused, she always completes her homework. Alice's professor recommends that students attend office hours if they want to excel. Alice prefers studying in the library because it is quiet there."""

    print("STANFORD OPENIE + ENHANCED LLM PIPELINE DEMO")
    print("=" * 80)
    print("INPUT TEXT:")
    print(alice_text)
    print("=" * 80)

    try:
        # Initialize Stanford OpenIE converter
        converter = StanfordOpenIEMockConverter()

        # Run the complete pipeline
        result = converter.convert_text_to_logic(alice_text)

        # Display the simulated enhanced logical structure
        logic_structure = result['simulated_logic_structure']

        print("\nENHANCED LOGICAL STRUCTURE (Simulated LLM Output):")
        print("=" * 80)
        print(f"Primitive Propositions: {len(logic_structure['primitive_props'])}")
        print(f"Hard Constraints: {len(logic_structure['hard_constraints'])}")
        print(f"Soft Constraints: {len(logic_structure['soft_constraints'])}")
        print()

        print("Stanford OpenIE Statistics:")
        stats = logic_structure['stanford_openie_stats']
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Save complete demo output
        output_path = '/workspace/repo/artifacts/stanford_openie_full_demo.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\nComplete demo output saved to: {output_path}")
        print("\n🎉 Stanford OpenIE integration successful!")
        print(f"Extracted {result['openie_triples_count']} high-quality relation triples")

    except Exception as e:
        print(f"Error in Stanford OpenIE demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()