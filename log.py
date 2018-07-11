
import sys
import os
import re
import subprocess
import time

if sys.version.startswith("3"):
    import io
    io_method = io.BytesIO
else:
    import cStringIO
    io_method = cStringIO.StringIO


def parse_files(files, fields, filters):
    tree, lines_total, filtered_total, start = {}, 0, 0, time.time()

    for filename in files:
        start_parse, count_lines, count_filtered = time.time(), 0, 0

        with open(filename) as fp:
            for line in fp:
                count_lines += 1
                data = parse_apache_line(line)

                if filters_pass(data, filters) == False:
                    count_filtered += 1
                    continue

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

        end_parse = time.time()
        lines_total += count_lines
        filtered_total += count_filtered
        print("[{:6.2f} s, {:10d} : (+{:10d}, -{:10d}) lines] {}".format(
            (end_parse - start_parse),
            count_lines,
            (count_lines - count_filtered),
            count_filtered,
            filename,
        ))
        sys.stdout.flush()

    end = time.time()
    return {
        'time':         (end - start),
        'total':        lines_total,
        'filtered':     filtered_total,
        'tree':         tree,
    }


def filters_pass(data, filters):

    def rules_pass(rules, currField=''):

        if type(rules) is str:
            return re.search(rules, data[currField], re.I) != None

        if type(rules) is list:
            for rule in rules:
                if rules_pass(rule) == True:
                    return True

        if type(rules) is dict:
            for k, v in rules.items():
                if (
                    type(v) is dict and rules_pass(v) == False
                    or type(v) is list and rules_pass(v) == False
                    or type(v) is str and rules_pass(v, k) == False
                ):
                    return False
            return True

        return False

    if filters.get('exclude') != None and rules_pass(filters['exclude']) == True:
        return False

    if filters.get('include') != None and rules_pass(filters['include']) == False:
        return False

    return True


