#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./transform_LaTeX_JSON_to_HTML_JSON.py --json fordiva.json [--acronyms acronyms.tex]
#
# Purpose: Transform the LaTeX JSON file that has been produced by my LaTeX template and produced an HTML JSON file.
# The resulting file can be used with my other program (to create calendar entries, MODS file, and insert titles into LADOK).
#
# Outputs a a JSON file with HTML in a file with the name augmented by "-HTML"
#
# Example:
# ./transform_LaTeX_JSON_to_HTML_JSON.py --json fordiva.json [--acronyms acronyms.tex]
# 
# Based upon earlier cleanup_pseudo_JSON-from_LaTeX.py
#
# 2025-08-13 G. Q. Maguire Jr.

#
import re
import sys

import json
#import argparse
import optparse
import os			# to make OS calls, here to get time zone info
import pprint


def remove_latex_comments(s):
    """
    Removes single-line LaTeX comments (%), ignoring escaped percent signs (\\%).

    Args:
        s (str): The input string with LaTeX comments.

    Returns:
        str: The string with comments completely removed.
    """
    processed_lines = []
    for line in s.split('\n'):
        # Find the first unescaped '%' on the line
        match = re.search(r'(?<!\\)%', line)
        if match:
            # If a comment is found, keep only the part of the line before it
            start_pos = match.start()
            processed_lines.append(line[:start_pos])
        else:
            # If no comment is found, keep the entire line
            processed_lines.append(line)
            
    return '\n'.join(processed_lines)

def convert_latex_comments_to_html(s):
    """
    Finds and converts single-line LaTeX comments (%) into HTML comments (),
    while correctly ignoring escaped percent signs (\\%).
    """
    processed_lines = []
    
    for line in s.split('\n'):
        match = re.search(r'(?<!\\)%', line)
        
        if match:
            start_pos = match.start()
            before_comment = line[:start_pos]
            comment_text = line[start_pos+1:] # The text after the '%'
            
            # *** YOUR CORRECTED LINE ***
            # Reconstruct the line with HTML comment tags
            new_line = f"{before_comment}<!-- {comment_text} -->"
            processed_lines.append(new_line)
        else:
            # If no comment is found, keep the line as is
            processed_lines.append(line)
            
    return '\n'.join(processed_lines)



def old_replace_latex_symbol(s, symbol, insert_symbol):
    global Verbose_Flag
    cmd_offset=s.find(symbol)
    while (cmd_offset) > 0:
        s1=s[:cmd_offset]
        s2=s[cmd_offset+len(symbol):]
        s=s1+insert_symbol+s2
        cmd_offset=s.find(symbol, cmd_offset)
    return s

def replace_latex_symbol(s, symbol, insert_symbol):
    """
    Replaces a LaTeX symbol and consumes one optional trailing space.
    
    Args:
        s (str): The input string.
        symbol (str): The LaTeX command to replace (e.g., '\\textregistered').
        insert_symbol (str): The string to substitute.

    Returns:
        str: The modified string.
    """
    # 1. Escape the input symbol to treat it as a literal string in the regex.
    #    This is important in case the symbol contains special regex characters.
    escaped_symbol = re.escape(symbol)
    
    # 2. Create a pattern that matches the symbol followed by ONE optional space.
    #    ' ?' matches zero or one space character.
    pattern = escaped_symbol + r' ?'
    
    # 3. Use re.sub() to perform the replacement.
    return re.sub(pattern, insert_symbol, s)


# usage: replace_latex_command(s1, '\\textit{', '<i>', '</i>')
def old_replace_latex_command(s, command, insert_at_start, insert_at_end):
    """
    Replaces a simple LaTeX command with content in braces, allowing for
    optional whitespace between the command and its argument.
    """
    command_name = command.lstrip('\\')
    
    # *** THE CRITICAL FIX ***
    # The \s* pattern is added to match zero or more whitespace characters
    # (spaces, tabs, newlines) between the command and the opening brace.
    pattern = rf'\\{command_name}\s*{{(.*?)}}'
    
    replacement = rf'{insert_at_start}\1{insert_at_end}'
    
    return re.sub(pattern, replacement, s)

def replace_latex_command(s, command, insert_at_start, insert_at_end):
    """
    Replaces a simple LaTeX command with content in braces, allowing for
    optional whitespace and correctly handling trailing punctuation.
    """
    # 1. Use re.escape() to safely handle the backslash in the command name.
    #    This is the most robust way to build the pattern.
    escaped_command = re.escape(command)

    # 2. *** THE CRITICAL FIX ***
    #    The pattern now uses [^}]+ to capture one or more characters
    #    that are NOT a closing brace. This is more precise and avoids
    #    the "greedy" behavior that was eating a following period.
    pattern = escaped_command + r'\s*\{([^}]+)\}'
    
    # 3. The replacement uses \1 to backreference the captured content.
    replacement = rf'{insert_at_start}\1{insert_at_end}'
    
    # 4. Use re.sub() to perform the replacement.
    return re.sub(pattern, replacement, s)


def replace_latex_environment(s, environment, insert_at_start, insert_at_end):
    """
    Replaces a LaTeX environment with specified start and end tags.

    This function finds all occurrences of `\\begin{env} ... \\end{env}`
    and replaces them, keeping the inner content.

    Args:
        s (str): The input string to process.
        environment (str): The name of the environment (e.g., 'itemize').
        insert_at_start (str): The string to replace the \\begin{...} tag.
        insert_at_end (str): The string to replace the \\end{...} tag.

    Returns:
        str: The modified string.
    """
    # 1. Create the regex pattern.
    #    - \\begin\s*\{...\} matches the opening tag with optional whitespace.
    #    - (.*?) captures the content in between, non-greedily.
    #    - \\end\s*\{...\} matches the closing tag.
    #    - The re.DOTALL flag is crucial to allow '.' to match newline characters.
    pattern = rf'\\begin\s*{{{environment}}}(.*?)\\end\s*{{{environment}}}'
    
    # 2. Create the replacement string.
    #    '\\1' is a backreference to the captured content.
    replacement = rf'{insert_at_start}\1{insert_at_end}'
    
    # 3. Use re.sub() to find all matches and replace them.
    return re.sub(pattern, replacement, s, flags=re.DOTALL)

def replace_latex_break_command(s, command_name, replacement):
    """
    Replaces a LaTeX line break command and its optional argument.

    Args:
        s (str): The input string to process.
        command_name (str): The name of the break command (e.g., 'linebreak').
        replacement (str): The string to substitute for the command.

    Returns:
        str: The modified string.
    """
    # 1. Create the regex pattern.
    #    - \\{command_name} matches the command itself.
    #    - \s* matches any optional whitespace.
    #    - (?:\[\d\])? is a non-capturing group that optionally matches
    #      a single digit inside square brackets.
    pattern = rf'\\{command_name}\s*(?:\[\d\])?'
    
    # 2. Use re.sub() to find all matches and replace them.
    return re.sub(pattern, replacement, s)

def remove_empty_paragraphs(s):
    """
    Removes empty <p> tags that only contain whitespace.

    Args:
        s (str): The input string (e.g., HTML content).

    Returns:
        str: The string with empty paragraphs removed.
    """
    # The pattern looks for a <p> tag, followed by any number of
    # whitespace characters (\s*), and then a closing </p> tag.
    # The re.IGNORECASE flag makes the match case-insensitive (so it also finds <P>).
    pattern = r'<p>\s*</p>'
    
    # Replace all occurrences of the pattern with an empty string.
    return re.sub(pattern, '', s, flags=re.IGNORECASE)

def remove_empty_listitems(s):
    """
    Removes empty <p> tags that only contain whitespace.

    Args:
        s (str): The input string (e.g., HTML content).

    Returns:
        str: The string with empty paragraphs removed.
    """
    # The pattern looks for a <p> tag, followed by any number of
    # whitespace characters (\s*), and then a closing </p> tag.
    # The re.IGNORECASE flag makes the match case-insensitive (so it also finds <P>).
    pattern = r'<li>\s*</li>'
    
    # Replace all occurrences of the pattern with an empty string.
    return re.sub(pattern, '', s, flags=re.IGNORECASE)

string_replacements = {
    # Rates and Ratios
    '\\meter\\per\\second': 'm/s', # or ms<sup>-1</sup>
    'meters per minute': 'm/min',
    'degrees per second': 'deg/s',
    'Litres per minute': 'L/min',
    'Coulombs per minute': 'C/min',
    'Exabits/s': 'Ebit/s',
    'GBytes/s': 'GB/s',
    'Gigabits/s': 'Gbit/s',
    'Gigabits/second': 'Gbit/s',
    'Gbit/sec': 'Gbit/s',
    'Gbps': 'Gbit/s',
    'joule/bit': 'J/bit',
    'Mbit/s': 'Mbit/s',
    'Mbits/s': 'Mbit/s',
    'Mbits/sec': 'Mbit/s',
    'Mbps': 'Mbit/s',
    'bits/sec': 'bit/s',
    'bits/second': 'bit/s',
    'bps': 'bit/s',
    'bytes/sec': 'B/s',
    'calls/day': 'calls/day',
    'calls/year': 'calls/year',
    'h/year': 'h/year',
    'ms/frame': 'ms/frame',
    's/transaction': 's/transaction',
    'SEK/kWh': 'SEK/kWh',
    'NOK/kWh': 'NOK/kWh',
    '€/MWh': '€/MWh',
    'watt/second': 'W/s',
    'Wh/km': 'Wh/km',

    # Units with Superscripts
    '\\meter\\squared': 'm<sup>2</sup>',
    '\\meter\\cubed': 'm<sup>3</sup>',
    'atoms/cm2': 'atoms/cm<sup>2</sup>',
    'cd/m2': 'cd/m<sup>2</sup>',
    'cm2': 'cm<sup>2</sup>',
    'cm-1': 'cm<sup>-1</sup>',
    'cm-2': 'cm<sup>-2</sup>',
    'cm−2': 'cm<sup>-2</sup>', # Using an en-dash
    'cm-3': 'cm<sup>-3</sup>',
    'm2': 'm<sup>2</sup>',
    'm3': 'm<sup>3</sup>',
    'µm2': 'µm<sup>2</sup>',

    # Special Cases and Normalization
    'CO2-eq./km': 'CO<sub>2</sub>-eq/km',
    'S.cm-1': 'S/cm',
    'KiloWatts': 'kW',
    'TeraWatthours': 'TWh',
    'Terawatt-hours': 'TWh',
    'centigrade': '°C',
    'Ångström': 'Å',
    'angstroms': 'Å',
    'angstrom': 'Å',

    # Angles
    '\\degree': '°',
    '\\arcminute': "'",
    '\\arcsecond': '"',
    '\\radian': 'rad',

    # Common Scientific Units
    '\\astronomicalunit': 'au',
    '\\atmosphere': 'atm',
    '\\bar': 'bar',
    '\\candela': 'cd',
    '\\dalton': 'Da',
    '\\electronvolt': 'eV',
    '\\hertz': 'Hz',
    '\\joule': 'J',
    '\\kelvin': 'K',
    '\\knot': 'kn',
    '\\mole': 'mol',
    '\\newton': 'N',
    '\\ohm': 'Ω',
    '\\pascal': 'Pa',
    '\\siemens': 'S',
    '\\tesla': 'T',
    '\\volt': 'V',
    '\\watt': 'W',

    # Textual and Phrase-based Units
    '\\percent': '%', # note that this has to done be before the following
    '\\per': '/', # Converts commands like \meter\per\second
    '\\square': '<sup>2</sup>', # For units like \square\meter
    '\\cubic': '<sup>3</sup>',  # For units like \cubic\meter
    
    # Specific Compound Units
    'kilo parsec': 'kpc',
    'megakronor': 'Mkr',
    'gigakronor': 'Gkr',
    'million €': 'M€',
    'million SEK': 'MSEK',
    'Giga tons': 'Gt',
    'Terawatt-hours': 'TWh',
    'Gigaflop/Joule': 'GFLOP/J',
    'Gigaflop/second': 'GFLOP/s',
    'kibibit per second': 'Kibit/s', # Normalizing names
    'megamessages per second': 'MMS/s'
}


