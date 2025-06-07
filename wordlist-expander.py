#!/usr/bin/env python3

import sys
import re
import itertools
import string
import argparse

def expand_char_range(start, end):
    """Expand character ranges like A-Z, a-z, A-z"""
    return [chr(i) for i in range(ord(start), ord(end) + 1)]

def get_char_class(pattern, i):
    """Handle special regex character classes"""
    if i + 1 >= len(pattern):
        return [pattern[i]], 1
    
    if pattern[i] != '\\':
        return None, 0

    # Define base character sets
    digits = list(string.digits)
    word_chars = list(string.ascii_letters + string.digits + '_')
    whitespace = list(' \t\n\r\f\v')
    
    # Define all printable characters for complement sets
    all_chars = list(string.printable)
    
    # Create complement sets
    non_digits = sorted(list(set(all_chars) - set(digits)))
    non_word = sorted(list(set(all_chars) - set(word_chars)))
    non_whitespace = sorted(list(set(all_chars) - set(whitespace)))

    char_class_map = {
        'w': word_chars,        # Word characters [A-Za-z0-9_]
        'd': digits,            # Digits [0-9]
        's': whitespace,        # Whitespace [ \t\n\r\f\v]
        'W': non_word,          # Non-word characters [^A-Za-z0-9_]
        'D': non_digits,        # Non-digits [^0-9]
        'S': non_whitespace,    # Non-whitespace [^ \t\n\r\f\v]
    }

    next_char = pattern[i + 1]
    if next_char in char_class_map:
        return char_class_map[next_char], 2
    return ['\\' + next_char], 2

def generate_combinations_parts(pattern):
    """Generate the parts list for pattern combination"""
    parts = []
    i = 0
    while i < len(pattern):
        # Check for special character classes first
        char_class, advance = get_char_class(pattern, i)
        if char_class is not None:
            parts.append(char_class)
            i += advance
        elif pattern[i] == '[':
            # Handle character class
            end = pattern.index(']', i)
            chars = set()  # Use set to avoid duplicates
            j = i + 1
            while j < end:
                if j + 2 < end and pattern[j+1] == '-':
                    # Handle ranges like A-Z, a-z, A-z
                    chars.update(expand_char_range(pattern[j], pattern[j+2]))
                    j += 3
                else:
                    chars.add(pattern[j])
                    j += 1
            parts.append(sorted(list(chars)))
            i = end + 1
        elif pattern[i] == '{':
            # Handle quantifier
            end = pattern.index('}', i)
            nums = pattern[i+1:end].split(',')
            min_count = int(nums[0])
            max_count = int(nums[1]) if len(nums) > 1 else min_count
            # Modify the previous part to include repetition
            prev_part = parts.pop()
            expanded = []
            for n in range(min_count, max_count + 1):
                expanded.extend([''.join(p) for p in itertools.product(prev_part, repeat=n)])
            parts.append(expanded)
            i = end + 1
        else:
            # Handle literal character
            parts.append([pattern[i]])
            i += 1
    return parts

def generate_combinations(pattern):
    """Generate combinations one at a time using yield"""
    parts = generate_combinations_parts(pattern)
    for combo in itertools.product(*parts):
        yield ''.join(combo)

def load_wordlist(wordlist_path):
    """Load words from a wordlist file"""
    try:
        with open(wordlist_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading wordlist file: {e}", file=sys.stderr)
        sys.exit(1)

def process_pattern_with_wordlist(pattern, wordlist):
    """Process a pattern containing /x placeholders using words from the wordlist"""
    if '/x' not in pattern:
        print("Error: When using --wordlist, the pattern must contain at least one /x", file=sys.stderr)
        sys.exit(1)

    # Split pattern into parts by /x
    parts = pattern.split('/x')
    
    # Generate combinations one at a time
    for word_combo in itertools.product(wordlist, repeat=len(parts)-1):
        current_pattern = parts[0]
        for i, word in enumerate(word_combo):
            current_pattern += word + parts[i+1]
        yield from generate_combinations(current_pattern)

def main():
    parser = argparse.ArgumentParser(description='Generate all possible strings matching a regex pattern')
    parser.add_argument('pattern', help='The regex pattern to expand')
    parser.add_argument('--wordlist', help='Path to a wordlist file for /x substitution')
    args = parser.parse_args()

    try:
        # Validate the regex pattern first
        re.compile(args.pattern)

        # Process the pattern and stream results
        if args.wordlist:
            wordlist = load_wordlist(args.wordlist)
            generator = process_pattern_with_wordlist(args.pattern, wordlist)
        else:
            generator = generate_combinations(args.pattern)

        # Print results as they are generated
        seen = set()  # To maintain uniqueness while streaming
        for result in generator:
            if result not in seen:  # Only print unique results
                seen.add(result)
                print(result, flush=True)  # flush=True ensures immediate output

    except re.error:
        print(f"Error: Invalid regex pattern: {args.pattern}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
