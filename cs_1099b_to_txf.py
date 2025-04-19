#!/usr/bin/env python3

"""cssb_1099b_to_txf converts simple Charles Schwab 1099-B PDFs to TXF files."""

import argparse
import datetime
import os
import re
import subprocess
import sys

# Codes and structure are defined at
# https://taxdataexchange.org/docs/txf/v042/index.html
categories = {
        # MSSB style:
        'Short Term – Noncovered Securities': '711',
        'Long Term – Noncovered Securities': '713',
        # Schwab style:
        'Short-term transaction for which basis is not reported to the IRS; report on Form 8949, Part I, with Box B checked.': '711',
        'Long-term transaction for which basis is not reported to the IRS; report on Form 8949, Part II, with Box E checked.': '713'
}

# Match a section of sales for one sales category.
# The last line can say 'Total Short Term – Noncovered Securities' or
# 'Total Short Term Noncovered Securities' (without the hypen) so match
# only on "^Total".
categories_pattern = '|'.join(categories)
section_expr = re.compile(
    (
        r'^(' + categories_pattern + r')'
        r'(.*?)'
        r'^Total'
    ),
    re.DOTALL|re.MULTILINE,
)

# MSSB FORMAT:
# Fields: RefNumber Description CUSIP Quantity DateAcquired DateSold
#         GrossProceeds CostBasis
#
# Example:
#   1234 ALPHABET INC CL C
#   12345A678
#   1.000000 01/01/20 02/01/20 $2,000.00 $1,9999.00
#
# Example:
#   1234 ALPHABET INC CL C
#   12345A678
#   1.000000 VARIOUS 02/01/20 $2,000.00 $1,9999.00
mssb_row_expr = re.compile(
    (
        r'^'
        r'(?P<descr>(\w| )+)'
        r'\s+'
        r'(?P<cusip>\w+)'
        r'\s+'
        r'(?P<quantity>\d*\.\d+)'
        r'\s+'
        r'(?P<acquired>(\d+/\d+/\d+|\w+))'
        r'\s+'
        r'(?P<sold>\d+/\d+/\d+)'
        r'\s+'
        r'(?P<proceeds>\$[0-9,.]+)'
        r'\s+'
        r'(?P<cost>\$[0-9,.]+)'
        r'\s'
    ),
    re.DOTALL|re.MULTILINE,
)

# SCHWAB FORMAT:
# Each entry consists of 4 lines; fields are broken up like:
#   CUSIP
#   QuantityAndDescription
#   DateAcquired Proceeds CostBasis NonCoveredSecurity(IfYesThen"X",IfNoThenEmpty)
#   DateSold GROSS_or_NET
#
# Example:
#   02079K107
#   28.028 SHARES OF GOOG
#   12/23/2023 4,801.24 4,000.16 X
#   05/08/2024 GROSS
schwab_row_expr = re.compile(
    (
        r'\s*'
        r'(?P<cusip>\w+)'
        r'\s+'
        r'(?P<quantity>\d+(\.\d+)?)\s+SHARES OF\s+(?P<descr>(\w)+)'
        r'\s+'
        r'(?P<acquireddate>(\d+/\d+/\d+|\w+))'
        r'\s+'
        r'(?P<proceeds>(\$)?[0-9,.]+)'
        r'\s+'
        r'(?P<cost>(\$)?[0-9,.]+)'
        r'\s+'
        r'(?P<noncoveredsecurity>[Xx])'
        r'\s+'
        r'(?P<solddate>\d+/\d+/\d+)'
        r'\s+'
        r'(?P<grossornet>GROSS)'  # TODO: Test against PDF with NET entries.
    ),
    re.DOTALL|re.MULTILINE,
)

# row_expr = mssb_row_expr
row_expr = schwab_row_expr


def parseAndSerializeRows(text, entry_code):
    output_rows = []
    for match in row_expr.finditer(text):
        output_rows.append('TD')
        output_rows.append('N' + entry_code)
        output_rows.append('C1')
        output_rows.append('L1')
        # Form 8949 documents "100 sh. XYZ Co." as the example format.
        output_rows.append(
            'P' + match.group('quantity') + ' sh. of ' + match.group('descr'))
        output_rows.append('D' + match.group('acquireddate'))
        output_rows.append('D' + match.group('solddate'))
        # These have a leading dollar sign on Merrill formatting, but not Schwab.
        cost = match.group('cost')
        if not cost.startswith('$'):
            cost = '$' + cost
        output_rows.append(cost)
        proceeds = match.group('proceeds')
        if not proceeds.startswith('$'):
            proceeds = '$' + proceeds
        output_rows.append(proceeds)
        output_rows.append("$") # Wash sale. Leaving blank. They aren't handled here.
        output_rows.append('^')
    return '\n'.join(output_rows) + '\n'


def parse_sections(text):
    return section_expr.finditer(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_path',
        type=os.path.realpath,
        help='The path to the 1099-B PDF document.',
    )
    parser.add_argument(
        'output_path',
        nargs='?',
        default=None,
        type=str,
        help=(
            'The destination file name for the TXF output. If this argument '
            'is omitted, then the TXF output will print to stdout.'
        ),
    )
    args = parser.parse_args()
    text = subprocess.check_output(['pdftotext', '-raw', args.input_path, '-']).decode()

    output_stream = sys.stdout
    if args.output_path:
        if os.path.exists(args.output_path):
            raise FileExistsError('Output path "' + args.output_path + '" already exists')
        output_stream = open(args.output_path, 'w')

    try:
        output_stream.write('V042' + '\n')
        output_stream.write('A mssb_1099b_to_txf' + '\n')
        output_stream.write('D ' + datetime.datetime.now().strftime('%m/%d/%Y') + '\n')
        output_stream.write('^' + '\n')
        for section_match in parse_sections(text):
            entry_code = categories[section_match.group(1)]
            contents = section_match.group(2)
            serialized = parseAndSerializeRows(contents, entry_code)
            output_stream.write(serialized)
    finally:
        output_stream.close()


if __name__ == '__main__':
    main()