def preprocess_units(s, replacements):
    """
    Performs a series of direct string replacements for complex units.
    """
    for latex_str, replacement_str in replacements.items():
        s = s.replace(latex_str, replacement_str)
    return s


def replace_latex_qty(s):
    """
    Replaces LaTeX \\qty{number}{unit} and \\qty{number} commands.

    Args:
        s (str): The input string containing LaTeX commands.

    Returns:
        str: The string with \\qty commands replaced.
    """
    
    unit_mapping = {
        # Base SI
        '\\meter': 'm',
        '\\second': 's',
        '\\gram': 'g',

        # Electrical and Magnetic
        '\\ohm': 'Ω',
        '\\siemens': 'S',
        '\\hertz': 'Hz',
        '\\ampere': 'A',
        '\\volt': 'V',
        '\\watt': 'W',
        '\\farad': 'F',
        '\\tesla': 'T',
        '\\oersted': 'Oe',

        # Temperature and Energy
        '\\degreeCelsius': '℃',
        '\\degreeKelvin': 'K', # Note: 'degree' is often omitted for Kelvin
        '\\joule': 'J',
        '\\electronvolt': 'eV',

        # Other Physical Units
        '\\pascal': 'Pa',
        '\\newton': 'N',
        '\\gray': 'Gy',
        '\\dalton': 'Da',

        # Currencies and Other Symbols
        '\\percent': '%',
        '\\euro': '€',
        '\\sek': 'kr', # For Swedish Krona
        '\\degree': '°',
        '\\angstrom': 'Å'



        # Add other units here
    }

    # *** THE CRITICAL FIX ***
    # The second group for the unit is now optional.
    # (?:\s*\{([^}]+)\})?  <-- This part makes the second argument optional
    pattern = r'\\qty\s*\{([^}]+)\}(?:\s*\{([^}]+)\})?'

    def replacer(match):
        number = match.group(1)
        unit_command = match.group(2) # This will be None if the unit is not present
        
        # If a unit was provided, process it
        if unit_command:
            unit_symbol = unit_mapping.get(unit_command, unit_command)
            # Return with the narrow non-breaking space and the unit
            return f'{number}\u202F{unit_symbol}'
        else:
            # If no unit was provided, just return the number
            return number

    return re.sub(pattern, replacer, s)

def replace_ordinals_and_fix_spacing(s):
    """
    Replaces LaTeX ordinal commands and correctly handles spacing
    before punctuation.
    """
    # 1. Perform your initial replacements as before.
    replacements = {
        '\\first': '(i) ',
        '\\Second': '(ii) ', # Assuming this should be lowercase 'second'
        '\\third': '(iii) ',
        '\\fourth': '(iv) ',
        '\\fifth': '(v) ',
        '\\sixth': '(vi) ',
        '\\seventh': '(vii) ',
        '\\eighth': '(viii) '
    }
    
    for command, replacement in replacements.items():
        s = s.replace(command, replacement)
        
    # 2. *** THE CRITICAL FIX ***
    #    Use a regex to remove any space that is immediately followed by
    #    a punctuation character from the set [, . ? ! : ;].
    #    The (?=...) is a "positive lookahead".
    cleanup_pattern = r' (?=[,.?!:;])'
    s = re.sub(cleanup_pattern, '', s)
    
    return s

def replace_latex_abbreviations(s):
    """
    Replaces LaTeX abbreviations like \\etal and \\eg with HTML,
    correctly handling surrounding punctuation.
    """
    # 1. Define the abbreviations and their replacements.
    #    The replacement text should not include a final period,
    #    as the logic will add it contextually.
    abbreviations = {
        'eg': 'e.g',
        'Eg': 'E.g',
        'ie': 'i.e',
        'Ie': 'I.e',
        'etc': 'etc',
        'etal': 'et al'  # The non-breaking space (~) becomes a regular space
    }

    # 2. Iterate through each command to apply the specific replacement rules.
    for command, text in abbreviations.items():
        
        # Rule 1: Handle the command when it's followed by \cite.
        # Pattern: \command, optional space, followed by \cite (lookahead)
        # Replaces with: <i>text.</i>&thinsp;
        s = re.sub(rf'\\{command}\s*(?=\\cite)', f'<i>{text}.</i>&thinsp;', s)
        
        # Rule 2: Handle the command when it's followed by a period.
        # Pattern: \command, optional space, and a literal period.
        # Replaces with: <i>text</i>. (to avoid a double period)
        s = re.sub(rf'\\{command}\s*\.', f'<i>{text}</i>.', s)

        # Rule 3: Handle the command when followed by other punctuation.
        # Pattern: \command, optional space, followed by , ! ? or ) (lookahead)
        # Replaces with: <i>text.</i>
        s = re.sub(rf'\\{command}\s*(?=[,!?\)])', f'<i>{text}.</i>', s)
        
        # Rule 4: Handle the default case (e.g., followed by a word).
        # This is the last and most general rule. It will only apply to
        # commands that were not matched by the rules above.
        # Replaces with: <i>text.,</i> (with a comma and space, as in the macro)
        s = re.sub(rf'\\{command}', f'<i>{text}.,</i> ', s)
        
    return s

def replace_latex_accents(s):
    """
    Replaces LaTeX accent commands with their corresponding pre-composed
    Unicode characters using the unicodedata library. This version has a
    more comprehensive list of standard LaTeX accents.
    """
    
    # 1. A more comprehensive map of LaTeX accent commands to their
    #    Unicode COMBINING character codes.
    accent_map = {
        # Standard European accents
        '\\`': '\u0300',  # Combining Grave Accent
        "\\'": '\u0301',  # Combining Acute Accent
        "\\^": '\u0302',  # Combining Circumflex Accent
        "\\~": '\u0303',  # Combining Tilde
        '\\"': '\u0308',  # Combining Diaeresis (umlaut)
        "\\H": '\u030B',  # Combining Double Acute Accent
        
        # Dot, Ring, and Macron accents
        "\\.": '\u0307',  # Combining Dot Above
        "\\r": '\u030A',  # Combining Ring Above
        "\\=": '\u0304',  # Combining Macron
        "\\bar": '\u0305', # Combining Overline (often visually similar to macron)
        
        # Other common accents
        "\\v": '\u030C',  # Combining Caron (haček)
        "\\u": '\u0306',  # Combining Breve
        "\\h": '\u0309',  # Combining Hook Above
        "\\t": '\u0361',  # Combining Double Inverted Breve (tie)
        
        # Under-accents
        "\\c": '\u0327',  # Combining Cedilla
        "\\k": '\u0328',  # Combining Ogonek
        "\\d": '\u0323',  # Combining Dot Below
        "\\b": '\u0331',  # Combining Macron Below
        
    }

    # 2. Build a single regex pattern from the accent_map keys.
    #    This is more efficient than looping in Python.
    pattern = r'({0})\s*{{([^}}]*)}}'.format('|'.join(re.escape(k) for k in accent_map.keys()))

    def replacer(match):
        command = match.group(1)
        base_text = match.group(2)
        combining_char = accent_map.get(command)
        
        # Recursively process the inner text first to handle nested accents
        processed_base = replace_latex_accents(base_text)
        
        # Combine and normalize
        combined_sequence = processed_base + combining_char
        return unicodedata.normalize('NFC', combined_sequence)

    # Loop until no more replacements can be made to handle nesting
    while re.search(pattern, s):
        s = re.sub(pattern, replacer, s)
        
    return s


latex_to_html_entities = {
    '\\ldots': '&mldr;',
    '\\textregistered': '&reg;',
    '\\texttrademark': '&trade;',
    '\\textcopyright': '&copy;',
    '\\S': '&sect;',  # Section symbol
    '\\P': '&para;',   # Paragraph symbol (pilcrow)
    '\\textcircledP': '&copysr;', # Sound Recording Copyright - U+2117

    '\\textservicemark': '℠',
    '\\textcopyleft': '\u1f12f',


}


def replace_latex_symbols_from_dict(s, replacement_dict):
    """
    Iterates through a dictionary of LaTeX commands and their HTML
    replacements, applying them to a string.

    Args:
        s (str): The input string.
        replacement_dict (dict): A dictionary where keys are LaTeX commands
                                 (e.g., '\\textregistered') and values are
                                 their HTML replacements (e.g., '&reg;').

    Returns:
        str: The modified string.
    """
    # Iterate through each item in the dictionary
    for command, replacement in replacement_dict.items():
        # Escape the command to make it safe for use in a regex
        escaped_command = re.escape(command)
        
        # This pattern finds the command and one optional trailing space
        pattern = escaped_command + r' ?'
        
        # Perform the substitution
        s = re.sub(pattern, replacement, s)
        
    return s

