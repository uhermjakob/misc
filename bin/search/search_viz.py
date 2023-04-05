#!/usr/bin/env python
"""
Written by Ulf Hermjakob, USC/ISI
This script searches a file for one or more substrings and outputs an HTML file with visualized search results.
Examples:
  search_viz.py -h  # for full usage info
  search_viz.py -i orig/eng-eng-asv.txt -o wb-ana-orig/asv-david.html -s David
  search_viz.py -i orig/eng-eng-asv.txt -o wb-ana-orig/asv-king-david.html -r vref.txt -s 'King David' --ignore_case
  search_viz.py -i orig/hbo-hboWLC.txt -o wb-ana-orig/pateh-meteg-order.html -r vref.txt \
      -s '\u05B7\u05BD' '\u05BD\u05B7' -n 20
"""

import argparse
from collections import defaultdict
import datetime
import os
import regex
import sys
import unicodedata as ud


def html_head(title: str, date: str, meta_title: str) -> str:
    return f"""<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>{meta_title}</title>
    </head>
    <body bgcolor="#FFFFEE" onload="set_status('START');">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr bgcolor="#BBCCFF">
                <td><table border="0" cellpadding="3" cellspacing="0">
                        <tr>
                            <td><b><font class="large" size="+1">&nbsp; {title}</font></b></td>
                            <td>&nbsp;&nbsp;&nbsp;{date}&nbsp;&nbsp;&nbsp;</td>
                            <td style="color:#777777;font-size:80%;">Script search_viz.py &nbsp; 
                                                                    by Ulf Hermjakob</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table><p>
"""


def html_foot() -> str:
    return """    </body>
</html>
"""


def guard_html(s: str) -> str:
    s = regex.sub('&', '&amp;', s)
    s = regex.sub('<', '&lt;', s)
    s = regex.sub('>', '&gt;', s)
    s = regex.sub('"', '&quot;', s)
    return s


def char_unicode_name_rows(s: str) -> list:
    result = []
    for c in s:
        result.append(f"<tr><td>{c}</td><td>U+{ord(c):04X}</td><td>{ud.name(c, '')}</td></tr>")
    return result


def decode_unicode_escape(s: str) -> str:
    while m3 := regex.match(r'(.*?)\\u([0-9A-Fa-f]{4,4})(.*)$', s):
        code_point = int(f'0x{m3.group(2)}', 0)
        s = m3.group(1) + chr(code_point) + m3.group(3)
    return s


def highlight_search_term_tokens_in_text(text, search_term, ignore_case: bool = False, full_token_only_p: bool = False):
    """returns text with search_term highlighted in red, token in yellow background"""
    # Identify text tokens to be highlighted
    n_matches = 0
    result = ''
    rest = text
    if full_token_only_p:
        regex_s = rf'(.*?)(\s*)(?<!\S)({search_term})(?!\S)(\s*)(.*)$'
    else:
        regex_s = rf'(.*?)(\s?\S*?)({search_term})(\S*\s|\S*)(.*)$'
    try:
        regex.match(regex_s, text, regex.IGNORECASE)
    except:
        print('Error HL', regex_s)
        return text, 0
    case_flag = regex.IGNORECASE if ignore_case else regex.FULLCASE
    while m5 := regex.match(regex_s, rest, case_flag):
        pre_tokens, pre, term, post, post_tokens = m5.group(1, 2, 3, 4, 5)
        result += guard_html(pre_tokens) \
                  + '<span style="background-color:yellow;">' \
                  + guard_html(pre) \
                  + '<span style="color:red;">' \
                  + guard_html(term) \
                  + '</span>'
        n_matches += 1
        rest2 = post
        while m3 := regex.match(rf'(.*?)({search_term})(.*)$', rest2, case_flag):
            pre2, term2, post2 = m3.group(1, 2, 3)
            result += guard_html(pre2) + '<span style="color:red;">' + guard_html(term2) + '</span>'
            rest2 = post2
            n_matches += 1
        result += guard_html(rest2) + '</span>'
        rest = post_tokens
    result += guard_html(rest)
    return result, n_matches


def main():
    # print(sys.version)  # will print Python version, e.g. 3.11
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_filename', type=str, required=True, help='plain text')
    parser.add_argument('-o', '--output_filename', type=str, required=True, help='HTML file')
    parser.add_argument('-r', '--snt_id_filename', type=str, default=None,
                        help='reference ID file, e.g. vref.txt, same number of lines as input file')
    parser.add_argument('-s', '--search_term', type=str, nargs='+', required=True)
    parser.add_argument('-n', '--max_n_examples', type=int)
    parser.add_argument('--ignore_case', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--regex', action=argparse.BooleanOptionalAction, default=False,
                        help='Interpret search terms as regular expressions')
    args = parser.parse_args()

    count_dict = defaultdict(int)
    example_row_dict = defaultdict(list)
    f_in = open(args.input_filename)
    f_ref = open(args.snt_id_filename) if args.snt_id_filename else None
    f_out = open(args.output_filename, 'w')
    f_out.write(html_head(f'Searching file {args.input_filename}',
                datetime.datetime.now().strftime('%B %d, %Y at %H:%M'), 'search_viz'))
    line_number = 0
    search_terms = []
    for search_term in args.search_term:
        search_terms.append(decode_unicode_escape(search_term))
    # print(f's: {search_terms} {len(search_terms[0])}')
    for line in f_in:
        line_number += 1
        ref = f_ref.readline().strip() if f_ref else None
        for search_term in search_terms:
            if args.ignore_case or args.regex or (search_term in line):
                pattern = search_term if args.regex else regex.escape(search_term)
                highlighted_line, n_matches = highlight_search_term_tokens_in_text(line, pattern,
                                                                                   ignore_case=args.ignore_case)
                if n_matches and (args.max_n_examples is None or count_dict[search_term] < args.max_n_examples):
                    example_row_dict[search_term].append(f'<tr>'
                        f'<td align="right" style="color:#AAAAAA;">{line_number}</td><td>&nbsp;</td>'
                        f'<td><nobr>{ref if ref else ""}</nobr></td><td>&nbsp;</td><td>{highlighted_line}</td></tr>')
                count_dict[search_term] += n_matches
    for search_term in search_terms:
        f_out.write('<p>\n')
        n = count_dict[search_term]
        instances = 'instance' if n == 1 else 'instances'
        case_clause = 'case-insensitive, ' if args.ignore_case else ''
        regex_clase = 'regex, ' if args.ignore_case else ''
        if regex.match(r'[\u0020-\u007E]+', search_term):
            f_out.write(f'<b>Search term:</b> {search_term} &nbsp; ({case_clause}{regex_clase}found {n} {instances})')
        else:
            f_out.write(f'<b>Search term:</b> &nbsp; ({case_clause}{regex_clase}found {n} {instances})')
            f_out.write('<table>')
            for row in char_unicode_name_rows(search_term):
                f_out.write('    ' + row)
            f_out.write('</table>')
        f_out.write('<p>\n')
        f_out.write('<table>')
        for example_row in example_row_dict[search_term]:
            f_out.write('    ' + example_row)
        f_out.write('</table>')
        sys.stderr.write(f'Search term: {search_term} ({case_clause}found {n} {instances})\n')
    f_out.write(html_foot())
    if f_ref:
        f_ref.close()
    f_out.close()
    f_in.close()
    sys.stderr.write(f'Wrote results to {os.path.abspath(args.output_filename)}\n')


if __name__ == "__main__":
    main()
