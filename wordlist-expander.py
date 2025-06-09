#!/usr/bin/env python3

import sys
import re
import itertools
import string
import argparse

intlimit = 1000000  # Limit for the number of combinations to generate

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

    # Special escape sequences
    escape_sequences = {
        'n': '\n',  # newline
        't': '\t',  # tab
        'r': '\r',  # carriage return
        'f': '\f',  # form feed
        'v': '\v',  # vertical tab
        'b': '\b',  # backspace
        'a': '\a',  # bell/alert
    }

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
    if next_char == '\\':
        # Double backslash should output a single backslash
        return ['\\'], 2
    if next_char in escape_sequences:
        # Handle special escape sequences
        return [escape_sequences[next_char]], 2
    # For any other escaped character, just return the character itself
    return [next_char], 2

def generate_combinations_parts(pattern):
    """Generate the parts list for pattern combination"""
    # First, process regex quantifiers that aren't escaped
    processed_pattern = ""
    i = 0
    while i < len(pattern):
        if i > 0 and pattern[i-1] != '\\':  # Check if not escaped
            if pattern[i] == '+':
                processed_pattern += f"{{1,{intlimit}}}"
                i += 1
                continue
            elif pattern[i] == '*':
                processed_pattern += f"{{0,{intlimit}}}"
                i += 1
                continue
            elif pattern[i] == '?':
                processed_pattern += "{0,1}"
                i += 1
                continue
        processed_pattern += pattern[i]
        i += 1
    
    pattern = processed_pattern
    parts = []
    i = 0
    while i < len(pattern):
        # Check for special character classes first
        char_class, advance = get_char_class(pattern, i)
        if char_class is not None:
            parts.append(char_class)
            i += advance
        elif pattern[i] == '[':            # Handle character class
            end = pattern.index(']', i)
            chars = set()  # Use set to avoid duplicates
            j = i + 1
            while j < end:
                if j + 1 < end and pattern[j] == '\\':
                    # Handle special character classes inside brackets
                    char_class, advance = get_char_class(pattern, j)
                    if char_class is not None:
                        chars.update(char_class)
                        j += advance
                        continue
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
            max_count = int(nums[1]) if len(nums) > 1 else min_count            # Store quantifier info with the part instead of pre-expanding
            prev_part = parts.pop()
            parts.append((prev_part, min_count, max_count))
            i = end + 1
        else:
            # Handle literal character
            parts.append([pattern[i]])
            i += 1
    return parts

def generate_combinations(pattern):
    """Generate combinations one at a time using yield"""
    parts = generate_combinations_parts(pattern)
    
    def expand_part(part):
        """Helper function to handle both simple parts and quantifier tuples"""
        if isinstance(part, tuple):
            chars, min_count, max_count = part
            # Generate one length at a time to avoid memory explosion
            for n in range(min_count, max_count + 1):
                for p in itertools.product(chars, repeat=n):
                    yield ''.join(p)
        else:
            for char in part:
                yield char
    
    # Generate one complete combination at a time
    def recursive_combine(prefix, remaining_parts):
        if not remaining_parts:
            yield prefix
            return
            
        current_part = remaining_parts[0]
        for expanded in expand_part(current_part):
            yield from recursive_combine(prefix + expanded, remaining_parts[1:])
    
    yield from recursive_combine("", parts)

def get_capitalization_variants(line):
    """Generate capitalization variants for a line of text"""
    words = line.split()
    variants = set()  # Use set to automatically handle duplicates
    
    # 1. Original string
    variants.add(line)
    
    # 2. All lowercase
    variants.add(line.lower())
    
    # 3. First letter capitalized (e.g., "test string" -> "Test string")
    variants.add(line.capitalize())
    
    # 4. First letter of each word capitalized (e.g., "test string" -> "Test String")
    variants.add(' '.join(word.capitalize() for word in words))
    
    # 5. All capital letters
    variants.add(line.upper())
    
    # Convert back to list and sort for consistent output order
    return sorted(variants)

def load_wordlist(wordlist_path, capitalize=False):
    """Load words from a wordlist file, with optional capitalization variants"""
    try:
        with open(wordlist_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            if capitalize:
                # For each line, generate its capitalization variants
                expanded_lines = []
                for line in lines:
                    expanded_lines.extend(get_capitalization_variants(line))
                return expanded_lines
            return lines
    except Exception as e:
        print(f"Error reading wordlist file: {e}", file=sys.stderr)
        sys.exit(1)

def process_pattern_with_wordlist(pattern, wordlist):
    """Process a pattern containing \\x placeholders using words from the wordlist"""
    if '\\x' not in pattern:
        print("Error: When using --wordlist, the pattern must contain at least one \\x", file=sys.stderr)
        sys.exit(1)

    # Split pattern by \x, but handle escaped backslashes
    parts = []
    current = ""
    i = 0
    while i < len(pattern):
        if i + 1 < len(pattern) and pattern[i:i+2] == '\\x':
            parts.append(current)
            current = ""
            i += 2
        else:
            current += pattern[i]
            i += 1
    parts.append(current)
    
    # Generate combinations one at a time
    for word_combo in itertools.product(wordlist, repeat=len(parts)-1):
        current_pattern = parts[0]
        for i, word in enumerate(word_combo):
            current_pattern += word + parts[i+1]
        yield from generate_combinations(current_pattern)

def main():
    parser = argparse.ArgumentParser(description='Generate all possible strings matching a regex pattern')
    parser.add_argument('pattern', help='The regex pattern to expand')
    parser.add_argument('--wordlist', help='Path to a wordlist file for \\x substitution')
    parser.add_argument('-c', '--capitalize', action='store_true', 
                       help='Generate capitalization variants for each wordlist line (only works with --wordlist)')
    args = parser.parse_args()

    try:
        # Process the pattern and stream results
        if args.wordlist:
            if args.capitalize and '\\x' not in args.pattern:
                print("Error: -c/--capitalize option requires \\x in the pattern", file=sys.stderr)
                sys.exit(1)
            wordlist = load_wordlist(args.wordlist, args.capitalize)
            # Escape \x in pattern before regex validation
            validation_pattern = args.pattern.replace('\\x', 'X')  # temporary replacement for validation
            re.compile(validation_pattern)  # validate the pattern
            generator = process_pattern_with_wordlist(args.pattern, wordlist)
        else:
            re.compile(args.pattern)  # validate the pattern
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