def perform_substitutions(s):

    #s=s.replace('\x0c', '')  # Unsure if this is necessary

    s=s.replace('\u2029', '</p><p>')
    s=s.replace('\u2028', '<BR>')
    s=s.replace('\\\\', '\\')

    s=s.replace('\&', '&amp;')
    s=s.replace('\\hbox{-}', '\u2011')	# NON-BREAKING HYPHEN
    s=s.replace('\\,', '\u202f')     	# NARROW NO-BREAK SPACE
    s=s.replace('\\prime,', '\u2032')   # Prime

    s=replace_latex_break_command(s, 'linebreak', '<BR>')

    s=replace_latex_command(s, '\\textit', '<i>', '</i>')
    s=replace_latex_command(s, '\\textbf', '<strong>', '</strong>')
    s=replace_latex_command(s, '\\texttt', '<tt>', '</tt>')
    s=replace_latex_command(s, '\\textsubscript', '<sub>', '</sub>')
    s=replace_latex_command(s, '\\textsuperscript', '<sup>', '</sup>')
    s=replace_latex_command(s, '\\mbox', '<span>', '</span>')
    s=replace_latex_command(s, '\\engExpl', '<!-- ', ' -->')
    s=replace_latex_command(s, '\\tothe', '<sup>', '</sup>')
    s=replace_latex_environment(s, 'itemize', '</p><p><ul>', '</li></ul></p><p>')
    s=replace_latex_environment(s, 'enumerate', '</p><p><ol>', '</li></ol></p><p>')
    
    s=s.replace('\\item', '<li>')
    s=s.replace('<li> ', '<li>')
    s=s.replace(' <li>', '<li>')
    s=s.replace(' <li>', '<li>')


    s=s.replace('<BR></p>', '</p>')
    s=s.replace('<BR></li>', '</li>')
    s=s.replace('<BR><li>', '</li><li>')

    s=s.replace('\\par', '</p><p>')

    s=s.replace('\n', ' ')

    # handle defines.tex macros
    s=replace_latex_abbreviations(s)

    s=replace_ordinals_and_fix_spacing(s)

    # convert these to the more general qty{}{} form
    s=s.replace('\\num', '\\qty')
    s=s.replace('\\SI', '\\qty')

    # replace more complex units before the replace_latex_qty() call
    s=preprocess_units(s, string_replacements)

    # handle \qty{}{} with some units
    s=replace_latex_qty(s)

    s=replace_latex_symbols_from_dict(s, latex_to_html_entities)

    # some final cleanup

    s=remove_empty_listitems(s)
    s=remove_empty_paragraphs(s)
    s=s.replace(' </p>', '</p>')
    s=s.replace('\\\\', '\\')
    s=s.replace('\\textbackslash ', '\\')
    return s

def process_latex_in_blocks(s):
    """
    Safely processes a LaTeX string by separating text and math blocks.
    This version correctly identifies blocks by content, not by index.
    """
    # 1. First, remove all comments from the entire string.
    s = remove_latex_comments(s)

    # 2. Define a regex pattern to find and CAPTURE all math environments.
    pattern = r'(\$.*?\S\$|\\\(.*?\\\)|\\\[.*?\\\])'
    
    # 3. Split the string by this pattern.
    blocks = re.split(pattern, s)
    
    # 4. Process the blocks.
    processed_blocks = []
    for block in blocks:
        if not block: # Skip any empty strings that result from the split
            continue
            
        # *** THE CRITICAL FIX ***
        # Check if the block is a math block by looking at its first characters.
        if block.startswith('$') or block.startswith('\\(') or block.startswith('\\['):
            print(f"mathblock: {block}")
            # This is a math block, so we append it unchanged.
            processed_blocks.append(block)
        else:
            # This is a text block, so we can safely process it.
            print(f"textblock: {block}")
            processed_block = replace_latex_accents(block)
            # Add any other text-only replacements here.
            processed_block=perform_substitutions(processed_block)

            processed_blocks.append(processed_block)
            
    # 5. Reconstitute the final string.
    return "".join(processed_blocks)

