#!/usr/bin/env python3
"""
Full demo of logify2.py functionality with simulated LLM response.
Shows complete pipeline: OpenIE -> Enhanced Prompt -> Simulated Logic Output
"""

import json
from test_logify2_demo import MockLogifyConverter2


class FullMockLogifyConverter2(MockLogifyConverter2):
    """Full mock version that includes a simulated LLM response."""

    def convert_text_to_logic(self, text: str) -> dict:
        """Full demo version that shows the complete process with simulated LLM response."""
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
        print("STEP 1: OPENIE EXTRACTION")
        print("=" * 60)
        print(f"Extracted {len(openie_triples)} relation triples:")
        for i, triple in enumerate(openie_triples, 1):
            print(f"{i}. ({triple['subject']}; {triple['predicate']}; {triple['object']}) [conf: {triple['confidence']:.2f}]")

        print("\n" + "=" * 60)
        print("STEP 2: FORMATTED INPUT FOR LLM")
        print("=" * 60)
        print(combined_input)

        print("\n" + "=" * 60)
        print("STEP 3: SIMULATED LLM LOGICAL STRUCTURE OUTPUT")
        print("=" * 60)

        # Simulate what the enhanced LLM would return
        simulated_response = {
            "primitive_props": [
                {
                    "id": "P_1",
                    "translation": "Alice is a student",
                    "evidence": "Beginning of text: 'Alice is a student'",
                    "explanation": "Atomic statement about Alice's status as a student",
                    "openie_support": "('Alice'; 'is'; 'a student') from triple #7"
                },
                {
                    "id": "P_2",
                    "translation": "Alice loves mathematics",
                    "evidence": "First sentence: 'Alice is a student who loves mathematics'",
                    "explanation": "Atomic statement about Alice's preference for mathematics",
                    "openie_support": "Inferred from relative clause structure in original text"
                },
                {
                    "id": "P_3",
                    "translation": "Alice studies hard",
                    "evidence": "Second sentence: 'If Alice studies hard' and 'Alice usually studies hard'",
                    "explanation": "Atomic statement about Alice's study behavior",
                    "openie_support": "Referenced in conditional statements"
                },
                {
                    "id": "P_4",
                    "translation": "Alice passes the exam",
                    "evidence": "Second sentence: 'she will pass the exam'",
                    "explanation": "Atomic statement about exam outcome",
                    "openie_support": "('Alice'; 'pass'; 'the exam') from triple #2"
                },
                {
                    "id": "P_5",
                    "translation": "Alice gets distracted by social media",
                    "evidence": "Third sentence: 'sometimes she gets distracted by social media'",
                    "explanation": "Atomic statement about distraction behavior",
                    "openie_support": "Extracted from text analysis"
                },
                {
                    "id": "P_6",
                    "translation": "Alice is focused",
                    "evidence": "Fourth sentence: 'When Alice is focused'",
                    "explanation": "Atomic statement about Alice's mental state",
                    "openie_support": "('Alice'; 'is'; 'focused') from triple #8"
                },
                {
                    "id": "P_7",
                    "translation": "Alice completes her homework",
                    "evidence": "Fourth sentence: 'she always completes her homework'",
                    "explanation": "Atomic statement about homework completion",
                    "openie_support": "('Alice'; 'complete'; 'homework') from triple #3"
                },
                {
                    "id": "P_8",
                    "translation": "Students attend office hours",
                    "evidence": "Fifth sentence: 'students attend office hours'",
                    "explanation": "Atomic statement about student behavior recommendation",
                    "openie_support": "('students'; 'attend'; 'office hours') from triple #5"
                },
                {
                    "id": "P_9",
                    "translation": "Alice studies in the library",
                    "evidence": "Last sentence: 'Alice prefers studying in the library'",
                    "explanation": "Atomic statement about Alice's preferred study location",
                    "openie_support": "('Alice'; 'study in'; 'the library') from triple #6"
                },
                {
                    "id": "P_10",
                    "translation": "The library is quiet",
                    "evidence": "Last sentence: 'because it is quiet there'",
                    "explanation": "Atomic statement about library environment",
                    "openie_support": "('it'; 'is'; 'quiet') from triple #9"
                }
            ],
            "hard_constraints": [
                {
                    "id": "H_1",
                    "formula": "P_3 ⟹ P_4",
                    "translation": "If Alice studies hard, then she passes the exam",
                    "evidence": "Second sentence: 'If Alice studies hard, she will pass the exam'",
                    "reasoning": "Explicit conditional statement establishing logical implication",
                    "openie_support": "Derived from conditional structure with triples #2"
                },
                {
                    "id": "H_2",
                    "formula": "P_6 ⟹ P_7",
                    "translation": "If Alice is focused, then she completes her homework",
                    "evidence": "Fourth sentence: 'When Alice is focused, she always completes her homework'",
                    "reasoning": "Universal quantifier 'always' indicates hard constraint",
                    "openie_support": "Derived from conditional with triples #8 and #3"
                },
                {
                    "id": "H_3",
                    "formula": "P_9 ⟹ P_10",
                    "translation": "Alice's preference for library study is because it is quiet",
                    "evidence": "Last sentence: 'Alice prefers studying in the library because it is quiet there'",
                    "reasoning": "Causal relationship indicated by 'because'",
                    "openie_support": "Causal link between triples #6 and #9"
                }
            ],
            "soft_constraints": [
                {
                    "id": "S_1",
                    "formula": "P_3",
                    "translation": "Alice usually studies hard",
                    "evidence": "Third sentence: 'Alice usually studies hard'",
                    "reasoning": "Frequency adverb 'usually' indicates high probability but not certainty",
                    "weight": 0.8,
                    "openie_support": "Qualified frequency statement about study behavior"
                },
                {
                    "id": "S_2",
                    "formula": "P_5",
                    "translation": "Alice sometimes gets distracted by social media",
                    "evidence": "Third sentence: 'but sometimes she gets distracted by social media'",
                    "reasoning": "Frequency adverb 'sometimes' indicates moderate probability",
                    "weight": 0.3,
                    "openie_support": "Qualified frequency statement about distraction"
                },
                {
                    "id": "S_3",
                    "formula": "P_8",
                    "translation": "Students should attend office hours to excel",
                    "evidence": "Fifth sentence: 'Alice's professor recommends that students attend office hours if they want to excel'",
                    "reasoning": "Recommendation indicates desirable but not mandatory behavior",
                    "weight": 0.7,
                    "openie_support": "Derived from recommendation with triple #5"
                },
                {
                    "id": "S_4",
                    "formula": "P_9",
                    "translation": "Alice prefers studying in the library",
                    "evidence": "Last sentence: 'Alice prefers studying in the library'",
                    "reasoning": "Preference indicates likely but not absolute behavior",
                    "weight": 0.75,
                    "openie_support": "Direct from triple #6 with preference indicator"
                }
            ]
        }

        # Pretty print the simulated response
        print(json.dumps(simulated_response, indent=2))

        return simulated_response


