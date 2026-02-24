#!/usr/bin/env python3
"""
logic_converter.py - Two-Pass Text-to-Logic Converter

Pass 1: Extract ALL propositions + modal constraints only (full document)
Pass 2: Generate constraints chunk-by-chunk with cumulative context
"""

import json
import re
import os
from typing import Dict, Any, List, Tuple, Optional
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
    """Converts text + OpenIE triples to structured propositional logic using LLM."""

    # Threshold for triggering two-pass mode (characters)
    TWO_PASS_THRESHOLD = 8000
    
    # Target chunk size (characters)
    CHUNK_TARGET_SIZE = 4000

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

    def _parse_json_response(self, response_text: str, context: str = "") -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown fences and errors.
        
        Args:
            response_text: Raw response text from LLM
            context: Context string for error messages (e.g., "(pass1)", "(pass2-chunk0)")
            
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
                # Save debug file for inspection
                debug_file = f"debug_llm_response{context.replace(' ', '_').replace('(', '_').replace(')', '_')}.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response_text)
                print(f"[logic_converter] Raw response saved to: {debug_file}")
                raise ValueError(f"[logic_converter] Failed to parse JSON {context}: {e2}")
        
        # No JSON structure found at all
        debug_file = f"debug_llm_response{context.replace(' ', '_').replace('(', '_').replace(')', '_')}.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        print(f"[logic_converter] Raw response saved to: {debug_file}")
        raise ValueError(f"[logic_converter] No JSON structure found in response {context}")


    def _split_into_chunks(self, text: str, target_size: int = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks at sentence boundaries.
        
        Args:
            text: Full document text
            target_size: Target chunk size in characters (default: CHUNK_TARGET_SIZE)
            
        Returns:
            List of chunk dictionaries, each containing:
                - text: Chunk text content
                - start_sentence: First sentence index (0-based)
                - end_sentence: Last sentence index (inclusive)
        """
        if target_size is None:
            target_size = self.CHUNK_TARGET_SIZE
        
        # Split into sentences using regex
        # Handles: period, exclamation, question mark followed by whitespace
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        # Clean up: remove empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return [{"text": text, "start_sentence": 0, "end_sentence": 0}]
        
        chunks = []
        current_chunk_sentences = []
        current_chunk_start = 0
        current_size = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            # If adding this sentence exceeds target AND we already have content,
            # finalize current chunk and start a new one
            if current_size + sentence_size > target_size and current_chunk_sentences:
                chunks.append({
                    "text": " ".join(current_chunk_sentences),
                    "start_sentence": current_chunk_start,
                    "end_sentence": i - 1
                })
                # Start new chunk with current sentence
                current_chunk_sentences = [sentence]
                current_chunk_start = i
                current_size = sentence_size
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append(sentence)
                current_size += sentence_size + 1  # +1 for space
        
        # Don't forget the last chunk
        if current_chunk_sentences:
            chunks.append({
                "text": " ".join(current_chunk_sentences),
                "start_sentence": current_chunk_start,
                "end_sentence": len(sentences) - 1
            })
        
        return chunks
    
    def _parse_sentence_index(self, evidence: str) -> Optional[int]:
        """
        Extract sentence index from evidence field.
        
        Handles formats like:
            - "Sentence 12"
            - "Sentence 12-14" (returns first: 12)
            - "Sentences 5, 6, 7" (returns first: 5)
            - "Sentence 0: some text"
        
        Args:
            evidence: Evidence string from proposition
            
        Returns:
            Sentence index (0-based) or None if not found
        """
        if not evidence:
            return None
        
        # Match "Sentence X" pattern (case-insensitive)
        match = re.search(r'Sentence[s]?\s+(\d+)', evidence, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
    
    def _map_props_to_chunks(
        self, 
        propositions: List[Dict[str, Any]], 
        chunks: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Map propositions to chunks based on their evidence sentence index.
        
        Args:
            propositions: List of proposition dictionaries (must have 'evidence' field)
            chunks: List of chunk dictionaries (must have 'start_sentence', 'end_sentence')
            
        Returns:
            List of lists, where props_by_chunk[i] contains propositions for chunk i
        """
        props_by_chunk = [[] for _ in chunks]
        unmapped_props = []
        
        for prop in propositions:
            evidence = prop.get('evidence', '')
            sentence_idx = self._parse_sentence_index(evidence)
            
            if sentence_idx is not None:
                # Find which chunk this sentence belongs to
                mapped = False
                for i, chunk in enumerate(chunks):
                    if chunk['start_sentence'] <= sentence_idx <= chunk['end_sentence']:
                        props_by_chunk[i].append(prop)
                        mapped = True
                        break
                
                if not mapped:
                    # Sentence index out of range - add to unmapped
                    unmapped_props.append(prop)
            else:
                # No sentence index found - collect for later
                unmapped_props.append(prop)
        
        # Distribute unmapped props to first chunk (typically preamble/definitions)
        if unmapped_props:
            props_by_chunk[0].extend(unmapped_props)
        
        return props_by_chunk

    def _map_triples_to_chunks(
        self, 
        triples: List[List], 
        chunks: List[Dict[str, Any]]
    ) -> List[List[List]]:
        """
        Map OpenIE triples to chunks based on their sentence_index.
        
        Args:
            triples: List of triples, each as [subject, predicate, object, sentence_index]
            chunks: List of chunk dictionaries (must have 'start_sentence', 'end_sentence')
            
        Returns:
            List of lists, where triples_by_chunk[i] contains triples for chunk i
        """
        triples_by_chunk = [[] for _ in chunks]
        
        for triple in triples:
            # Triple format: [subject, predicate, object, sentence_index]
            if len(triple) >= 4:
                sentence_idx = triple[3]
                
                # Find which chunk this sentence belongs to
                for i, chunk in enumerate(chunks):
                    if chunk['start_sentence'] <= sentence_idx <= chunk['end_sentence']:
                        triples_by_chunk[i].append(triple)
                        break
            else:
                # Malformed triple (missing sentence_index) - add to first chunk
                triples_by_chunk[0].append(triple)
        
        return triples_by_chunk


    def _format_props_compact(self, propositions: List[Dict[str, Any]]) -> str:
        """
        Format propositions as compact reference list.
        
        Used for prior propositions in Pass 2 (ID + translation only).
        
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

    def _format_props_full(self, propositions: List[Dict[str, Any]]) -> str:
        """
        Format propositions with full detail as JSON.
        
        Used for current chunk propositions in Pass 2.
        
        Args:
            propositions: List of proposition dictionaries
            
        Returns:
            JSON string with indentation
        """
        if not propositions:
            return "[]"
        
        return json.dumps(propositions, indent=2, ensure_ascii=False)

    def _format_triples(self, triples: List[List]) -> str:
        """
        Format OpenIE triples as JSON array.
        
        Args:
            triples: List of triples [subject, predicate, object, sentence_index]
            
        Returns:
            JSON string with indentation
        """
        if not triples:
            return "[]"
        
        return json.dumps(triples, indent=2, ensure_ascii=False)
            

    def _single_pass(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Original single-pass conversion for short documents.
        
        Args:
            text: Full document text
            formatted_triples: JSON string of OpenIE triples
            
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

    def _pass1_extract_propositions(
        self, 
        text: str, 
        formatted_triples: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Pass 1: Extract all propositions and modal constraints only.
        
        Args:
            text: Full document text
            formatted_triples: JSON string of all OpenIE triples
            
        Returns:
            Tuple of (propositions, modal_constraints)
        """
        combined_input = f"""ORIGINAL TEXT:
        <<<
        {text}
        >>>

        RELATION TRIPLES:
        <<<
        {formatted_triples}
        >>>"""

        print(f"[logic_converter] Pass 1: Extracting propositions from {len(text)} chars...")
        
        response_text = self._call_llm(self.pass1_prompt, combined_input)
        print(f"[logic_converter] Pass 1 response: {len(response_text)} characters")
        
        result = self._parse_json_response(response_text, "(pass1)")
        
        propositions = result.get('primitive_props', [])
        modal_constraints = result.get('constraints', [])
        
        print(f"[logic_converter] Pass 1 complete: {len(propositions)} propositions, {len(modal_constraints)} modal constraints")
        
        return propositions, modal_constraints
    
    
    def _pass2_generate_constraints(
        self,
        chunk_text: str,
        chunk_triples: List[List],
        current_props: List[Dict[str, Any]],
        prior_props: List[Dict[str, Any]],
        start_constraint_id: int,
        chunk_index: int
    ) -> List[Dict[str, Any]]:
        """
        Pass 2: Generate constraints for propositions in current chunk.
        
        Args:
            chunk_text: Text of current chunk
            chunk_triples: OpenIE triples for this chunk
            current_props: Propositions from this chunk (generate constraints for these)
            prior_props: Propositions from previous chunks (reference only)
            start_constraint_id: Starting ID number for new constraints
            chunk_index: Index of current chunk (for logging)
            
        Returns:
            List of new constraints
        """
        if not current_props:
            print(f"[logic_converter] Pass 2 chunk {chunk_index}: No propositions, skipping")
            return []
        
        # Format components for prompt
        prior_props_text = self._format_props_compact(prior_props)
        current_props_text = self._format_props_full(current_props)
        triples_text = self._format_triples(chunk_triples)
        
        user_content = f"""## DOCUMENT SECTION (Chunk {chunk_index}):
        <<<
        {chunk_text}
        >>>

        ## OPENIE TRIPLES FOR THIS SECTION:
        {triples_text}

        ## PRIOR PROPOSITIONS (reference only - do NOT generate constraints for these):
        {prior_props_text}

        ## CURRENT PROPOSITIONS (generate constraints for THESE):
        {current_props_text}

        Generate constraints for all current propositions. Start constraint IDs from C_{start_constraint_id}."""

        print(f"[logic_converter] Pass 2 chunk {chunk_index}: {len(current_props)} props, {len(prior_props)} prior props, {len(chunk_triples)} triples")
        
        response_text = self._call_llm(self.pass2_prompt, user_content)
        result = self._parse_json_response(response_text, f"(pass2-chunk{chunk_index})")
        
        constraints = result.get('constraints', [])
        print(f"[logic_converter] Pass 2 chunk {chunk_index}: Generated {len(constraints)} constraints")
        
        return constraints

    def _two_pass_convert(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Two-pass conversion for long documents.
        
        Pass 1: Extract all propositions + modal constraints
        Pass 2: Generate other constraints chunk-by-chunk with cumulative context
        
        Args:
            text: Full document text
            formatted_triples: JSON string of all OpenIE triples
            
        Returns:
            Logic structure with primitive_props and constraints
        """
        print(f"[logic_converter] Two-pass mode (document size: {len(text)} chars)")
        
        # Parse triples for chunk mapping
        try:
            triples = json.loads(formatted_triples) if formatted_triples else []
        except json.JSONDecodeError:
            print("[logic_converter] WARNING: Could not parse triples, using empty list")
            triples = []
        
        # === PASS 1: Extract propositions + modal constraints ===
        propositions, modal_constraints = self._pass1_extract_propositions(text, formatted_triples)
        
        if not propositions:
            print("[logic_converter] WARNING: Pass 1 returned no propositions")
            return {"primitive_props": [], "constraints": []}
        
        # === CHUNKING ===
        chunks = self._split_into_chunks(text, self.CHUNK_TARGET_SIZE)
        print(f"[logic_converter] Split document into {len(chunks)} chunks")
        
        # Map propositions to chunks
        props_by_chunk = self._map_props_to_chunks(propositions, chunks)
        
        # Map triples to chunks
        triples_by_chunk = self._map_triples_to_chunks(triples, chunks)
        
        # Log distribution
        for i, chunk in enumerate(chunks):
            print(f"[logic_converter]   Chunk {i}: sentences {chunk['start_sentence']}-{chunk['end_sentence']}, "
                  f"{len(props_by_chunk[i])} props, {len(triples_by_chunk[i])} triples")
        
        # === PASS 2: Generate constraints chunk-by-chunk ===
        all_constraints = list(modal_constraints)
        cumulative_props = []
        
        # Find highest constraint ID from modal constraints
        max_constraint_id = 0
        for c in modal_constraints:
            match = re.search(r'C_(\d+)', c.get('id', ''))
            if match:
                max_constraint_id = max(max_constraint_id, int(match.group(1)))
        
        next_constraint_id = max_constraint_id + 1
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_props = props_by_chunk[i]
            chunk_triples = triples_by_chunk[i]
            
            new_constraints = self._pass2_generate_constraints(
                chunk_text=chunk['text'],
                chunk_triples=chunk_triples,
                current_props=chunk_props,
                prior_props=cumulative_props,
                start_constraint_id=next_constraint_id,
                chunk_index=i
            )
            
            all_constraints.extend(new_constraints)
            cumulative_props.extend(chunk_props)
            
            # Update next constraint ID based on what was generated
            for c in new_constraints:
                match = re.search(r'C_(\d+)', c.get('id', ''))
                if match:
                    next_constraint_id = max(next_constraint_id, int(match.group(1)) + 1)
        
        # === MERGE AND RETURN ===
        print(f"[logic_converter] Two-pass complete: {len(propositions)} props, {len(all_constraints)} constraints")
        
        return {
            "primitive_props": propositions,
            "constraints": all_constraints
        }


    def convert(self, text: str, formatted_triples: str) -> Dict[str, Any]:
        """
        Convert text + OpenIE triples to structured propositional logic.
        
        Automatically selects single-pass or two-pass mode based on document size.
        
        Args:
            text: Original document text
            formatted_triples: JSON string of OpenIE triples
            
        Returns:
            Logic structure with primitive_props and constraints
            
        Raises:
            RuntimeError: If conversion fails
        """
        try:
            # Choose mode based on document size
            if len(text) < self.TWO_PASS_THRESHOLD:
                return self._single_pass(text, formatted_triples)
            else:
                return self._two_pass_convert(text, formatted_triples)
        
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