def replace_math_alphabets(s):
    """
    Replaces LaTeX math alphabet commands like \\mathbb{C} with their
    corresponding Unicode characters.
    """
    
    # 1. Define mapping tables for each math alphabet command.
    #    These can be expanded as needed.
    mathbb_map = {
        'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼', 'F': '𝔽',
        'G': '𝔾', 'H': 'ℍ', 'I': '𝕀', 'J': '𝕁', 'K': '𝕂', 'L': '𝕃', 'M': '𝕄',
        'N': 'ℕ', 'O': '𝕆', 'P': 'ℙ',
        'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋',
        'U': '𝕌', 'V': '𝕍', 'W': '𝕎', 'X': '𝕏', 'Y': '𝕐', 'Z': 'ℤ',

        # lower case
        'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖',
        'f': '𝕗', 'g': '𝕘', 'h': '𝕙', 'i': '𝕚', '𝕛': '𝕛',
        'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟', 'o': '𝕠',
        'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥',
        'u': '𝕦', 'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪', 'z': '𝕫',

        # digits
        '0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜',
        '5': '𝟝', '6': '𝟞', '7': '𝟟', '8': '𝟠', '9': '𝟡',

        # Greek
        'Γ': 'ℾ', 'Π': 'ℿ', 'Σ': '⅀',
        'π': 'ℼ', 'γ': 'ℽ', 
        
    }

    # BB with italics
    mathbbit_map = {
        'D': 'ⅅ', 'd': 'ⅆ', 'e': 'ⅇ', 'i': 'ⅈ', 'j': 'ⅉ',
    }

    # VS2_roundhand = '\uFE01' # For \mathcal
    # upright, calligraphic style - roundhand
    mathcal_map = {
        'A': '\u1D49C\uFE01', 'B': '\u212C\uFE01', 'C': '\u1D49E\uFE01', 'D': '\u1D49F\uFE01', 
        'E': '\u2130\uFE01', 'F': '\u2131\uFE01', 'G': '\u1D4A2\uFE01', 'H': '\u210B\uFE01', 
        'I': '\u2110\uFE01', 'J': '\u1D4A5\uFE01', 'K': '\u1D4A6\uFE01', 'L': '\u2112\uFE01', 
        'M': '\u2133\uFE01', 'N': '\u1D4A9\uFE01', 'O': '\u1D4AA\uFE01', 'P': '\u1D4AB\uFE01', 
        'Q': '\u1D4AC\uFE01', 'R': '\u211B\uFE01', 'S': '\u1D4AE\uFE01', 'T': '\u1D4AF\uFE01', 
        'U': '\u1D4B0\uFE01', 'V': '\u1D4B1\uFE01', 'W': '\u1D4B2\uFE01', 'X': '\u1D4B3\uFE01', 
        'Y': '\u1D4B4\uFE01', 'Z': '\u1D4B5\uFE01',
        'a': '\u1D4B6\uFE01', 'b': '\u1D4B7\uFE01', 'c': '\u1D4B8\uFE01', 'd': '\u1D4B9\uFE01',
        'e': '\u212F\uFE01',  'f': '\u1D4BB\uFE01', 'g': '\u210A\uFE01',  'h': '\u1D4BD\uFE01',
        'i': '\u1D4BE\uFE01', 'j': '\u1D4BF\uFE01', 'k': '\u1D4C0\uFE01', 'l': '\u1D4C1\uFE01',
        'm': '\u1D4C\uFE01', 'n': '\u1D4C3\uFE01',  'o': '\u2134\uFE01',  'p': '\u1D4C5\uFE01',
        'q': '\u1D4C6\uFE01', 'r': '\u1D4C7\uFE01', 's': '\u1D4C8\uFE01', 't': '\u1D4C9\uFE01',
        'u': '\u1D4CA\uFE01', 'v': '\u1D4CB\uFE01', 'w': '\u1D4CC\uFE01', 'x': '\u1D4CD\uFE01',
        'y': '\u1D4CE\uFE01', 'z': '\u1D4CF\uFE01',
    }

        # upright, calligraphic style - roundhand
    mathcalbold_map = {
        'A': '\u1D4D0\uFE01', 'B': '\u1D4D1\uFE01', 'C': '\u1D4D2\uFE01', 'D': '\u1D4D3\uFE01', 
        'E': '\u1D4D4\uFE01', 'F': '\u1D4D5\uFE01', 'G': '\u1D4D6\uFE01', 'H': '\u1D4D7\uFE01', 
        'I': '\u1D4D8\uFE01', 'J': '\u1D4D9\uFE01', 'K': '\u1D4DA\uFE01', 'L': '\u1D4DB\uFE01', 
        'M': '\u1D4DC\uFE01', 'N': '\u1D4DD\uFE01', 'O': '\u1D4DE\uFE01', 'P': '\u1D4DF\uFE01', 
        'Q': '\u1D4E0\uFE01', 'R': '\u1D4E1\uFE01', 'S': '\u1D4E2\uFE01', 'T': '\u1D4E3\uFE01', 
        'U': '\u1D4E4\uFE01', 'V': '\u1D4E5\uFE01', 'W': '\u1D4E6\uFE01', 'X': '\u1D4E7\uFE01', 
        'Y': '\u1D4E8\uFE01', 'Z': '\u1D4E9\uFE01',
        'a': '\u1D4EA\uFE01', 'b': '\u1D4EB\uFE01', 'c': '\u1D4EC\uFE01', 'd': '\u1D4ED\uFE01',
        'e': '\u1D4EE\uFE01', 'f': '\u1D4EF\uFE01', 'g': '\u1D4F0\uFE01', 'h': '\u1D4F1\uFE01',
        'i': '\u1D4F2\uFE01', 'j': '\u1D4F3\uFE01', 'k': '\u1D4F4\uFE01', 'l': '\u1D4F5\uFE01',
        'm': '\u1D4F6\uFE01', 'm': '\u1D4F7\uFE01', 'o': '\u1D4F8\uFE01', 'p': '\u1D4F9\uFE01',
        'q': '\u1D4FA\uFE01', 'r': '\u1D4FB\uFE01', 's': '\u1D4FC\uFE01', 't': '\u1D4FD\uFE01',
        'u': '\u1D4FE\uFE01', 'v': '\u1D4FF\uFE01', 'w': '\u1D500\uFE01', 'x': '\u1D501\uFE01',
        'y': '\u1D502\uFE01', 'z': '\u1D503\uFE01',
    }

    
    # VS1_chancery = '\uFE00'  # For \mathscr
    # the more slanted, chancery or "script" style
    mathscr_map = {
        'A': '\u1D49C\uFE00', 'B': '\u212C\uFE00', 'C': '\u1D49E\uFE00', 'D': '\u1D49F\uFE00', 
        'E': '\u2130\uFE00', 'F': '\u2131\uFE00', 'G': '\u1D4A2\uFE00', 'H': '\u210B\uFE00', 
        'I': '\u2110\uFE00', 'J': '\u1D4A5\uFE00', 'K': '\u1D4A6\uFE00', 'L': '\u2112\uFE00', 
        'M': '\u2133\uFE00', 'N': '\u1D4A9\uFE00', 'O': '\u1D4AA\uFE00', 'P': '\u1D4AB\uFE00', 
        'Q': '\u1D4AC\uFE00', 'R': '\u211B\uFE00', 'S': '\u1D4AE\uFE00', 'T': '\u1D4AF\uFE00', 
        'U': '\u1D4B0\uFE00', 'V': '\u1D4B1\uFE00', 'W': '\u1D4B2\uFE00', 'X': '\u1D4B3\uFE00', 
        'Y': '\u1D4B4\uFE00', 'Z': '\u1D4B5\uFE00',
        'a': '\u1D4B6\uFE00', 'b': '\u1D4B7\uFE00', 'c': '\u1D4B8\uFE00', 'd': '\u1D4B9\uFE00',
        'e': '\u212F\uFE00',  'f': '\u1D4BB\uFE00', 'g': '\u210A\uFE00',  'h': '\u1D4BD\uFE00',
        'i': '\u1D4BE\uFE00', 'j': '\u1D4BF\uFE00', 'k': '\u1D4C0\uFE00', 'l': '\u1D4C1\uFE00',
        'm': '\u1D4C\uFE00',  'n': '\u1D4C3\uFE00', 'o': '\u2134\uFE00',  'p': '\u1D4C5\uFE00',
        'q': '\u1D4C6\uFE00', 'r': '\u1D4C7\uFE00', 's': '\u1D4C8\uFE00', 't': '\u1D4C9\uFE00',
        'u': '\u1D4CA\uFE00', 'v': '\u1D4CB\uFE00', 'w': '\u1D4CC\uFE00', 'x': '\u1D4CD\uFE00',
        'y': '\u1D4CE\uFE00', 'z': '\u1D4CF\uFE00',

    }

    mathscrbold_map = {
        'A': '\u1D4D0\uFE00', 'B': '\u1D4D1\uFE00', 'C': '\u1D4D2\uFE00', 'D': '\u1D4D3\uFE00', 
        'E': '\u1D4D4\uFE00', 'F': '\u1D4D5\uFE00', 'G': '\u1D4D6\uFE00', 'H': '\u1D4D7\uFE00', 
        'I': '\u1D4D8\uFE00', 'J': '\u1D4D9\uFE00', 'K': '\u1D4DA\uFE00', 'L': '\u1D4DB\uFE00', 
        'M': '\u1D4DC\uFE00', 'N': '\u1D4DD\uFE00', 'O': '\u1D4DE\uFE00', 'P': '\u1D4DF\uFE00', 
        'Q': '\u1D4E0\uFE00', 'R': '\u1D4E1\uFE00', 'S': '\u1D4E2\uFE00', 'T': '\u1D4E3\uFE00', 
        'U': '\u1D4E4\uFE00', 'V': '\u1D4E5\uFE00', 'W': '\u1D4E6\uFE00', 'X': '\u1D4E7\uFE00', 
        'Y': '\u1D4E8\uFE00', 'Z': '\u1D4E9\uFE00',
        'a': '\u1D4EA\uFE00', 'b': '\u1D4EB\uFE00', 'c': '\u1D4EC\uFE00', 'd': '\u1D4ED\uFE00',
        'e': '\u1D4EE\uFE00', 'f': '\u1D4EF\uFE00', 'g': '\u1D4F0\uFE00', 'h': '\u1D4F1\uFE00',
        'i': '\u1D4F2\uFE00', 'j': '\u1D4F3\uFE00', 'k': '\u1D4F4\uFE00', 'l': '\u1D4F5\uFE00',
        'm': '\u1D4F6\uFE00', 'm': '\u1D4F7\uFE00', 'o': '\u1D4F8\uFE00', 'p': '\u1D4F9\uFE00',
        'q': '\u1D4FA\uFE00', 'r': '\u1D4FB\uFE00', 's': '\u1D4FC\uFE00', 't': '\u1D4FD\uFE00',
        'u': '\u1D4FE\uFE00', 'v': '\u1D4FF\uFE00', 'w': '\u1D500\uFE00', 'x': '\u1D501\uFE00',
        'y': '\u1D502\uFE00', 'z': '\u1D503\uFE00',
    }


    mathfrak_map = {
        # upper case

        'A': '𝔄', 'B': '𝔅', 'C': 'ℭ', 'D': '𝔇', 'E': '𝔈',
        'F': '𝔉', 'G': '𝔊', 'H': 'ℌ', 'I': 'ℑ', 'J': '𝔍',
        'K': '𝔎', 'L': '𝔏', 'M': '𝔐', 'N': '𝔑', 'O': '𝔒',
        'P': '𝔓', 'Q': '𝔔', 'R': 'ℜ', 'S': '𝔖', 'T': '𝔗',
        'U': '𝔘', 'V': '𝔙', 'W': '𝔚', 'X': '𝔛', 'Y': '𝔜', 'Z': 'ℨ',

        # lower case
        'a': '𝔞', 'b': '𝔟', 'c': '𝔠', 'd': '𝔡', 'e': '𝔢',
        'f': '𝔣', 'g': '𝔤', 'h': '𝔥', 'i': '𝔦', 'j': '𝔧',
        'k': '𝔨', 'l': '𝔩', 'm': '𝔪', 'n': '𝔫', 'o': '𝔬',
        'p': '𝔭', 'q': '𝔮', 'r': '𝔯', 's': '𝔰', 't': '𝔱',
        'u': '𝔲', 'v': '𝔳', 'w': '𝔴', 'x': '𝔵', 'y': '𝔶', 'z': '𝔷',

        # digits
    }

    mbfrak_map = {
        # upper case

        'A': '𝕬', 'B': '𝕭', 'C': '𝕮', 'D': '𝕯', 'E': '𝕰',
        'F': '𝕱', 'G': '𝕲', 'H': '𝕳', 'I': '𝕴', 'J': '𝕵',
        'K': '𝕶', 'L': '𝕷', 'M': '𝕸', 'N': '𝕹', 'O': '𝕺',
        'P': '𝕻', 'Q': '𝕼', 'R': '𝕽', 'S': '𝕾', 'T': '𝕿',
        'U': '𝖀', 'V': '𝖁', 'W': '𝖂', 'X': '𝖃', 'Y': '𝖄', 'Z': '𝖅',

        # lower case
        'a': '𝖆', 'b': '𝖇', 'c': '𝖈', 'd': '𝖉', 'e': '𝖊',
        'f': '𝖋', 'g': '𝖌', 'h': '𝖍', 'i': '𝖎', 'j': '𝖏',
        'k': '𝖐', 'l': '𝖑', 'm': '𝖒', 'n': '𝖓', 'o': '𝖔',
        'p': '𝖕', 'q': '𝖖', 'r': '𝖗', 's': '𝖘', 't': '𝖙',
        'u': '𝖚', 'v': '𝖛', 'w': '𝖜', 'x': '𝖝', 'y': '𝖞', 'z': '𝖟',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
        '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗',

    }

    # sans serif
    mathsf_map = {
        # upper case

        'A': '𝖠', 'B': '𝖡', 'C': '𝖢', 'D': '𝖣', 'E': '𝖤',
        'F': '𝖥', 'G': '𝖦', 'H': '𝖧', 'I': '𝖨', 'J': '𝖩',
        'K': '𝖪', 'L': '𝖫', 'M': '𝖬', 'N': '𝖭', 'O': '𝖮',
        'P': '𝖯', 'Q': '𝖰', 'R': '𝖱', 'S': '𝖲', 'T': '𝖳',
        'U': '𝖴', 'V': '𝖵', 'W': '𝖶', 'X': '𝖷', 'Y': '𝖸', 'Z': '𝖹',

        # lower case
        'a': '𝖺', 'b': '𝖻', 'c': '𝖼', 'd': '𝖽', 'e': '𝖾',
        'f': '𝖿', 'g': '𝗀', 'h': '𝗁', 'i': '𝗂', 'j': '𝗃',
        'k': '𝗄', 'l': '𝗅', 'm': '𝗆', 'n': '𝗇', 'o': '𝗈',
        'p': '𝗉', 'q': '𝗊', 'r': '𝗋', 's': '𝗌', 't': '𝗍',
        'u': '𝗎', 'v': '𝗏', 'w': '𝗐', 'x': '𝗑', 'y': '𝗒', 'z': '𝗓',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦',
        '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫',

    }

    mathsfit_map = {
        # upper case

        'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌',
        'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐', 'J': '𝘑',
        'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖',
        'P': '𝘗', 'Q': '𝘘', 'R': '𝘙', 'S': '𝘚', 'T': '𝘛',
        'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡',

        # lower case
        'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦',
        'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪', 'j': '𝘫',
        'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰',
        'p': '𝘱', 'q': '𝘲', 'r': '𝘳', 's': '𝘴', 't': '𝘵',
        'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦',
        '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫',

    }

    # sans serif bold
    mathbfsf_map = {
        # upper case

        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘',
        'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
        'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢',
        'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
        'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',

        # lower case
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲',
        'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
        'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼',
        'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
        'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',

        # Greek
        # Greek Letters (Uppercase)
        'Α': '𝝖', 'Β': '𝝗', 'Γ': '𝝘', 'Δ': '𝝙', 'Ε': '𝝚', 'Ζ': '𝝛', 
        'Η': '𝝜', 'Θ': '𝝝', 'Ι': '𝝞', 'Κ': '𝝟',  'Λ': '𝝠', 'Μ': '𝝡',
        'Ν': '𝝢', 'Ξ': '𝝣', 'Ο': '𝝤', 'Π': '𝝥', 'Ρ': '𝝦', 'ϴ': '𝝧',
        'Σ': '𝝨', 'Τ': '𝝩', 'ϒ': '𝝪', 'Φ': '𝝫', 'Χ': '𝝬', 'Ψ': '𝝭',
        'Ω': '𝝮', '∇': '𝝯',

        # Greek Letters (Lowercase)
        'α': '𝝰', 'β': '𝝱', 'γ': '𝝲', 'δ': '𝝳', 'ε': '𝝴', 'ζ': '𝝵',
        'η': '𝝶', 'θ': '𝝷', 'ι': '𝝸', 'κ': '𝝹', 'λ': '𝝺', 'μ': '𝝻', 
        'ν': '𝝼', 'ξ': '𝝽', 'ο': '𝝾', 'π': '𝝿', 'ρ': '𝞀', 'ς': '𝞁',
        'σ': '𝞂', 'τ': '𝞃', 'υ': '𝞄', 'φ': '𝞅', 'χ': '𝞆', 'ψ': '𝞇',
        'ω': '𝞈',
        '∂': '𝞉', 'ϵ': '𝞊',




    }

    # sans serif bold italic
    mathbfsfit_map = {
        # upper case

        'A': '𝘼', 'B': '𝘽', 'C': '𝘾', 'D': '𝘿', 'E': '𝙀',
        'F': '𝙁', 'G': '𝙂', 'H': '𝙃', 'I': '𝙄', 'J': '𝙅',
        'K': '𝙆', 'L': '𝙇', 'M': '𝙈', 'N': '𝙉', 'O': '𝙊',
        'P': '𝙋', 'Q': '𝙌', 'R': '𝙍', 'S': '𝙎', 'T': '𝙏',
        'U': '𝙐', 'V': '𝙑', 'W': '𝙒', 'X': '𝙓', 'Y': '𝙔', 'Z': '𝙕',

        # lower case
        'a': '𝙖', 'b': '𝙗', 'c': '𝙘', 'd': '𝙙', 'e': '𝙚',
        'f': '𝙛', 'g': '𝙜', 'h': '𝙝', 'i': '𝙞', 'j': '𝙟',
        'k': '𝙠', 'l': '𝙡', 'm': '𝙢', 'n': '𝙣', 'o': '𝙤',
        'p': '𝙥', 'q': '𝙦', 'r': '𝙧', 's': '𝙨', 't': '𝙩',
        'u': '𝙪', 'v': '𝙫', 'w': '𝙬', 'x': '𝙭', 'y': '𝙮', 'z': '𝙯',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',

        # Greek
        # Greek Letters (Uppercase)
        'Α': '𝞐', 'Β': '𝞑', 'Γ': '𝞒', 'Δ': '𝞓', 'Ε': '𝞔', 'Ζ': '𝞕', 
        'Η': '𝞖', 'Θ': '𝞗', 'Ι': '𝞘', 'Κ': '𝞙',  'Λ': '𝞚', 'Μ': '𝞛',
        'Ν': '𝞜', 'Ξ': '𝞝', 'Ο': '𝞞', 'Π': '𝞟', 'Ρ': '𝞠', 'ϴ': '𝞡',
        'Σ': '𝞢', 'Τ': '𝞣', 'ϒ': '𝞤', 'Φ': '𝞥', 'Χ': '𝞦', 'Ψ': '𝞧',
        'Ω': '𝞨', '∇': '𝞩',

        # Greek Letters (Lowercase)
        'α': '𝞪', 'β': '𝞫', 'γ': '𝞬', 'δ': '𝞭', 'ε': '𝞮', 'ζ': '𝞯',
        'η': '𝞰', 'θ': '𝞱', 'ι': '𝞲', 'κ': '𝞳', 'λ': '𝞴', 'μ': '𝞵', 
        'ν': '𝞶', 'ξ': '𝞷', 'ο': '𝞸', 'π': '𝞹', 'ρ': '𝞺', 'ς': '𝞻',
        'σ': '𝞼', 'τ': '𝞽', 'υ': '𝞾', 'φ': '𝞿', 'χ': '𝟀', 'ψ': '𝟁',
        'ω': '𝟂',
        '∂': '𝟃', 'ϵ': '𝟄',




    }

    # bold italic
    mathbfit_map = {
        # upper case

        'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬',
        'F': '𝑭', 'G': '𝑮', 'H': '𝑯', 'I': '𝑰', 'J': '𝑱',
        'K': '𝑲', 'L': '𝑳', 'M': '𝑴', 'N': '𝑵', 'O': '𝑶',
        'P': '𝑷', 'Q': '𝑸', 'R': '𝑹', 'S': '𝑺', 'T': '𝑻',
        'U': '𝑼', 'V': '𝑽', 'W': '𝑾', 'X': '𝑿', 'Y': '𝒀', 'Z': '𝒁',

        # lower case
        'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆',
        'f': '𝒇', 'g': '𝒈', 'h': '𝒉', 'i': '𝒊', 'j': '𝒋',
        'k': '𝒌', 'l': '𝒍', 'm': '𝒎', 'n': '𝒏', 'o': '𝒐',
        'p': '𝒑', 'q': '𝒒', 'r': '𝒓', 's': '𝒔', 't': '𝒕',
        'u': '𝒖', 'v': '𝒗', 'w': '𝒘', 'x': '𝒙', 'y': '𝒚', 'z': '𝒛',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',

        # Greek
        # Greek Letters (Uppercase)
        'Α': '𝜜', 'Β': '𝜝', 'Γ': '𝜞', 'Δ': '𝜟', 'Ε': '𝜠', 'Ζ': '𝜡', 
        'Η': '𝜢', 'Θ': '𝜣', 'Ι': '𝜤', 'Κ': '𝜥',  'Λ': '𝜦', 'Μ': '𝜧',
        'Ν': '𝜨', 'Ξ': '𝜩', 'Ο': '𝜪', 'Π': '𝜫', 'Ρ': '𝜬', 'ϴ': '𝜭',
        'Σ': '𝜮', 'Τ': '𝜯', 'ϒ': '𝜰', 'Φ': '𝜱', 'Χ': '𝜲', 'Ψ': '𝜳',
        'Ω': '𝜴', '∇': '𝜵',

        # Greek Letters (Lowercase)
        'α': '𝜶', 'β': '𝜷', 'γ': '𝜸', 'δ': '𝜹', 'ε': '𝜺', 'ζ': '𝜻',
        'η': '𝜼', 'θ': '𝜽', 'ι': '𝜾', 'κ': '𝜿', 'λ': '𝝀', 'μ': '𝝁', 
        'ν': '𝝂', 'ξ': '𝝃', 'ο': '𝝄', 'π': '𝝅', 'ρ': '𝝆', 'ς': '𝝇',
        'σ': '𝝈', 'τ': '𝝉', 'υ': '𝝊', 'φ': '𝝋', 'χ': '𝝌', 'ψ': '𝝍',
        'ω': '𝝎',
        '∂': '𝝏', 'ϵ': '𝝐',
    }

    # for \symup - relly just a NOP
    math_upright_map = {
        # Uppercase Latin
        'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G',
        'H': 'H', 'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N',
        'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U',
        'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',

        # Lowercase Latin
        'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g',
        'h': 'h', 'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
        'o': 'o', 'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u',
        'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',

        # Digits
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
        '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',

        # Greek Uppercase Upright
        'Α': 'Α', 'Β': 'Β', 'Γ': 'Γ', 'Δ': 'Δ', 'Ε': 'Ε', 'Ζ': 'Ζ', 'Η': 'Η',
        'Θ': 'Θ', 'Ι': 'Ι', 'Κ': 'Κ', 'Λ': 'Λ', 'Μ': 'Μ', 'Ν': 'Ν', 'Ξ': 'Ξ',
        'Ο': 'Ο', 'Π': 'Π', 'Ρ': 'Ρ', 'Σ': 'Σ', 'Τ': 'Τ', 'Υ': 'Υ', 'Φ': 'Φ',
        'Χ': 'Χ', 'Ψ': 'Ψ', 'Ω': 'Ω',

        # Greek Lowercase Upright
        'α': 'α', 'β': 'β', 'γ': 'γ', 'δ': 'δ', 'ε': 'ε', 'ζ': 'ζ', 'η': 'η',
        'θ': 'θ', 'ι': 'ι', 'κ': 'κ', 'λ': 'λ', 'μ': 'μ', 'ν': 'ν', 'ξ': 'ξ',
        'ο': 'ο', 'π': 'π', 'ρ': 'ρ', 'σ': 'σ', 'τ': 'τ', 'υ': 'υ', 'φ': 'φ',
        'χ': 'χ', 'ψ': 'ψ', 'ω': 'ω',
    }

    # For \symit (Italic)
    math_italic_map = {
        'A': '𝐴', 'B': '𝐵', 'C': '𝐶', 'D': '𝐷', 'E': '𝐸', 'F': '𝐹', 'G': '𝐺', 'H': '𝐻',
        'I': '𝐼', 'J': '𝐽', 'K': '𝐾', 'L': '𝐿', 'M': '𝑀', 'N': '𝑁', 'O': '𝑂', 'P': '𝑃',
        'Q': '𝑄', 'R': '𝑅', 'S': '𝑆', 'T': '𝑇', 'U': '𝑈', 'V': '𝑉', 'W': '𝑊', 'X': '𝑋',
        'Y': '𝑌', 'Z': '𝑍',
        'a': '𝑎', 'b': '𝑏', 'c': '𝑐', 'd': '𝑑', 'e': '𝑒', 'f': '𝑓', 'g': '𝑔', 'h': 'ℎ',
        'i': '𝑖', 'j': '𝑗', 'k': '𝑘', 'l': '𝑙', 'm': '𝑚', 'n': '𝑛', 'o': '𝑜', 'p': '𝑝',
        'q': '𝑞', 'r': '𝑟', 's': '𝑠', 't': '𝑡', 'u': '𝑢', 'v': '𝑣', 'w': '𝑤', 'x': '𝑥',
        'y': '𝑦', 'z': '𝑧',
        'Α': '\u1D6E2', 'Β': '\u1D6E3', 'Γ': '\u1D6E4', 'Δ': '\u1D6E5', 'Ε': '\u1D6E6', 'Ζ': '\u1D6E7',
        'Η': '\u1D6E8', 'Θ': '\u1D6E9', 'Ι': '\u1D6EA', 'Κ': '\u1D6EB', 'Λ': '\u1D6EC', 'Μ': '\u1D6ED',
        'Ν': '\u1D6EE', 'Ξ': '\u1D6EF', 'Ο': '\u1D6F0', 'Π': '\u1D6F1', 'Ρ': '\u1D6F2', 'ϴ': '\u1D6F3',
        'Σ': '\u1D6F4', 'Τ': '\u1D6F5', 'Υ': '\u1D6F6', 'Φ': '\u1D6F7', 'Χ': '\u1D6F8', 'Ψ': '\u1D6F9',
        'Ω': '\u1D6FA', '∇': '\u1D6FB',
        'α': '\u1D6FC', 'β': '\u1D6FD', 'γ': '\u1D6FE', 'δ': '\u1D6FF', 'ε': '\u1D700', 'ζ': '\u1D701',
        'η': '\u1D702', 'θ': '\u1D703', 'ι': '\u1D704', 'κ': '\u1D705', 'λ': '\u1D706', 'μ': '\u1D707',
        'ν': '\u1D708', 'ξ': '\u1D709', 'ο': '\u1D70A', 'π': '\u1D70B', 'ρ': '\u1D70C', 'ς': '\u1D70D',
        'σ': '\u1D70E', 'τ': '\u1D70F', 'υ': '\u1D710', 'φ': '\u1D711', 'χ': '\u1D712', 'ψ': '\u1D713',
        'ω': '\u1D714',
        '∂': '\u1D715', 'ϵ': '\u1D716',
    }

    # For \symbf (Bold)
    math_bold_map = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇',
        'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏',
        'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗',
        'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡',
        'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩',
        'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱',
        'y': '𝐲', 'z': '𝐳',
        'Α': '\u1D6A8', 'Β': '\u1D6A9', 'Γ': '\u1D6AA', 'Δ': '\u1D6AB', 'Ε': '\u1D6AC', 'Ζ': '\1D6AD',
        'Η': '\u1D6AE', 'Θ': '\u1D6AF', 'Ι': '\u1D6B0', 'Κ': '\u1D6B1', 'Λ': '\u1D6B2', 'Μ': '\u1D6B3',
        'Ν': '\u1D6B4', 'Ξ': '\u1D6B5', 'Ο': '\u1D6B6', 'Π': '\u1D6B7', 'Ρ': '\u1D6B8', 'θ': 'u1D6B9',
        'Σ': '\u1D6BA', 'Τ': '\u1D6BB', 'Υ': '\u1D6BC', 'Φ': '\u1D6BD', 'Χ': '\u1D6BE', 'Ψ': '\u1D6B',
        'Ω': '\u1D6C0', '∇': '\u1D6C1',
        'α': '\u1D6C2', 'β': '\u1D6C3', 'γ': '\u1D6C4', 'δ': '\u1D6C5', 'ε': '\u1D6C6', 'ζ': '\u1D6C7',
        'η': '\u1D6C8', 'θ': '\u1D6C9', 'ι': '\u1D6CA', 'κ': '\u1D6CB', 'λ': '\u1D6CC', 'μ': '\u1D6CD',
        'ν': '\u1D6CE', 'ξ': '\u1D6CF', 'ο': '\u1D6D0', 'π': '\u1D6D1', 'ρ': '\u1D6D2', 'ς': '\u1D6D3',
        'σ': '\u1D6D4', 'τ': '\u1D6D5', 'υ': '\u1D6D6', 'φ': '\u1D6D7', 'χ': '\u1D6D8', 'ψ': '\u1D6D9',
        'ω': '\u1D6DA', '∂': '\u1D6DB', 'ϵ': '\u1D6DC',

        # digits - these are all "Mathematical Bold Digit"
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',

    }

    # For \symsf (sans-serif)
    math_sans_map = {
        'A': '\u1D5A0', 'B': '\u1D5A1', 'C': '\u1D5A2', 'D': '\u1D5A3', 'E': '\u1D5A4',
        'F': '\u1D5A5', 'G': '\u1D5A6', 'H': '\u1D5A7', 'I': '\u1D5A8', 'J': '\u1D5A9',
        'K': '\u1D5AA', 'L': '\u1D5AB', 'M': '\u1D5AC', 'N': '\u1D5AD', 'O': '\u1D5AE',
        'P': '\u1D5AF', 'Q': '\u1D5B0', 'R': '\u1D5B1', 'S': '\u1D5B2', 'T': '\u1D5B3',
        'U': '\u1D5B4', 'V': '\u1D5B5', 'W': '\u1D5B6', 'X': '\u1D5B7', 'Y': '\u1D5B8', 'Z': '\u1D5B9',
        'a': '\u1D5BA', 'b': '\u1D5BB', 'c': '\u1D5BC', 'd': '\u1D5BD', 'e': '\u1D5BE',
        'f': '\u1D5BF', 'g': '\u1D5C0', 'h': '\u1D5C1', 'i': '\u1D5C2', 'j': '\u1D5C3',
        'k': '\u1D5C4', 'l': '\u1D5C5', 'm': '\u1D5C6', 'n': '\u1D5C7', 'o': '\u1D5C8',
        'p': '\u1D5C9', 'q': '\u1D5CA', 'r': '\u1D5CB', 's': '\u1D5CC', 't': '\u1D5CD',
        'u': '\u1D5CE', 'v': '\u1D5CF', 'w': '\u1D5D0', 'x': '\u1D5D1', 'y': '\u1D5D2', 'z': '\u1D5D3',

        # digits - these are all "Mathematical Bold Digit"
        '0': '\u1D7E2', '1': '\u1D7E3', '2': '\u1D7E4', '3': '\u1D7E5', '4': '\u1D7E6',
        '5': '\u1D7E7', '6': '\u1D7E8', '7': '\u1D7E9', '8': '\u1D7EA', '9': '\u1D7EB',

    }

    # For \symtt (mono)
    math_mono_map = {
        'A': '\u1D670', 'B': '\u1D671', 'C': '\u1D672', 'D': '\u1D673', 'E': '\u1D674',
        'F': '\u1D675', 'G': '\u1D676', 'H': '\u1D677', 'I': '\u1D678', 'J': '\u1D679',
        'K': '\u1D67A', 'L': '\u1D67B', 'M': '\u1D67C', 'N': '\u1D67D', 'O': '\u1D67E',
        'P': '\u1D67F', 'Q': '\u1D680', 'R': '\u1D681', 'S': '\u1D682', 'T': '\u1D683',
        'U': '\u1D684', 'V': '\u1D685', 'W': '\u1D686', 'X': '\u1D687', 'Y': '\u1D688', 'Z': '\u1D689',
        'a': '\u1D68A', 'b': '\u1D68B', 'c': '\u1D68C', 'd': '\u1D68D', 'e': '\u1D68E',
        'f': '\u1D68F', 'g': '\u1D690', 'h': '\u1D691', 'i': '\u1D692', 'j': '\u1D693',
        'k': '\u1D694', 'l': '\u1D695', 'm': '\u1D696', 'n': '\u1D697', 'o': '\u1D698',
        'p': '\u1D699', 'q': '\u1D69A', 'r': '\u1D69B', 's': '\u1D69C', 't': '\u1D69D',
        'u': '\u1D69E', 'v': '\u1D69F', 'w': '\u1D6A0', 'x': '\u1D6A1', 'y': '\u1D6A2', 'z': '\u1D6A3',

        # digits - these are all "Mathematical Bold Digit"
        '0': '\u1D7F6', '1': '\u1D7F7', '2': '\u1D7F8', '3': '\u1D7F9', '4': '\u1D7FA',
        '5': '\u1D7FB', '6': '\u1D7FC', '7': '\u1D7FD', '8': '\u1D7FE', '9': '\u1D7FF',

    }


    # 2. Create a master dictionary mapping the command to its character table.
    math_alphabet_commands = {
        '\\symup': math_upright_map,
        '\\symit': math_italic_map,
        '\\symbf': math_bold_map,
        '\\symsf': math_sans_map,
        '\\symtt': math_mono_map,

        '\\mathbb': mathbb_map,
        '\\symbb': mathbb_map,  # new unicode-math command

        '\\mathbbit': mathbbit_map,
        '\\symbbit': mathbbit_map,


        '\\mathds': mathbb_map, # this uses another font, but maps to the same unicode codepoints

        '\\mathcal': mathcal_map,
        '\\symcal': mathcal_map,
        '\\symbfcal': mathcalbold_map,
        '\\mathbfcal': mathcalbold_map,

        
        '\\mathscr': mathscr_map,
        '\\symscr': mathscr_map,
        '\\symbfscr': mathscrbold_map,
        '\\mathbfscr': mathscrbold_map,


        '\\mathfrak': mathfrak_map,
        '\\symfrak': mathfrak_map,
        '\\textfrak': mathfrak_map,

        '\\mbfrak':   mbfrak_map,
        '\\symbffrak':  mbfrak_map,
        '\\mathbffrak':  mbfrak_map,

        '\\mathsf': mathsf_map,
        '\\symsf': mathsf_map,
        '\\symsfit': mathsfit_map,
        '\\mathsfit':  mathsfit_map,
        '\\mathbfsf': mathbfsf_map,
        '\\symbfsf': mathbfsf_map,

        '\\mathbfit': mathbfit_map,
        '\\symbfit': mathbfit_map,

        # Add other alphabets if needed

    }

    # 3. Iterate through the commands and perform the replacements.
    for command, char_map in math_alphabet_commands.items():
        escaped_command = re.escape(command)
        # Pattern finds the command and captures the single letter in braces.
        pattern = escaped_command + r'\s*\{([A-Za-z])\}'
        
        def replacer(match):
            char_to_replace = match.group(1)
            # Look up the captured letter in the correct character map.
            # If not found, return the original full match to be safe.
            return char_map.get(char_to_replace, match.group(0))

        s = re.sub(pattern, replacer, s)
        
    return s

