"""
Test script for baseline RAG code validation.
Tests each module independently to verify correctness.
"""

def test_chunker():
    """Test chunking functionality."""
    from chunker import chunk_document

    text = "This is a test document with multiple words to test chunking functionality properly."
    chunks = chunk_document(text, chunk_size=5, overlap=2)

    assert len(chunks) > 0, "No chunks created"
    assert all('text' in c and 'chunk_id' in c for c in chunks), "Missing required fields"
    assert chunks[0]['chunk_id'] == 0, "First chunk should have ID 0"
    print("✓ Chunker tests passed")


def test_retriever():
    """Test retrieval functionality."""
    from retriever import load_sbert_model, encode_chunks, encode_query, retrieve

    model = load_sbert_model("all-MiniLM-L6-v2")

    chunks = [
        {'text': 'The sky is blue', 'chunk_id': 0},
        {'text': 'The grass is green', 'chunk_id': 1},
        {'text': 'Water is wet', 'chunk_id': 2}
    ]

    chunk_embeddings = encode_chunks(chunks, model)
    assert chunk_embeddings.shape[0] == 3, "Should have 3 chunk embeddings"

    query = "What color is the sky?"
    query_embedding = encode_query(query, model)

    retrieved = retrieve(query_embedding, chunk_embeddings, chunks, k=2)
    assert len(retrieved) == 2, "Should retrieve 2 chunks"
    print("✓ Retriever tests passed")


def test_evaluator():
    """Test evaluation metrics."""
    from evaluator import evaluate, format_results

    predictions = ['True', 'False', 'True', 'Unknown', 'True']
    ground_truth = ['True', 'True', 'True', 'Unknown', 'False']

    metrics = evaluate(predictions, ground_truth)

    assert 'accuracy' in metrics, "Missing accuracy"
    assert 'precision' in metrics, "Missing precision"
    assert 'recall' in metrics, "Missing recall"
    assert 'f1' in metrics, "Missing F1"
    assert 0 <= metrics['accuracy'] <= 1, "Accuracy out of range"

    formatted = format_results(metrics, 'test_dataset')
    assert len(formatted) > 0, "Empty formatted output"
    print("✓ Evaluator tests passed")


def test_main_functions():
    """Test main.py functions without API calls."""
    from main import preprocess_document

    text = "  Multiple   spaces   and\n\nnewlines  "
    cleaned = preprocess_document(text)
    assert cleaned == "Multiple spaces and newlines", f"Got: {cleaned}"
    print("✓ Main function tests passed")


def test_parse_response():
    """Test response parsing."""
    from reasoner import parse_response

    response1 = "After careful analysis, the answer is True."
    result1 = parse_response(response1)
    assert result1['answer'] == 'True', f"Expected True, got {result1['answer']}"

    response2 = "This is false because..."
    result2 = parse_response(response2)
    assert result2['answer'] == 'False', f"Expected False, got {result2['answer']}"

    response3 = "We cannot determine this, so Unknown."
    result3 = parse_response(response3)
    assert result3['answer'] == 'Unknown', f"Expected Unknown, got {result3['answer']}"

    print("✓ Response parsing tests passed")


if __name__ == "__main__":
    print("Running baseline RAG tests...\n")

    try:
        test_chunker()
        test_evaluator()
        test_main_functions()
        test_parse_response()
        test_retriever()

        print("\n" + "="*50)
        print("All tests passed successfully!")
        print("="*50)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