def main():
    """Test with Alice example showing full pipeline."""
    alice_text = """Alice is a student who loves mathematics. If Alice studies hard, she will pass the exam. Alice usually studies hard, but sometimes she gets distracted by social media. When Alice is focused, she always completes her homework. Alice's professor recommends that students attend office hours if they want to excel. Alice prefers studying in the library because it is quiet there."""

    print("FULL LOGIFY2 DEMO: OpenIE + Enhanced LLM Pipeline")
    print("=" * 80)
    print("INPUT TEXT:")
    print(alice_text)
    print("=" * 80)

    try:
        # Initialize mock converter
        converter = FullMockLogifyConverter2()

        # Process the text through full pipeline
        result = converter.convert_text_to_logic(alice_text)

        # Save simulated output
        output_path = '/workspace/repo/artifacts/logify2_full_demo.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n{'='*80}")
        print("ANALYSIS SUMMARY:")
        print(f"{'='*80}")
        print(f"• Extracted {len(result['primitive_props'])} primitive propositions")
        print(f"• Identified {len(result['hard_constraints'])} hard constraints")
        print(f"• Identified {len(result['soft_constraints'])} soft constraints")
        print(f"• OpenIE preprocessing helped identify key relationships")
        print(f"• Enhanced prompt integrates OpenIE triples with original text")
        print(f"\nFull output saved to: {output_path}")

    except Exception as e:
        print(f"Error in demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()