def convert_latex_math_to_unicode(s):
    """
    Converts a wider range of LaTeX math commands found in titles
    to their Unicode equivalents.
    """
    s = s.replace("'''", "‴") # Triple Prime (U+2034)
    s = s.replace("''", "″")  # Double Prime (U+2033)
    s = s.replace("'", "′")   # Prime (U+2032)
    s=s.replace('\\to,', '→')   # Rightwards Arrow - &rightarrow;



    # 1. A much more comprehensive mapping for Greek letters and common symbols.
    symbol_map = {
        # Greek Letters (Uppercase)
        '\\Gamma': 'Γ', '\\Delta': 'Δ', '\\Theta': 'Θ', '\\Lambda': 'Λ',
        '\\Xi': 'Ξ', '\\Pi': 'Π', '\\Sigma': 'Σ',
        #'\\Upsilon': 'Υ', # Incorrect: Standard Greek Upsilon (U+03A5)
        '\\Upsilon': 'ϒ',  # Correct: Greek Upsilon with hook symbol (U+03D2)
        '\\Phi': 'Φ', '\\Psi': 'Ψ', '\\Omega': 'Ω', '\\nabla': '∇', '\\Theta': 'Θ',
        # Greek Letters (Lowercase)
        '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\delta': 'δ',
        '\\epsilon': 'ε', '\\varepsilon': 'ϵ', '\\zeta': 'ζ', '\\eta': 'η',
        '\\theta': 'θ', '\\vartheta': 'ϑ', '\\iota': 'ι', '\\kappa': 'κ',
        '\\lambda': 'λ', '\\mu': 'μ', '\\nu': 'ν', '\\xi': 'ξ',
        '\\pi': 'π', '\\varpi': 'ϖ', '\\rho': 'ρ', '\\varrho': 'ϱ',
        '\\sigma': 'σ', '\\varsigma': 'ς', '\\tau': 'τ', '\\upsilon': 'υ',
        '\\phi': 'φ', '\\varphi': 'ϕ', '\\chi': 'χ', '\\psi': 'ψ',
        '\\omega': 'ω',  '\\theta': 'θ',

        # script l (used for leptons)
        '\\ell': 'ℓ',
        # Common Math Symbols
        '\\pm': '±', '\\times': '×', '\\div': '÷',
        '\\leq': '≤', '\\geq': '≥', '\\neq': '≠',
        '\\approx': '≈', '\\sim': '∼', '\\infty': '∞',
        '\\ldots': '…', '\\cdot': '·', '\\circ': '◦',
        '\\in': '∈', '\\otimes': '⊗', '\\oplus': '⊕',
        '\\sum': '∑', '\\prod': '∏', '\\sqrt': '√', # Handle sqrt with arg separately if needed
        '\\prime': "′",   # Prime (U+2032)
        '\\dprime': "″",  # Double Prime (U+2033)
        '\\prime': "‴",   # Triple Prime (U+2034)
    }

    # Mappings for superscripts and subscripts
    superscript_map = {
        # Digits
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',

        # Punctuation & Operators
        '+': '⁺', # 	U+207A
        '-': '⁻', #	U+207B
        '=': '⁼', #	U+207C
        '(': '⁽', #	U+207D
        ')': '⁾', #	U+207E

        # Uppercase Latin
        'A': 'ᴬ', #	U+1D2C
        'B': 'ᴮ', #	U+1D2E
        # C is missing
        'D': 'ᴰ', #	U+1D30
        'E': 'ᴱ', #	U+1D31
        # F is missing
        'G': 'ᴳ', #	U+1D33
        'H': 'ᴴ', #	U+1D34
        'I': 'ᴵ', #	U+1D35
        'J': 'ᴶ', #	U+1D36
        'K': 'ᴷ', #	U+1D37
        'L': 'ᴸ', #	U+1D38
        'M': 'ᴹ', #	U+1D39
        'N': 'ᴺ', #	U+1D3A
        'O': 'ᴼ', #	U+1D3C
        'P': 'ᴾ', #	U+1D3E
        # Q is missing
        'R': 'ᴿ', #	U+1D3F
        # S is missing
        'T': 'ᵀ', #	U+1D40
        'U': 'ᵁ', #	U+1D41
        # V is mssing
        'W': 'ᵂ', #	U+1D42
        # X, Y, and Z are missing


        # Lowercase Latin
        'a': 'ᵃ', #	U+1D43
        'b': 'ᵇ', #	U+1D47
        'c': 'ᶜ', #	U+1D9C
        'd': 'ᵈ', #	U+1D48
        'e': 'ᵈ', #	U+1D48
        'f': 'ᶠ', #	U+1DA0
        'g': 'ᵍ', #	U+1D4D
        'h': 'ʰ', #	U+02B0
        'i': 'ⁱ', #	U+2071
        'j': 'ʲ', #	U+02B2
        'k': 'ᵏ', #	U+1D4F
        'l': 'ˡ', #	U+02E1
        'm': 'ᵐ', #	U+1D50
        'n': 'ⁿ', #	U+207F
        'o': 'ᵒ', #	U+1D52
        'p': 'ᵖ', #	U+1D56
        # q is missing
        'r': 'ʳ', #	U+02B3
        's': 'ˢ', #	U+02E2
        't': 'ᵗ', #	U+1D57
        'u': 'ᵘ', #	U+1D58
        'v': 'ᵛ', #	U+1D5B
        'w': 'ʷ', #	U+02B7
        'x': 'ˣ', #	U+02E3
        'y': 'ʸ', #	U+02B8
        'z': 'ᶻ', #	U+1DBB

        # Greek
        'α': 'ᵅ', #	U+1D45
        'β': 'ᵝ', #	U+1D5D
        'γ': 'ᵞ', #	U+1D5E
        'δ': 'ᵟ', #	U+1D5F
        'φ': 'ᵠ', #	U+1D60
        'χ': 'ᵡ', #	U+1D61
    }

    subscript_map   = {
        # Digits
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',

        # Punctuation & Operators
        '+': '₊', #	U+208A
        '-': '₋', #	U+208B
        '=': '₌', #	U+208C
        '(': '₍', #	U+208D
        ')': '₎', #	U+208E

        # Lowercase Latin
        'a': 'ₐ', #	U+2090
        'e': 'ₑ', #	U+2091
        'h': 'ₕ', #	U+2095
        'i': 'ᵢ', #	U+1D62
        'j': 'ⱼ', #	U+2C7C
        'k': 'ₖ', #	U+2096
        'l': 'ₗ', #	U+2097
        'm': 'ₘ', #	U+2098
        'n': 'ₙ', #	U+2099
        'o': 'ₒ', #	U+2092
        'p': 'ₚ', #	U+209A
        'r': 'ᵣ', #	U+1D63
        's': 'ₛ', #	U+209B
        't': 'ₜ', #	U+209C
        'u': 'ᵤ', #	U+1D64
        'v': 'ᵥ', #	U+1D65
        'x': 'ₓ', #	U+2093

        # Greek
        'β': 'ᵦ', #	U+1D66
        'γ': 'ᵧ', #	U+1D67
        'ρ': 'ᵨ', #	U+1D68
        'φ': 'ᵩ', #	U+1D69
        'χ': 'ᵪ', #	U+1D6A
    }

    # Replace simple, no-argument commands first
    for command, unicode_char in symbol_map.items():
        s = s.replace(command, unicode_char)

    # Replace superscripts
    def sup_replacer(match):
        content = match.group(1)
        # Try to use the Unicode map first
        unicode_chars = [superscript_map.get(char, None) for char in content]
        if all(unicode_chars):
            return "".join(unicode_chars)
        # If any character is not in the map, fall back to HTML tags
        else:
            return f'<sup>{content}</sup>'
    s = re.sub(r'\^\{?([^}]+)\}?', sup_replacer, s)

    # Replace subscripts
    def sub_replacer(match):
        content = match.group(1)
        unicode_chars = [subscript_map.get(char, None) for char in content]
        if all(unicode_chars):
            return "".join(unicode_chars)
        else:
            return f'<sub>{content}</sub>'
    s = re.sub(r'\_\{?([^}]+)\}?', sub_replacer, s)
    
    # Handle math alphabets
    s = replace_math_alphabets(s)

    # Remove any remaining math delimiters
    s = s.replace('$', '')
    
    return s



