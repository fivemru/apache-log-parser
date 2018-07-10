
import sys
import re
import os
import os.path
import time
import subprocess

if sys.version.startswith("3"):
    import io
    io_method = io.BytesIO
else:
    import cStringIO
    io_method = cStringIO.StringIO

from collections import Counter


def parse_log_lines(content, fields):
    tree = {}
    count_lines = 0
    start = time.time()

    for line in content:
        count_lines += 1
        data = parse_line(line)

        tmp = tree

        for i, field in enumerate(fields):
            isLast = True if i == len(fields) - 1 else False
            val = ""
            if type(field) is list:
                for fi in field:
                    val += format_value(fi, data)
            else:
                val = format_value(field, data)

            if tmp.get(val) == None:
                tmp[val] = 0 if isLast else {}
            if isLast:
                tmp[val] += 1
            tmp = tmp[val]

    end = time.time()
    return {
        'lines':    count_lines,
        'tree':     tree,
        'time':     (end - start),
    }


def parse_line(line):
    chunk = line.split()
    return {
        'ip':		chunk[0],
        'date':		chunk[3][1:12],
        'code':		(chunk[8] if len(chunk) >= 8 else ""),
        'method':	(chunk[5][1:] if len(chunk) >= 5 else ""),
        'uri':		(chunk[6] if len(chunk) >= 6 else ""),
        'protocol':	(chunk[7][:-1] if len(chunk) >= 7 else ""),
        'request':	(chunk[5][1:]+" "+chunk[6]+" "+chunk[7][:-1] if len(chunk) >= 7 else ""),
        'ua':		(' '.join(chunk[11:])[1:-1] if len(chunk) >= 11 else ""),
        'ref':		(chunk[10][1:-1] if len(chunk) >= 11 else ""),
    }


def field_param(field):
    chunk = field.split(':')
    return {
        'name': 	chunk[0],
        'format': 	(chunk[1] if len(chunk) > 1 else ""),
    }


def norm_date(date_str):
    return '-'.join(
        reduce(
            lambda str, re: str.replace(
                re[1],
                '{0}'.format(re[0]).zfill(2)
            ),
            enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1),
            date_str.replace('\t', '')
        ).split('/')[::-1]
    )


def format_value(field, data):
    f_param = field_param(field)
    value = ('{0:' + f_param['format'] + '}').format(
        data[f_param['name']]
    )
    return value + "\t"


def find_and_replace(tree, fields, field, find_name, fn):
    new_tree = {}
    col_separator = '\t'
    field_names = []

    if type(field) is list:
        for fi in field:
            field_names.append(field_param(fi)['name'])
    else:
        field_names.append(field_param(field)['name'])

    try:
        field_names.index(find_name)

        for k, v in tree.items():
            if type(field) is list:
                ch = k.split(col_separator)

                for i, name in enumerate(field_names):
                    if name == find_name:
                        ch[i] = fn(ch[i])

                new_tree[col_separator.join(ch)] = v
            else:
                new_tree[fn(k)] = v

    except Exception as err:
        # print("Unexpected error:", err)
        new_tree = tree
        pass

    return new_tree


def print_tree(tree, fields, pad="", level=0):

    tree = find_and_replace(tree, fields, fields[level], 'date',
                            lambda value: norm_date(value))
    sum = 0
    for item in sorted(tree):
        val = tree[item]
        if type(val) is dict:
            print(pad + item)
            sum += print_tree(val, fields, pad + "\t", level + 1)
        else:
            print(pad + str(val) + "\t" + item)
            sum += val
    print("---sum=" + str(sum))
    return sum


def print_report(files, fields, filters=[]):
    print('=== Report fields : ', fields, ' ===')

    p = subprocess.Popen((["cat"] + files), stdout=subprocess.PIPE)
    content = io_method(p.communicate()[0])
    assert p.returncode == 0

    res = parse_log_lines(content, fields)
    print("Number of lines: " + str(res['lines']))
    print("Time: " + str(res['time']) + "\n")
    print_tree(res['tree'], fields)
    print
    content.close()


if __name__ == '__main__':
    print("Hello! This is simple Apache log analyzer\n")

    files = []
    for filename in sys.argv[1:]:
        if os.path.isfile(filename):
            files.append(filename)

    if len(files) == 0:
        print("Files not found: ", ("\n\t".join(sys.argv[1])))
        sys.exit(1)

    print("Files (" + str(len(files)) + "): \n" + ("\t".join(files)) + "\n\n")

    sys.stdout.flush()

    # print_report(files, ['code'])
    # print_report(files, ['date'])
    # print_report(files, ['ip'])
    # print_report(files, ['method'])
    # print_report(files, ['request'])
    print_report(files, ['method', 'uri'])

    # {
    #     'WP vulm':
    # }

    # print_report(files, ['ip', 'ua', ['uri', 'ref']])
    # print_report(files, ['ip', 'date', 'ua', ['uri', 'ref']])
    # print_report(files, ['ip', 'code'])
    # print_report(files, ['date', ['ip:16', 'ua']])
    # print_report(files, ['ip:16', ['date', 'ua']])
    # print_report(files, ['ip:16', ['date', 'ua']])
    # print_report(files, ['date', 'request'])