def parse_apache_line(line):
    chunk = line.split()
    return {
        'ip':		(chunk[0]).strip(),
        'date':		(chunk[3][1:12]).strip(),
        'code':		(chunk[8] if len(chunk) >= 8 else "").strip(),
        'method':	(chunk[5][1:] if len(chunk) >= 5 else "").strip(),
        'uri':		(chunk[6] if len(chunk) >= 6 else "").strip(),
        'protocol':	(chunk[7][:-1] if len(chunk) >= 7 else "").strip(),
        'request':	(chunk[5][1:]+" "+chunk[6]+" "+chunk[7][:-1] if len(chunk) >= 7 else "").strip(),
        'ua':		(' '.join(chunk[11:])[1:-1] if len(chunk) >= 11 else "").strip(),
        'ref':		(chunk[10][1:-1] if len(chunk) >= 11 else "").strip(),
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

    # Replace date from '10/May/2018' to '2018-05-10' for sort reason.
    tree = find_and_replace(
        tree,
        fields,
        fields[level],
        'date',
        lambda value: norm_date(value)
    )

    sum = 0
    for item in sorted(tree):
        val = tree[item]
        if type(val) is dict:
            print(pad + item)
            sum += print_tree(val, fields, pad + "\t", level + 1)
        else:
            print("{}{}\t{}".format(pad, val, item))
            sum += val
    # print("[total: " + str(sum) + "]\n")
    print
    return sum


def print_report(files, fields, filters={}):
    print('Group by : {:s}\n'.format(fields))
    sys.stdout.flush()

    if len(files) == 0:
        print("Files not found: {:s}".format(sys.argv[1]))
        sys.exit(1)

    res = parse_files(files, fields, filters)

    print("\nTotal\n[{:6.2f} s, {:10d} : (+{:10d}, -{:10d}) lines]\n\n".format(
          res['time'],
          res['total'],
          (res['total'] - res['filtered']),
          res['filtered'],
          ))

    print_tree(res['tree'], fields)


if __name__ == '__main__':
    """
    '">----------------------------------------------------------------------------
    Hello friend!
    This is a simple Apache log parser with the ability to group and|or filter out.
    ----------------------------------------------------------------------------<"'
    """

    files = []
    for filename in sys.argv[1:]:
        if os.path.isfile(filename):
            files.append(filename)

    PATT = {
        'uri:openstat': {
            'uri': r'/\?_openstat=',
        },
        'uri:wp_cron': {
            'uri': r'^/wp-cron\.php\?'
        },
        'uri:wp_static_files': {
            'uri': r'^/(?:wp-content|wp-includes)/[^\?#]+\.(css|js|woff|ttf|eot|svg|jpg|png|gif)+(\?|\?ve?r?=[\da-f\.]+)?$',
        },
        'hacker:uri:scan:shells': [
            {'uri': r'\.(aasf|index\.php)'},
            {'uri': r'xo='},
            {'uri': r'L3dwLWNvbnRlbnQvcGx1Z2lucy8|cabee63d9736600fd19e3a724f9ddaeb'},
        ],
        'hacker:uri:scan:dev_mistakes': {
            'uri': r'\/\.(ftpconfig|env|svn|vscode|remote-sync|wp-config)',
        },
    }

    skip_my_ip = {
        'ip': r'(?:127.0.0.1|192.168.0.1)',
    }

    site = {
        'site1': [
            {'uri': r'^/(\?utm_source=[^/?#.\\]+)?$'},
            {'uri': r'(\?|&)yclid=[\d]+$'},
            {'uri': r'^/favicon\.ico$'},
            {'uri': r'^/sitemap_index\.xml$'},
            {'uri': r'^/page-sitemap\.xml$'},
            {'uri': r'^/sale/?(\?utm_source=[^/?#.\\]+)?$'},
            {'uri': r'^/contacts?/?(\?utm_source=[^/?#.\\]+)?$'},
            {'uri': r'^/(?:ge[a-z]+s|st[a-z]+s|tu[a-z]+s)/?$'},
            {'uri': r'^/price-(?:ge[a-z]+r|st[a-z]+r|tu[a-z]+e)/?$'},
            {'uri': r'^/remont-(?:ge[a-z]+v|st[a-z]+v|tu[a-z]+n)/?(\?utm_source=[^/?#.\\]+)?$'},
            {'uri': r'^/dis[a-z]+t-(?:10|25|each-5)/?$'},
            {'uri': r'^/gu[a-z]+e(?:-promo)?/?$'},
            {'uri': r'^/tabs/price-tabs/?$'},
            {'uri': r'^/za[a-z-]+t/?$'},
            {'uri': r'^/wp-content/uploads/[^?#.\\]+\.webp$'},
        ],
        'site2':  [
            {'uri': r'^/robots\.txt$'},
            {'uri': r'^/favicon\.ico$'},
            {'uri': r'^/apple[^/?#\\]+\.png$'},
            # sitemaps
            {'uri': r'^/(?:attachment|author|category|page|post|bwg_(?:album|gallery))-sitemap\.xml$'},
            {'uri': r'^/sitemap_index\.xml$'},
            # mix up pages
            {'uri': r'^/(?:bio|music)/[^?#\\]+\.html$'},
            # general pages
            {'uri': r'^/(\?utm_source=[^/?#.\\]+)?$'},
            {'uri': r'^/wp-content/uploads/[^?#.\\]+\.pdf$'},
            {'uri': r'^/(?:our-objects|contact|about|galery|pr[a-z-]+)/?$'},
            {'uri': r'^/(?:partners|bwg_(?:album|gallery)|accessory|installation|products)/?([^.?#\\]+(?:\.html(\?download=[\d]+|[^?#.\\]+)?|\/?))?$'},
        ],
    }

    # Search for anomalies
    # print_report(files, ['date', ['code', 'method', 'uri:100', 'ip:20']], {
    # print_report(files, ['date', ['code', 'method', 'uri:100'], 'ip:20'], {
    # print_report(files, ['date', 'ip:20', ['code', 'method', 'uri:100']], {
    #     'exclude': [
    #         skip_my_ip,
    #         # Common requests
    #         PATT['uri:openstat'],
    #         PATT['uri:wp_cron'],
    #         PATT['uri:wp_static_files'],
    #         # exclude login attempt to admin-ajax.php
    #         {'uri': r'^/wp-admin/admin-ajax.php$'},
    #         # site
    #         site['site2'],
    #     ],
    # })

    # Extract only important
    # print_report(files, ['date', ['code', 'method', 'uri:100'], 'ip:20'], {
    # print_report(files, [['code', 'method', 'uri:100'], 'ip:20'], {
    #     'exclude': [skip_my_ip],
    #     'include': {'uri': r'^/wp-admin/admin-ajax.php$'},
    # })

    print_report(files, ['uri:100', ['code', 'method', 'protocol'],  'ip:20'], {
        'exclude': [skip_my_ip],
        'include': {'ip': r'^141.8.132.\d{1,3}$'},
    })
    sys.stdout.flush()
    sys.stdout.close()

    sys.stderr.flush()
    sys.stderr.close()
