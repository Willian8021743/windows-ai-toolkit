#!/usr/bin/env python3
"""
Extract numerical values from presentation content for consistency checking.

Usage:
    python extract_numbers.py presentation-content.md
    python extract_numbers.py presentation-content.md --output numbers.json

This script parses markdown-formatted presentation content (from markitdown)
and extracts all numerical values with their context and slide references.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class NumberInstance:
    """A numerical value found in the presentation."""
    value: str           # Original string representation
    normalized: float    # Normalized numeric value
    unit: str           # Detected unit (M, B, K, %, bps, x, etc.)
    slide: int          # Slide number (0 if unknown)
    context: str        # Surrounding text for context
    line_number: int    # Line number in source file
    category: str       # Detected category (revenue, margin, multiple, etc.)


def normalize_number(value_str: str, unit: str) -> float:
    """Convert a number string with unit to a normalized float value."""
    clean = re.sub(r'[,\s]', '', value_str)

    try:
        base_value = float(clean)
    except ValueError:
        return 0.0

    multipliers = {
        'T': 1e12,
        'B': 1e9,
        'bn': 1e9,
        'billion': 1e9,
        'M': 1e6,
        'mm': 1e6,
        'mn': 1e6,
        'million': 1e6,
        'K': 1e3,
        'k': 1e3,
        'thousand': 1e3,
    }

    for unit_key in sorted(multipliers.keys(), key=len, reverse=True):
        if unit_key.lower() in unit.lower():
            return base_value * multipliers[unit_key]

    return base_value


def detect_category(context: str, unit: str) -> str:
    """Detect the category of a number based on context and unit."""
    context_lower = context.lower()

    if any(term in context_lower for term in ['revenue', 'sales', 'top line', 'topline']):
        return 'revenue'

    if 'ebitda' in context_lower:
        if any(term in context_lower for term in ['margin', '%', 'percent']):
            return 'ebitda_margin'
        return 'ebitda'

    if any(term in context_lower for term in ['margin', 'profit']):
        return 'margin'

    if any(term in context_lower for term in ['growth', 'cagr', 'yoy', 'y/y']):
        return 'growth'

    if any(term in context_lower for term in ['multiple', 'ev/', 'p/e', 'ev/ebitda', 'ev/revenue']):
        return 'multiple'

    if any(term in context_lower for term in ['enterprise value', 'ev ', 'market cap']):
        return 'valuation'

    if unit in ['%', 'bps', 'percent']:
        return 'percentage'

    if unit == 'x':
        return 'multiple'

    return 'other'


def extract_numbers(content: str) -> list[NumberInstance]:
    """Extract all numbers from presentation content."""
    numbers = []
    current_slide = 0

    slide_pattern = re.compile(r'^#+\s*Slide\s*(\d+)|^<!-- Slide (\d+)')

    number_pattern = re.compile(
        r'(?P<currency>[$\u20ac\u00a3\u00a5])?'
        r'(?P<number>[\d,]+(?:\.\d+)?)'
        r'\s*'
        r'(?P<unit>%|bps|x|'
        r'[Tt]rillion|[Bb]illion|[Mm]illion|[Tt]housand|'
        r'[TBMKtbmk]n?|mm|MM)?'
        r'(?!\d)'
    )

    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        slide_match = slide_pattern.match(line)
        if slide_match:
            current_slide = int(slide_match.group(1) or slide_match.group(2))
            continue

        for match in number_pattern.finditer(line):
            value_str = match.group('number')
            currency = match.group('currency') or ''
            unit = match.group('unit') or ''

            if len(value_str.replace(',', '').replace('.', '')) < 2 and not unit:
                continue

            try:
                num_val = float(value_str.replace(',', ''))
                if 1900 <= num_val <= 2099 and not unit and not currency:
                    continue
            except ValueError:
                pass

            full_value = f"{currency}{value_str}{unit}"

            start = max(0, match.start() - 50)
            end = min(len(line), match.end() + 50)
            context = line[start:end].strip()

            if currency:
                if not unit:
                    unit = 'USD'
                else:
                    unit = f"USD_{unit}"

            normalized = normalize_number(value_str, unit)
            category = detect_category(context, unit)

            numbers.append(NumberInstance(
                value=full_value,
                normalized=normalized,
                unit=unit or 'none',
                slide=current_slide,
                context=context,
                line_number=line_num,
                category=category
            ))

    return numbers


def find_inconsistencies(numbers: list[NumberInstance]) -> list[dict]:
    """Find potential inconsistencies in extracted numbers."""
    inconsistencies = []

    by_category = defaultdict(list)
    for num in numbers:
        if num.category != 'other':
            by_category[num.category].append(num)

    for category, instances in by_category.items():
        if len(instances) < 2:
            continue

        value_groups = []
        for inst in instances:
            placed = False
            for group in value_groups:
                ref_value = group[0].normalized
                if ref_value > 0:
                    diff_pct = abs(inst.normalized - ref_value) / ref_value
                    if diff_pct < 0.05:
                        group.append(inst)
                        placed = True
                        break
            if not placed:
                value_groups.append([inst])

        if len(value_groups) > 1:
            value_groups.sort(key=len, reverse=True)

            main_group = value_groups[0]
            for other_group in value_groups[1:]:
                inconsistencies.append({
                    'category': category,
                    'expected': {
                        'value': main_group[0].value,
                        'slides': sorted(set(n.slide for n in main_group)),
                        'count': len(main_group)
                    },
                    'found': {
                        'value': other_group[0].value,
                        'slides': sorted(set(n.slide for n in other_group)),
                        'count': len(other_group)
                    },
                    'severity': 'high' if category in ['revenue', 'ebitda', 'valuation'] else 'medium'
                })

    return inconsistencies


def main():
    parser = argparse.ArgumentParser(
        description='Extract numbers from presentation content for consistency checking'
    )
    parser.add_argument('input_file', help='Markdown file with presentation content')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')
    parser.add_argument('--check', '-c', action='store_true',
                       help='Check for inconsistencies and report')

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_text()

    numbers = extract_numbers(content)

    output = {
        'total_numbers': len(numbers),
        'by_category': defaultdict(list),
        'numbers': [asdict(n) for n in numbers]
    }

    for num in numbers:
        output['by_category'][num.category].append({
            'value': num.value,
            'slide': num.slide,
            'context': num.context[:100]
        })

    output['by_category'] = dict(output['by_category'])

    if args.check:
        inconsistencies = find_inconsistencies(numbers)
        output['inconsistencies'] = inconsistencies

        if inconsistencies:
            print("\n=== POTENTIAL INCONSISTENCIES DETECTED ===\n", file=sys.stderr)
            for inc in inconsistencies:
                print(f"Category: {inc['category'].upper()}", file=sys.stderr)
                print(f"  Expected: {inc['expected']['value']} (Slides: {inc['expected']['slides']}, Count: {inc['expected']['count']})", file=sys.stderr)
                print(f"  Found:    {inc['found']['value']} (Slides: {inc['found']['slides']}, Count: {inc['found']['count']})", file=sys.stderr)
                print(f"  Severity: {inc['severity']}", file=sys.stderr)
                print(file=sys.stderr)

    json_output = json.dumps(output, indent=2)

    if args.output:
        Path(args.output).write_text(json_output)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == '__main__':
    main()
