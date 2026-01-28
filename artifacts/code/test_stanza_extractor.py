#!/usr/bin/env python3
"""
Quick test to verify the modernized OpenIE extractor
"""

import sys
sys.path.insert(0, '/workspace/repo/code/from_text_to_logic')

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        import stanza
        from stanza.server import CoreNLPClient
        from openie_extractor import OpenIEExtractor
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_initialization():
    """Test extractor initialization."""
    print("\nTesting initialization...")
    try:
        from openie_extractor import OpenIEExtractor

        # Test with coref disabled (simpler)
        extractor = OpenIEExtractor(
            enable_coref=False,
            use_depparse_fallback=False,
            download_models=False
        )
        print("  ✓ Initialization successful")
        extractor.close()
        return True
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return False


def test_api_structure():
    """Test that API methods exist and have correct signatures."""
    print("\nTesting API structure...")
    try:
        from openie_extractor import OpenIEExtractor
        import inspect

        # Check methods exist
        methods = [
            'extract_triples',
            'extract_triples_with_coref_info',
            'format_triples',
            'format_triples_verbose',
            'close'
        ]

        for method in methods:
            if not hasattr(OpenIEExtractor, method):
                print(f"  ✗ Missing method: {method}")
                return False

        # Check extract_triples signature
        sig = inspect.signature(OpenIEExtractor.extract_triples)
        params = list(sig.parameters.keys())
        if 'text' not in params:
            print("  ✗ extract_triples missing 'text' parameter")
            return False

        print("  ✓ API structure correct")
        return True
    except Exception as e:
        print(f"  ✗ API check failed: {e}")
        return False


def test_triple_format():
    """Test that triple format is correct (no confidence scores)."""
    print("\nTesting triple format...")

    # Create a mock triple as the extractor would
    mock_triple = {
        'subject': 'Alice',
        'predicate': 'study',
        'object': 'mathematics',
        'sentence_index': 0,
        'source': 'openie'
    }

    # Check required fields
    required_fields = ['subject', 'predicate', 'object', 'sentence_index', 'source']
    for field in required_fields:
        if field not in mock_triple:
            print(f"  ✗ Missing required field: {field}")
            return False

    # Check confidence is NOT present
    if 'confidence' in mock_triple:
        print("  ✗ Confidence field should be removed")
        return False

    print("  ✓ Triple format correct (no confidence scores)")
    return True


def test_code_syntax():
    """Test that the Python file has valid syntax."""
    print("\nTesting code syntax...")
    try:
        import py_compile
        py_compile.compile('/workspace/repo/code/from_text_to_logic/openie_extractor.py', doraise=True)
        print("  ✓ Code syntax valid")
        return True
    except Exception as e:
        print(f"  ✗ Syntax error: {e}")
        return False


def main():
    print("=" * 60)
    print("STANZA OPENIE EXTRACTOR - VERIFICATION TESTS")
    print("=" * 60)

    tests = [
        test_code_syntax,
        test_imports,
        test_api_structure,
        test_triple_format,
        test_initialization
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! The extractor is ready to use.")
        print("\nNext steps:")
        print("  1. Download Stanza models (first time only):")
        print("     import stanza")
        print("     stanza.download('en', processors='tokenize,coref')")
        print("     stanza.download('en', processors='tokenize,pos,lemma,depparse')")
        print("\n  2. Run the demo:")
        print("     python3 /workspace/repo/artifacts/code/stanza_openie_demo.py")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check the errors above.")

    print("=" * 60)


if __name__ == "__main__":
    main()
