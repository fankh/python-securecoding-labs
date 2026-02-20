#!/usr/bin/env python3
"""
Python Secure Coding Labs - Master Test Runner
Usage: python run_tests.py [chapter] [--verbose]

Examples:
    python run_tests.py              # Run all tests
    python run_tests.py ch04         # Run ch04 tests only
    python run_tests.py --verbose    # Verbose output
"""
import subprocess
import sys
import os
from pathlib import Path


CHAPTERS = [
    'ch02-input-validation',
    'ch03-command-injection',
    'ch04-sql-injection',
    'ch05-xss',
    'ch06-csrf',
    'ch07-file-upload',
    'ch08-deserialization',
    'ch09-authentication',
    'ch10-encryption',
    'ch11-error-handling',
    'ch12-supply-chain',
]


def run_chapter_tests(chapter_dir: str, verbose: bool = False) -> tuple:
    """Run tests for a specific chapter"""
    test_file = Path(chapter_dir) / 'test_app.py'
    if not test_file.exists():
        test_file = Path(chapter_dir) / 'test_tools.py'

    if not test_file.exists():
        return chapter_dir, 'SKIP', 'No test file found'

    cmd = [sys.executable, '-m', 'pytest', str(test_file)]
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=chapter_dir,
        timeout=300
    )

    if result.returncode == 0:
        return chapter_dir, 'PASS', result.stdout
    else:
        return chapter_dir, 'FAIL', result.stdout + result.stderr


def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    specific_chapter = None

    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            specific_chapter = arg
            break

    base_dir = Path(__file__).parent

    print("=" * 60)
    print("Python Secure Coding Labs - Test Runner")
    print("=" * 60)
    print()

    results = []

    chapters_to_test = CHAPTERS
    if specific_chapter:
        chapters_to_test = [c for c in CHAPTERS if specific_chapter in c]
        if not chapters_to_test:
            print(f"No chapter matching '{specific_chapter}' found")
            sys.exit(1)

    for chapter in chapters_to_test:
        chapter_path = base_dir / chapter
        if not chapter_path.exists():
            continue

        print(f"Testing {chapter}...", end=' ', flush=True)

        try:
            name, status, output = run_chapter_tests(str(chapter_path), verbose)

            if status == 'PASS':
                print("[OK] PASS")
            elif status == 'SKIP':
                print("[--] SKIP")
            else:
                print("[!!] FAIL")

            if verbose and output:
                print(output)

            results.append((name, status))

        except subprocess.TimeoutExpired:
            print("[!!] TIMEOUT")
            results.append((chapter, 'TIMEOUT'))
        except Exception as e:
            print(f"[!!] ERROR: {e}")
            results.append((chapter, 'ERROR'))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, s in results if s == 'PASS')
    failed = sum(1 for _, s in results if s == 'FAIL')
    skipped = sum(1 for _, s in results if s == 'SKIP')
    errors = sum(1 for _, s in results if s in ['ERROR', 'TIMEOUT'])

    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")
    print()

    if failed > 0 or errors > 0:
        print("Failed chapters:")
        for name, status in results:
            if status in ['FAIL', 'ERROR', 'TIMEOUT']:
                print(f"  - {name}: {status}")
        sys.exit(1)
    else:
        print("All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
