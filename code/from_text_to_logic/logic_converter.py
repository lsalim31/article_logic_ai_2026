#!/usr/bin/env python3
"""
logic_converter.py - Chunk-Based Text-to-Logic Converter

Simplified approach:
- Split document into chunks by paragraph/character boundaries
- For each chunk: extract propositions + constraints (with prior props as context)
- No sentence index mapping required
- IDs are globally unique from the start (no renumbering needed)
"""

import json
import re
import os
from typing import Dict, Any, List, Tuple
from openai import OpenAI

from config.retrieval_config import (
    MAX_TOKENS,
    TEMPERATURE_LOGIC_CONVERTER,
    REASONING_EFFORT,
    PROMPT_EXTRACTION,
    TRANSLATE_MODEL,
    PROMPT_PASS_1,
    PROMPT_PASS_2
)


class LogicConverter:
    """Converts text to structured propositional logic using LLM."""

    # Threshold for triggering multi-chunk mode (characters)
    CHUNK_THRESHOLD = 500000
    # Target chunk size (characters)
    CHUNK_TARGET_SIZE = 1500

    def __init__(
        self,
        api_key: str,
        model: str = TRANSLATE_MODEL,
        temperature: float = TEMPERATURE_LOGIC_CONVERTER,
        max_tokens: int = MAX_TOKENS,
        reasoning_effort: str = REASONING_EFFORT
    ):
        """Initialize the logic converter with API credentials and model settings."""
        # Detect OpenRouter keys and use appropriate base URL
        if api_key.startswith('sk-or-v1-') or api_key.startswith('sk-or-'):
            self.client = OpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1')
            if not model.startswith('openai/'):
                model = f'openai/{model}'
        else:
            self.client = OpenAI(api_key=api_key)

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.api_key = api_key

        # Load prompts
        self._script_dir = os.path.dirname(os.path.abspath(__file__))
        self._prompts_dir = os.path.join(self._script_dir, "..", "prompts")
        
        self.system_prompt = self._load_prompt(PROMPT_EXTRACTION)
        self.pass1_prompt = self._load_prompt(PROMPT_PASS_1)
        self.pass2_prompt = self._load_prompt(PROMPT_PASS_2)

        

    def _load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt from the prompts folder.

        Args:
            prompt_name: Name of the prompt file (without extension)

        Returns:
            Prompt content as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_path = os.path.join(self._prompts_dir, prompt_name)

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                # For the original system prompt, clean up format
                if prompt_name == PROMPT_EXTRACTION:
                    if "INPUT FORMAT" in content:
                        content = content.split("INPUT FORMAT")[0].strip()
                    if content.startswith("SYSTEM"):
                        content = content[6:].strip()

                return content
        except FileNotFoundError:
            raise FileNotFoundError(
                f"[logic_converter] Prompt file not found: {prompt_path}"
            )

    def _call_llm(self, prompt: str, user_content: str) -> str:
        """
        Make an LLM API call and return the response text.

        Args:
            prompt: System/developer prompt
            user_content: User message content

        Returns:
            Response text from LLM

        Raises:
            ValueError: If LLM returns empty response
        """
        # Determine if this is a reasoning model (GPT-5.x, o1, o3, etc.)
        base_model = self.model.replace("openai/", "")
        is_reasoning_model = (
            base_model.startswith("gpt-5") or
            base_model.startswith("o1") or
            base_model.startswith("o3")
        )

        is_openrouter = (
            self.api_key.startswith('sk-or-v1-') or
            self.api_key.startswith('sk-or-')
        )

        # Build API call parameters based on model type
        if is_reasoning_model:
            if is_openrouter:
                # OpenRouter format - combine system + user, use extra_body
                api_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt + "\n\n" + user_content}
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
                        {"role": "developer", "content": prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "reasoning_effort": self.reasoning_effort,
                    "max_completion_tokens": self.max_tokens
                }
        else:
            # Standard chat completion format
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

        # Make API call
        response = self.client.chat.completions.create(**api_params)
        response_text = response.choices[0].message.content

        if response_text is None:
            raise ValueError("[logic_converter] LLM returned empty response")

        return response_text.strip()


    def _repair_json(self, json_text: str) -> str:
        """
        Attempt to repair common JSON errors from LLM output.

        Fixes:
        - Missing quotes around string values (e.g., "key": value instead of "key": "value")
        - Trailing commas before closing brackets
        - Single quotes instead of double quotes

        Args:
            json_text: Potentially malformed JSON string

        Returns:
            Repaired JSON string (may still be invalid)
        """
        repaired = json_text

        # Fix missing opening quote after colon for string values
        # Pattern: "key": SomeText" -> "key": "SomeText"
        # Match: colon, optional whitespace, capital letter (start of sentence), text ending with "
        # This catches: "reasoning": Prohibition is stated..." -> "reasoning": "Prohibition is stated..."
        repaired = re.sub(
            r'("[\w_]+"\s*:\s*)([A-Z][^"]*?")',  # Key followed by unquoted value starting with capital
            r'\1"\2',
            repaired
        )

        # Also fix lowercase unquoted strings
        # Pattern: "key": some text" -> "key": "some text"
        repaired = re.sub(
            r'("[\w_]+"\s*:\s*)([a-z][^"]*?")',  # Key followed by unquoted value starting with lowercase
            r'\1"\2',
            repaired
        )

        # Fix trailing commas: ,] -> ] and ,} -> }
        repaired = re.sub(r',\s*\]', ']', repaired)
        repaired = re.sub(r',\s*\}', '}', repaired)

        # Fix single quotes (only if not inside a double-quoted string)
        # This is tricky - simple approach: replace ' with " if it looks like JSON structure
        # Only do this if there are no double quotes (unlikely for valid JSON)
        if '"' not in repaired and "'" in repaired:
            repaired = repaired.replace("'", '"')

        return repaired

    def _parse_json_response(self, response_text: str, context: str = "") -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown fences and errors.

        Args:
            response_text: Raw response text from LLM
            context: Context string for error messages (e.g., "(chunk0)", "(single-pass)")

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Try direct parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[logic_converter] WARNING: JSON parse failed {context}: {e}")

        # Try to strip markdown code fences
        cleaned_text = response_text
        if response_text.strip().startswith("```"):
            lines = response_text.strip().split('\n')
            # Remove opening fence (```json or ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = '\n'.join(lines)

            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                pass  # Fall through to bracket extraction

        # Fallback: extract between first { and last }
        if "{" in cleaned_text and "}" in cleaned_text:
            json_start = cleaned_text.find("{")
            json_end = cleaned_text.rfind("}") + 1
            json_text = cleaned_text[json_start:json_end]

            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e2:
                # Try to repair the JSON before giving up
                print(f"[logic_converter] Attempting JSON repair {context}...")
                repaired_text = self._repair_json(json_text)

                try:
                    result = json.loads(repaired_text)
                    print(f"[logic_converter] JSON repair successful {context}")
                    return result
                except json.JSONDecodeError as e3:
                    # Save debug file for inspection
                    debug_file = f"debug_llm_response{context.replace(' ', '_').replace('(', '_').replace(')', '_')}.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    print(f"[logic_converter] Raw response saved to: {debug_file}")
                    raise ValueError(f"[logic_converter] Failed to parse JSON {context}: {e3}")

        # No JSON structure found at all
        debug_file = f"debug_llm_response{context.replace(' ', '_').replace('(', '_').replace(')', '_')}.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        print(f"[logic_converter] Raw response saved to: {debug_file}")
        raise ValueError(f"[logic_converter] No JSON structure found in response {context}")


    # def _parse_json_response(self, response_text: str, context: str = "") -> Dict[str, Any]:
    #     """
    #     Parse JSON from LLM response, handling markdown fences and errors.

    #     Args:
    #         response_text: Raw response text from LLM
    #         context: Context string for error messages (e.g., "(chunk0)", "(single-pass)")

    #     Returns:
    #         Parsed JSON as dictionary

    #     Raises:
    #         ValueError: If JSON cannot be parsed
    #     """
    #     # Try direct parsing first
    #     try:
    #         return json.loads(response_text)
    #     except json.JSONDecodeError as e:
    #         print(f"[logic_converter] WARNING: JSON parse failed {context}: {e}")

    #     # Try to strip markdown code fences
    #     cleaned_text = response_text
    #     if response_text.strip().startswith("```"):
    #         lines = response_text.strip().split('\n')
    #         # Remove opening fence (```json or ```)
    #         if lines[0].startswith("```"):
    #             lines = lines[1:]
    #         # Remove closing fence
    #         if lines and lines[-1].strip() == "```":
    #             lines = lines[:-1]
    #         cleaned_text = '\n'.join(lines)

    #         try:
    #             return json.loads(cleaned_text)
    #         except json.JSONDecodeError:
    #             pass  # Fall through to bracket extraction

    #     # Fallback: extract between first { and last }
    #     if "{" in cleaned_text and "}" in cleaned_text:
    #         json_start = cleaned_text.find("{")
    #         json_end = cleaned_text.rfind("}") + 1
    #         json_text = cleaned_text[json_start:json_end]

    #         try:
    #             return json.loads(json_text)
    #         except json.JSONDecodeError as e2:
    #             # Save debug file for inspection
    #             debug_file = f"debug_llm_response{context.replace(' ', '_').replace('(', '_').replace(')', '_')}.txt"
    #             with open(debug_file, 'w', encoding='utf-8') as f:
    #                 f.write(response_text)
    #             print(f"[logic_converter] Raw response saved to: {debug_file}")
    #             raise ValueError(f"[logic_converter] Failed to parse JSON {context}: {e2}")

    #     # No JSON structure found at all
    #     debug_file = f"debug_llm_response{context.replace(' ', '_').replace('(', '_').replace(')', '_')}.txt"
    #     with open(debug_file, 'w', encoding='utf-8') as f:
    #         f.write(response_text)
    #     print(f"[logic_converter] Raw response saved to: {debug_file}")
    #     raise ValueError(f"[logic_converter] No JSON structure found in response {context}")

    def _split_into_chunks(self, text: str, target_size: int = None) -> List[str]:
        """
        Split text into chunks at paragraph boundaries.

        Prefers splitting at double newlines (paragraph breaks), falls back to
        single newlines, then to target_size boundaries.

        Args:
            text: Full document text
            target_size: Target chunk size in characters (default: CHUNK_TARGET_SIZE)

        Returns:
            List of chunk text strings
        """
        if target_size is None:
            target_size = self.CHUNK_TARGET_SIZE

        # cut start here
        # First, split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # If no double-newline breaks (or only 1 large paragraph), split by single newlines
        if not paragraphs or (len(paragraphs) == 1 and len(paragraphs[0]) > target_size):
            paragraphs = text.split('\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            # Still nothing - return as single chunk
            return [text]

        #end cut here
        # Now group paragraphs into chunks
        chunks = []
        current_chunk_parts = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # If adding this paragraph exceeds target AND we have content, start new chunk
            if current_size + para_size > target_size and current_chunk_parts:
                chunks.append('\n\n'.join(current_chunk_parts))
                current_chunk_parts = [para]
                current_size = para_size
            else:
                current_chunk_parts.append(para)
                current_size += para_size + 2  # +2 for '\n\n'

        # Don't forget the last chunk
        if current_chunk_parts:
            chunks.append('\n\n'.join(current_chunk_parts))

        return chunks

    def _format_prior_props(self, propositions: List[Dict[str, Any]]) -> str:
        """
        Format prior propositions as compact reference list.

        Args:
            propositions: List of proposition dictionaries

        Returns:
            Formatted string with one proposition per line
        """
        if not propositions:
            return "(none)"

        lines = []
        for prop in propositions:
            prop_id = prop.get('id', 'P_?')
            translation = prop.get('translation', '')
            lines.append(f"  {prop_id}: \"{translation}\"")

        return '\n'.join(lines)

    def _single_pass(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Single-pass conversion for short documents.

        Args:
            text: Full document text
            formatted_triples: JSON string of OpenIE triples (can be "[]")

        Returns:
            Logic structure with primitive_props and constraints
        """
        combined_input = f"""ORIGINAL TEXT:
        <<<
        {text}
        >>>

        RELATION TRIPLES:
        <<<
        {formatted_triples}
        >>>"""

        print(f"[logic_converter] Single-pass mode (document size: {len(text)} chars)")

        response_text = self._call_llm(self.system_prompt, combined_input)
        print(f"[logic_converter] Response length: {len(response_text)} characters")

        logic_structure = self._parse_json_response(response_text, "(single-pass)")

        # Validate required keys
        if "primitive_props" not in logic_structure:
            raise ValueError("[logic_converter] LLM output missing required key: primitive_props")
        if "constraints" not in logic_structure:
            raise ValueError("[logic_converter] LLM output missing required key: constraints")

        return logic_structure
    ####
    def _format_props_for_pass2(self, propositions: List[Dict[str, Any]]) -> str:
        """
        Format propositions as JSON for pass 2.

        Args:
            propositions: List of proposition dictionaries

        Returns:
            JSON string of propositions
        """
        if not propositions:
            return "[]"
        return json.dumps(propositions, indent=2, ensure_ascii=False)

    def _process_chunk(
        self,
        chunk_text: str,
        prior_props: List[Dict[str, Any]],
        start_prop_id: int,
        start_constraint_id: int,
        chunk_index: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, int]:
        """
        Process a single chunk using two passes:
        - Pass 1: Extract propositions
        - Pass 2: Generate constraints for those propositions

        Args:
            chunk_text: Text of current chunk
            prior_props: Propositions from previous chunks (for reference)
            start_prop_id: Starting ID for new propositions
            start_constraint_id: Starting ID for new constraints
            chunk_index: Index of current chunk (for logging)

        Returns:
            Tuple of (new_props, new_constraints, next_prop_id, next_constraint_id)
        """
        prior_props_text = self._format_prior_props(prior_props)

        # === PASS 1: Extract propositions ===
        pass1_content = f"""## DOCUMENT SECTION (Chunk {chunk_index}):
<<<
{chunk_text}
>>>

Extract propositions from this chunk.
- Start proposition IDs from P_{start_prop_id}
- Extract ALL factual statements, obligations, permissions, and conditions as propositions"""

        print(f"[logic_converter] Chunk {chunk_index} Pass 1: {len(chunk_text)} chars")

        response_text = self._call_llm(self.pass1_prompt, pass1_content)
        result = self._parse_json_response(response_text, f"(chunk{chunk_index}-pass1)")

        chunk_props = result.get('primitive_props', [])

        if not chunk_props:
            print(f"[logic_converter] WARNING: Chunk {chunk_index} Pass 1 returned no propositions")
            return [], [], start_prop_id, start_constraint_id

        print(f"[logic_converter] Chunk {chunk_index} Pass 1: {len(chunk_props)} propositions extracted")

        # Calculate next prop ID
        next_prop_id = start_prop_id
        for prop in chunk_props:
            match = re.search(r'P_(\d+)', prop.get('id', ''))
            if match:
                next_prop_id = max(next_prop_id, int(match.group(1)) + 1)

        # === PASS 2: Generate constraints ===
        current_props_text = self._format_props_for_pass2(chunk_props)

        pass2_content = f"""## DOCUMENT SECTION (Chunk {chunk_index}):
        <<<
        {chunk_text}
        >>>

        ## PRIOR PROPOSITIONS (from earlier sections - reference only, do NOT generate constraints for these):
        {prior_props_text}

        ## CURRENT PROPOSITIONS (generate constraints for THESE):
        {current_props_text}

        Generate constraints for all current propositions. Start constraint IDs from C_{start_constraint_id}.
        IMPORTANT: Every current proposition MUST have at least one standalone constraint asserting it."""

        print(f"[logic_converter] Chunk {chunk_index} Pass 2: generating constraints for {len(chunk_props)} props")

        response_text = self._call_llm(self.pass2_prompt, pass2_content)
        result = self._parse_json_response(response_text, f"(chunk{chunk_index}-pass2)")

        chunk_constraints = result.get('constraints', [])

        if not chunk_constraints:
            print(f"[logic_converter] WARNING: Chunk {chunk_index} Pass 2 returned no constraints")

        print(f"[logic_converter] Chunk {chunk_index} Pass 2: {len(chunk_constraints)} constraints generated")

        # Calculate next constraint ID
        next_constraint_id = start_constraint_id
        for constraint in chunk_constraints:
            match = re.search(r'C_(\d+)', constraint.get('id', ''))
            if match:
                next_constraint_id = max(next_constraint_id, int(match.group(1)) + 1)

        return chunk_props, chunk_constraints, next_prop_id, next_constraint_id
    

    #######

    def _multi_chunk_convert(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Multi-chunk conversion for long documents.

        Processes chunk-by-chunk, accumulating propositions for cross-chunk references.

        Args:
            text: Full document text
            formatted_triples: JSON string of OpenIE triples (unused in chunk mode)

        Returns:
            Logic structure with primitive_props and constraints
        """
        print(f"[logic_converter] Multi-chunk mode (document size: {len(text)} chars)")

        # Split document into chunks
        chunks = self._split_into_chunks(text, self.CHUNK_TARGET_SIZE)
        print(f"[logic_converter] Split document into {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            print(f"[logic_converter]   Chunk {i}: {len(chunk)} chars")

        # Process each chunk
        all_props = []
        all_constraints = []
        next_prop_id = 1
        next_constraint_id = 1

        for i, chunk_text in enumerate(chunks):
            new_props, new_constraints, next_prop_id, next_constraint_id = self._process_chunk(
                chunk_text=chunk_text,
                prior_props=all_props,  # Accumulated props from previous chunks
                start_prop_id=next_prop_id,
                start_constraint_id=next_constraint_id,
                chunk_index=i
            )

            all_props.extend(new_props)
            all_constraints.extend(new_constraints)

        print(f"[logic_converter] Multi-chunk complete: {len(all_props)} props, {len(all_constraints)} constraints")

        return {
            "primitive_props": all_props,
            "constraints": all_constraints
        }

    def convert(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Convert text to structured propositional logic.

        Automatically selects single-pass or multi-chunk mode based on document size.

        Args:
            text: Original document text
            formatted_triples: JSON string of OpenIE triples (can be "[]")

        Returns:
            Logic structure with primitive_props and constraints

        Raises:
            RuntimeError: If conversion fails
        """
        try:
            # Choose mode based on document size
            if len(text) < self.CHUNK_THRESHOLD:
                return self._single_pass(text, formatted_triples)
            else:
                return self._multi_chunk_convert(text, formatted_triples)

        except Exception as e:
            raise RuntimeError(f"[logic_converter] Error in LLM conversion: {e}")

    def save_output(self, logic_structure: Dict[str, Any], output_path: str = "logified.json"):
        """
        Save the logic structure to a JSON file.

        Args:
            logic_structure: Dictionary with primitive_props and constraints
            output_path: Output file path (default: logified.json)
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logic_structure, f, indent=2, ensure_ascii=False)
        print(f"[logic_converter] Output saved to {output_path}")