def clean_up_abstract(s):
    #print(f"in clean_up_abstract abstract={s}")
    s='<p>'+s+'</p>'
    
    s = process_latex_in_blocks(s)

    return s



def check_for_acronyms(a):
    if (a.find('\\gls{') >= 0) or (a.find('\\glspl{') >= 0) or \
       (a.find('\\Gls{') >= 0) or (a.find('\\Glspl{') >= 0) or \
       (a.find('\\acrlong{') >= 0) or (a.find('\\acrshort{') >= 0) or \
       (a.find('\\glsentrylong') >= 0) or (a.find('\\glsentryshort{') >= 0) or (a.find('\\glsentryfull{') >= 0) or \
       (a.find('\\acrfull{') >= 0):
        return True
    return False

def get_acronyms_regex_with_errors(acronyms_filename):
    """
    Parses an acronyms file using a regular expression and reports
    any lines that appear to be definitions but cannot be parsed.
    """
    acronym_dict = {}
    
    # This pattern finds the command, ignores the optional [...], and captures the 3 arguments
    pattern = re.compile(r'\\newacronym(?:\[.*?\])?\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
    
    try:
        with open(acronyms_filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # We only care about lines that are likely to be definitions
                if '\\newacronym' in line:
                    # Strip comments from the line before matching
                    line_content = line.split('%')[0]
                    
                    match = pattern.search(line_content)
                    if match:
                        label, acronym, phrase = match.groups()
                        acronym_dict[label] = {'acronym': acronym, 'phrase': phrase}
                    else:
                        # If the line contains the command but doesn't match, it's a syntax error
                        print(f"Warning: Could not parse acronym definition on line {line_num}: {line.strip()}")
                        
    except FileNotFoundError:
        print(f"Error: Acronyms file not found at '{acronyms_filename}'")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
        
    return acronym_dict

def old_get_acronyms(acronyms_filename):
    acronym_dict=dict()
    #
    newacronym_pattern='newacronym'
    trailing_marker='}'
    start_option_marker='['
    end_option_marker=']'
    #
    with open(acronyms_filename, 'r', encoding='utf-8') as input_FH:
        for line in input_FH:
            line=line.strip()   # remove leading and trailing white space
            comment_offset=line.find('%')
            if comment_offset == 1: #  of a comment line, simply skip the line
                continue
            offset=line.find(newacronym_pattern)
            if offset < 1:
                continue
            offset_s=line.find(start_option_marker)
            offset_e=line.find(end_option_marker)
            if offset_s > 0 and offset_e > 0: 		# remove options to \newacronym[options]{}{}{}
                line=line[0:offset_s]+line[offset_e+1:]
            # process an acronym definition
            parts=line.split('{')
            label=None
            acronym=None
            phrase=None
            for i, value in enumerate(parts):
                if i == 0:
                    continue
                elif i == 1: #  get label
                    label=value.strip()
                    if label.endswith(trailing_marker):
                        label=label[:-1]
                    else:
                        print("Error in parsing for label in line: {}".format(line))
                        continue
                elif i == 2: # get acronym
                    acronym=value.strip()
                    if acronym.endswith(trailing_marker):
                        acronym=acronym[:-1]
                    else:
                        print("Error in parsing for acronym in line: {}".format(line))
                        continue
                elif i == 3: # get phrase
                    phrase=value.strip()
                    if phrase.endswith(trailing_marker):
                        phrase=phrase[:-1]
                    else:
                        print("Error in parsing for phrase in line: {}".format(line))
                        continue
                else:
                    print("Error in parsing in line: {}".format(line))
                    continue
            acronym_dict[label]={'acronym': acronym, 'phrase': phrase}
            #
    return acronym_dict

def replace_first_gls(a, offset, acronym_dict):
    global spelled_out
    a_prefix=a[:offset]
    end_of_acronym=a.find('}', offset+5)
    if end_of_acronym < 0:
        print("could not find end of acronym label")
        return a
    label=a[offset+5:end_of_acronym]
    a_postfix=a[end_of_acronym+1:]
    ad=acronym_dict.get(label, None)
    if ad:
        phrase=ad.get('phrase', None)
        acronym=ad.get('acronym', None)
        already_spelled_out=spelled_out.get(label, None)
        if already_spelled_out:
            if acronym:
                a=a_prefix+acronym+a_postfix
            else:
                print("acronym missing for label={}".format(label))
        else:
            if phrase and acronym:
                full_phrase="{0} ({1})".format(phrase, acronym)
                a=a_prefix+full_phrase+a_postfix
                spelled_out[label]=True
            else:
                print("phrase or acronym are missing for label={}".format(label))
    else:
        print("Missing acronym for {}".format(label))
        return None
    #
    return a

def replace_first_glspl(a, offset, acronym_dict):
    global spelled_out
    a_prefix=a[:offset]
    end_of_acronym=a.find('}', offset+7)
    if end_of_acronym < 0:
        print("could not find end of acronym label")
        return a
    label=a[offset+7:end_of_acronym]
    a_postfix=a[end_of_acronym+1:]
    ad=acronym_dict.get(label, None)
    if ad:
        phrase=ad.get('phrase', None)
        acronym=ad.get('acronym', None)
        already_spelled_out=spelled_out.get(label, None)
        if already_spelled_out:
            if acronym:
                a=a_prefix+acronym+a_postfix
            else:
                print("acronym missing for label={}".format(label))
        else:
            if phrase and acronym:
                full_phrase="{0} ({1})".format(phrase, acronym)
                a=a_prefix+full_phrase+a_postfix
                spelled_out[label]=True
            else:
                print("phrase or acronym are missing for label={}".format(label))
    else:
        print("Missing acronym for {}".format(label))
        return None
    #
    return a

def spellout_acronyms_in_abstract(acronym_dict, a):
    # look for use of acronyms (i.e., a reference to an acronym's label) and spell out as needed
    # keep list of labels of acronyms found and spellout out
    global spelled_out
    spelled_out=dict()
    # Note that because we initialize it for each call of this routine, the acronyms will be spellout appropriately in each abstract
    #
    # first handle all cases where the full version is to be included
    for template in ['\\acrfull{', '\\glsentryfull{']:
        offset=a.find(template)
        while offset >= 0:
            a_prefix=a[:offset]
            end_of_acronym=a.find('}', offset+len(template))
            if end_of_acronym < 0:
                print("could not find end of acronym label")
                break
            label=a[offset+len(template):end_of_acronym]
            a_postfix=a[end_of_acronym+1:]
            ad=acronym_dict.get(label, None)
            if ad:
                phrase=ad.get('phrase', None)
                acronym=ad.get('acronym', None)
                if phrase and acronym:
                    full_phrase="{0} ({1})".format(phrase, acronym)
                    a=a_prefix+full_phrase+a_postfix
                    spelled_out[label]=True
                else:
                    print("phrase or acronym are missing for label={}".format(label))
            #
            offset=a.find(template, end_of_acronym)
    #
    # second handle all cases where the long version is to be included
    for template in ['\\acrlong{', '\\glsentrylong{']:
        offset=a.find(template)
        while offset >= 0:
            a_prefix=a[:offset]
            end_of_acronym=a.find('}', offset+len(template))
            if end_of_acronym < 0:
                print("could not find end of acronym label")
                break
            label=a[offset+len(template):end_of_acronym]
            a_postfix=a[end_of_acronym+1:]
            ad=acronym_dict.get(label, None)
            if ad:
                phrase=ad.get('phrase', None)
                if phrase:
                    a=a_prefix+phrase+a_postfix
                else:
                    print("phrase or acronym are missing for label={}".format(label))
            #
            offset=a.find(template, end_of_acronym)
    #
    #
    # third handle all cases where the long version is to be included
    for template in ['\\acrshort{', '\\glsentryshort{']:
        offset=a.find(template)
        while offset >= 0:
            a_prefix=a[:offset]
            end_of_acronym=a.find('}', offset+len(template))
            if end_of_acronym < 0:
                print("could not find end of acronym label")
                break
            label=a[offset+len(template):end_of_acronym]
            a_postfix=a[end_of_acronym+1:]
            ad=acronym_dict.get(label, None)
            if ad:
                acronym=ad.get('acronym', None)
                if acronym:
                    a=a_prefix+acronym+a_postfix
                else:
                    print("phrase or acronym are missing for label={}".format(label))
            #
            offset=a.find(template, end_of_acronym)
    #
    # handle cases where the acronym is conditionally spelled out and introduced or only the acronym is inserted
    # gls_offset=a.find('\\gls{')
    # lspl_offset=a.find('\\glspl{')
    # ggls_offset=a.find('\\Gls{')
    # gglspl_offset=a.find('\\Glspl{')
    # 
    s1=re.search('\\\\gls\{', a, re.IGNORECASE)
    s2=re.search('\\\\glspl\{', a, re.IGNORECASE)
    # find the earliest one
    while s1 or s2:
        if s1 and s2:
            gls_offset=s1.span()[0]
            glspl_offset=s2.span()[0]
            if  gls_offset < glspl_offset:
                # gls case occurs first
                a1=replace_first_gls(a, gls_offset, acronym_dict)
                if a1:
                    a=a1
                else:           # if the replacement failed, bail out
                    return a
            else:
                a=replace_first_glspl(a, glspl_offset, acronym_dict)
        elif s1 and not s2:
            gls_offset=s1.span()[0]
            a1=replace_first_gls(a, gls_offset, acronym_dict)
            if a1:
                a=a1
            else:
                return a
        else: # case of no s1 and s2:
            glspl_offset=s2.span()[0]
            a1=replace_first_glspl(a, glspl_offset, acronym_dict)
            if a1:
                a=a1
            else:
                return a
        s1=re.search('\\\\gls\{', a, re.IGNORECASE)
        s2=re.search('\\\\glspl\{', a, re.IGNORECASE)
    return a

# ligature. LaTeX commonly does it for ff, fi, fl, ffi, ffl, ...
ligrature_table= {'\ufb00': 'ff', # 'ﬀ'
                  '\ufb03': 'f‌f‌i', # 'ﬃ'
                  '\ufb04': 'ffl', # 'ﬄ'
                  '\ufb01': 'fi', # 'ﬁ'
                  '\ufb02': 'fl', # 'ﬂ'
                  '\ua732': 'AA', # 'Ꜳ'
                  '\ua733': 'aa', # 'ꜳ'
                  '\ua733': 'aa', # 'ꜳ'
                  '\u00c6': 'AE', # 'Æ'
                  '\u00e6': 'ae', # 'æ'
                  '\uab31': 'aə', # 'ꬱ'
                  '\ua734': 'AO', # 'Ꜵ'
                  '\ua735': 'ao', # 'ꜵ'
                  '\ua736': 'AU', # 'Ꜷ'
                  '\ua737': 'au', # 'ꜷ'
                  '\ua738': 'AV', # 'Ꜹ'
                  '\ua739': 'av', # 'ꜹ'
                  '\ua73a': 'AV', # 'Ꜻ'  - note the bar
                  '\ua73b': 'av', # 'ꜻ'  - note the bar
                  '\ua73c': 'AY', # 'Ꜽ'
                  '\ua76a': 'ET', # 'Ꝫ'
                  '\ua76b': 'et', # 'ꝫ'
                  '\uab41': 'əø', # 'ꭁ'
                  '\u01F6': 'Hv', # 'Ƕ'
                  '\u0195': 'hu', # 'ƕ'
                  '\u2114': 'lb', # '℔'
                  '\u1efa': 'IL', # 'Ỻ'
                  '\u0152': 'OE', # 'Œ'
                  '\u0153': 'oe', # 'œ'
                  '\ua74e': 'OO', # 'Ꝏ'
                  '\ua74f': 'oo', # 'ꝏ'
                  '\uab62': 'ɔe', # 'ꭢ'
                  '\u1e9e': 'fs', # 'ẞ'
                  '\u00df': 'fz', # 'ß'
                  '\ufb06': 'st', # 'ﬆ'
                  '\ufb05': 'ſt', # 'ﬅ'  -- long ST
                  '\ua728': 'Tz', # 'Ꜩ'
                  '\ua729': 'tz', # 'ꜩ'
                  '\u1d6b': 'ue', # 'ᵫ'
                  '\uab63': 'uo', # 'ꭣ'
                  #'\u0057': 'UU', # 'W'
                  #'\u0077': 'uu', # 'w'
                  '\ua760': 'VY', # 'Ꝡ'
                  '\ua761': 'vy', # 'ꝡ'
                  # 
                  '\u0238': 'db', # 'ȸ'
                  '\u02a3': 'dz', # 'ʣ'
                  '\u1b66': 'dʐ', # 'ꭦ'
                  '\u02a5': 'dʑ', # 'ʥ'
                  '\u02a4': 'dʒ', # 'ʤ'
                  '\u02a9': 'fŋ', # 'ʩ'
                  '\u02aa': 'ls', # 'ʪ'
                  '\u02ab': 'lz', # 'ʫ'
                  '\u026e': 'lʒ', # 'ɮ'
                  '\u0239': 'qp', # 'ȹ'
                  '\u02a8': 'tɕ', # 'ʨ'
                  '\u02a6': 'ts', # 'ʦ'
                  '\uab67': 'tʂ', # 'ꭧ'
                  '\u02a7': 'tʃ', # 'ʧ'
                  '\uab50': 'ui', # 'ꭐ'
                  '\uab51': 'ui', # 'ꭑ' -- turned ui
                  '\u026f': 'uu', # 'ɯ'
                  # digraphs with single code points
                  '\u01f1': 'DZ', # 'Ǳ'
                  '\u01f2': 'Dz', # 'ǲ'
                  '\u01f3': 'dz', # 'ǳ'
                  '\u01c4': 'DŽ', # 'Ǆ'
                  '\u01c5': 'Dž', # 'ǅ'
                  '\u01c6': 'dž', # 'ǆ'
                  '\u0132': 'IJ', # 'Ĳ'
                  '\u0133': 'ij', # 'ĳ'
                  '\u01c7': 'LJ', # 'Ǉ'
                  '\u01c8': 'Lj', # 'ǈ'
                  '\u01c9': 'lj', # 'ǉ'
                  '\u01ca': 'NJ', # 'Ǌ'
                  '\u01cb': 'Nj', # 'ǋ'
                  '\u01cc': 'nj', # 'ǌ'
                  '\u1d7a': 'th', # 'ᵺ'
                  }

def replace_ligature(s):
    # check for ligratures and replace them with separate characters
    if not s:
        return s
    
    for l in ligrature_table:
        if s.find(l) >= 0:
            print("found ligrature {0} replacing with {1}".format(l, ligrature_table[l]))  
            s=s.replace(l, ligrature_table[l])
    #
    return s


def clean_and_transform_str(s):
    # remove preceeding and trailing white space
    s=s.strip()
    s=s.replace('\&', '&amp;')
    s=replace_ligature(s)
    return s
    

def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )

    parser.add_option('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    parser.add_option('-j', '--json',
                      type=str,
                      default="fordiva.json",
                      help="JSON file for extracted data"
                      )

    parser.add_option('-a', '--acronyms',
                      type=str,
                      default="acronyms.tex",
                      help="acronyms file"
                      )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))


    d=None                      # where the JSON data will be put

    pp = pprint.PrettyPrinter(indent=4, width=1024) # configure prettyprinter

    json_filename=options.json
    json_string=''
    if json_filename:
        try:
            with open(json_filename, 'r', encoding='utf-8') as json_FH:
                json_string=json_FH.read()
        except FileNotFoundError:
            print(f"File not found: {json_filename}")
            return 1

        try:
            d=json.loads(json_string)
            if Verbose_Flag:
                print(f"read JSON: {d}")

        except :
            print(f"Error in JSON in {json_filename}")
            return 1

    else:
        print(f"Unknown source for the JSON: {json_filename}")
        return 1

    # check for keywords
    keywords_dict=d.get('keywords', None)
    if keywords_dict and isinstance(keywords_dict, dict):
        for lang in keywords_dict:
            lang_keywords=keywords_dict.get(lang, None)
            keywords_str=lang_keywords.strip()
            keywords=keywords_str.split(',')
            cleaned_list = [clean_and_transform_str(keyword) for keyword in keywords]
    
            # Join the cleaned keywords back into a single string.
            d['keywords'][lang] = ', '.join(cleaned_list)

    #print("after cleaning keywords")
    #pp.pprint(d)
    
    # check for abstracts
    abstracts=d.get('abstracts', None)
    if abstracts:
        for lang in abstracts:
            abstracts[lang]=clean_up_abstract(abstracts[lang])

        any_acronyms_in_abstracts=False
        for lang in abstracts:
            acronyms_present=check_for_acronyms(abstracts[lang])
            if acronyms_present:
                any_acronyms_in_abstracts=True

        if any_acronyms_in_abstracts:
            acronyms_filename=options.acronyms
            print(f"Acronyms found, getting acronyms from {acronyms_filename}")
            acronym_dict=get_acronyms(acronyms_filename)
            if len(acronym_dict) == 0:
                print(f"no acronyms found in {acronyms_filename}")
            else:
                # entries of the form: acronym_dict[label]={'acronym': acronym, 'phrase': phrase}
                for lang in abstracts:
                    abstracts[lang]=spellout_acronyms_in_abstract(acronym_dict, abstracts[lang])

        if Verbose_Flag:
            for lang in abstracts:
                print(f"abstracts[{lang}]: {abstracts[lang]}")

    output_filename = json_filename[:-5] + "-HTML.json"
    if Verbose_Flag:
        print(f"output_filename={output_filename}")
    with open(output_filename, 'w', encoding='utf-8') as output_FH:
        j_as_string = json.dumps(d, ensure_ascii=False)
        print(j_as_string, file=output_FH)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

