#!/usr/bin/env python3
"""
Debug script to understand pysmi API
"""

from pysmi.compiler import MibCompiler
from pysmi.parser import SmiStarParser
from pysmi.codegen import JsonCodeGen
from pysmi.writer import FileWriter
from pysmi.reader import FileReader
from pysmi.borrower import AnyFileBorrower
from pysmi import debug
from pathlib import Path

def test_pysmi_api():
    """Test pysmi API with different approaches"""

    # Enable debug mode to see what's happening
    debug.set_logger(debug.Debug('reader', 'compiler', 'borrower', 'searcher'))

    # Create parser
    parser = SmiStarParser()

    # Setup JSON code generation
    json_codegen = JsonCodeGen()

    # Create writer
    writer = FileWriter(str(Path.cwd() / "test_output"))

    # Create compiler
    compiler = MibCompiler(parser, json_codegen, writer)

    # Add MIB source
    mib_dir = "MIB"
    if Path(mib_dir).exists():
        reader = FileReader(mib_dir)
        compiler.add_searchers(reader)
        borrower = AnyFileBorrower(FileReader(mib_dir))
        compiler.add_borrowers(borrower)

    print("Testing pysmi compiler...")
    print(f"MIB sources added: {mib_dir}")

    # Test different approaches
    print("\nTrying approach 1: Compile by actual MIB module name")
    try:
        result = compiler.compile("OPTIX-OID-MIB")
        print(f"Success: {result}")

        # Check if output file was created
        output_file = Path.cwd() / "test_output" / "OPTIX-OID-MIB.json"
        if output_file.exists():
            print(f"Output file created: {output_file}")
        else:
            print("Output file not found")

    except Exception as e:
        print(f"Error: {e}")

    print("\nTrying approach 2: Check what sources are configured")
    try:
        print(f"Sources: {compiler.get_sources()}")
    except Exception as e:
        print(f"Error getting sources: {e}")

    print("\nTrying approach 3: Using file path directly")
    try:
        result = compiler.compile("MIB/01_OPTIX-OID-MIB")
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pysmi_api()