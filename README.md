# Wordlist Expander

A command-line tool that generates all possible words matching a given regex pattern.

## Description

`wordlist-expander.py` is a Python script that takes a regular expression pattern as input and outputs all possible words that would match that pattern. It's particularly useful for pattern-based word generation and testing regex patterns.

## Usage

Basic regex pattern:
```bash
python wordlist-expander.py '[regex]'
```

With wordlist substitution:
```bash
python wordlist-expander.py --wordlist path/to/wordlist.txt '[pattern-with-/x]'
```

### Examples

Basic regex pattern:
```bash
python wordlist-expander.py 'h[ao]{0,2}t'
```

Output:
```
ht
hat
hot
haot
hoat
```

Using wordlist substitution:
```bash
# wordlist.txt contains:
# cat
# dog

python wordlist-expander.py --wordlist wordlist.txt '0/x1/x2'
```

Output:
```
0cat1cat2
0cat1dog2
0dog1cat2
0dog1dog2
```

## Features

Regular Expression Support:
- Character classes (e.g., `[ao]`, `[A-Z]`, `[a-z]`)
- Standard regex classes (`\w`, `\d`, `\s`, `\W`, `\D`, `\S`)
- Quantifiers (e.g., `{0,2}`, `{1,3}`)
- Outputs words in alphabetical order
- Validates regex pattern before processing

Wordlist Integration:
- Optional wordlist support via `--wordlist` parameter
- `/x` placeholder for wordlist substitution
- Multiple `/x` placeholders iterate independently
- Combines wordlist words with regex patterns

## Requirements

- Python 3.x

## Installation

1. Clone this repository or download the `wordlist-expander.py` script
2. Make the script executable (on Unix-like systems):
   ```bash
   chmod +x wordlist-expander.py
   ```

## Error Handling

- Displays usage information if no pattern is provided
- Validates regex pattern and provides error message for invalid patterns
- Handles exceptions gracefully with informative error messages

## Note

For complex patterns or patterns that would generate a very large number of combinations, the script may require significant memory and processing time.
