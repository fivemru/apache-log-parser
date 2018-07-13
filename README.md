# Apache log parser

```
'">-----X--S--S-------------------------S--Q--L----I--N--J-E--C-T-----

Hello friend!
This is a simple Apache log parser with a flexibly ability to group 
entries by column and|or filter it. Set up printing as you like!

--------m--a--l--i--c--i--o--u--s----r--e--q--u--e--s--t--s--------<"'
```

I use it to track robot requests, attempts to hack the site, and for general statistics.

_This is my first script on the `Python`. Please, rub my nose in every horrible string of code if you can. I want to be better. =)_


## Example outputs

**One of the variants of grouping**

```
Group by :  ['date', 'ip:20', ['code', 'method', 'uri:100']]

[  7.15 s,     107248 : (+     37680, -     69568) lines,  15001.93 l/s] 2018-01-13-site.net_access.log
[ 18.38 s,     185776 : (+    177003, -      8773) lines,  10105.29 l/s] 2018-02-15-site.net_access.log
[  3.19 s,      54966 : (+     21227, -     33739) lines,  17209.65 l/s] 2018-06-site.net_access.log
[  1.29 s,      16924 : (+     10484, -      6440) lines,  13093.75 l/s] 2018-07-site.net_access.log
[  0.09 s,       2640 : (+       178, -      2462) lines,  29022.45 l/s] site.net_access.log

Total
[ 30.11 s,     367554 : (+    246572, -    120982) lines, 12206.89 l/s]


2017-02-23
        5.18.223.132
                2       200     POST    /wp-admin/admin-ajax.php
2017-02-24
        141.8.184.105
                1       301     GET     /c
                1       301     GET     /d
        52.174.145.81
                1       404     GET     /effe
        62.16.25.217
                2       301     GET     /administrator/index.php
                1       404     GET     /admin.php
                2       404     GET     /administrator/
...
```


**Another way grouping** (_Without filters, the speed is noticeably larger =)_)

```
Group by :  ['method', 'code']

[  2.01 s,     107248 : (+    107248, -         0) lines,  53453.60 l/s] 2018-01-13-site.net_access.log
[  3.31 s,     185776 : (+    185776, -         0) lines,  56139.12 l/s] 2018-02-15-site.net_access.log
[  0.99 s,      54966 : (+     54966, -         0) lines,  55528.67 l/s] 2018-06-site.net_access.log
[  0.30 s,      16924 : (+     16924, -         0) lines,  57197.19 l/s] 2018-07-site.net_access.log
[  0.05 s,       2640 : (+      2640, -         0) lines,  54716.42 l/s] site.net_access.log

Total
[  6.65 s,     367554 : (+    367554, -         0) lines, 55266.40 l/s]


GET
        117321  200
        84      206
        8287    301
        118     302
        848     304
        4       400
        4       403
        3007    404
        47      405
        16      500
HEAD
        175     200
        86      301
        1       302
        65      404
POST
        236071  200
        183     204
        195     302
        8       400
        1028    404
        6       500
```


## Table of content

- [Apache log parser](#apache-log-parser)
    - [Example outputs](#example-outputs)
    - [Table of content](#table-of-content)
    - [Python version](#python-version)
    - [Usage](#usage)
        - [print_report()](#print_report)
    - [How it works?](#how-it-works)
    - [Named columns](#named-columns)
    - [Filtering](#filtering)
        - [Filters with AND logic](#filters-with-and-logic)
        - [Filters with OR logic](#filters-with-or-logic)
    - [Grouping](#grouping)
        - [Grouping columns](#grouping-columns)
        - [Grouping several columns](#grouping-several-columns)
        - [Set width of column](#set-width-of-column)
    - [How I usually use it?](#how-i-usually-use-it)
    - [Examples](#examples)
        - [Workflow for new site](#workflow-for-new-site)
        - [For daily view](#for-daily-view)
    - [To do](#to-do)
    - [P.S.](#ps)


## Python version

I tested it with `2.7.15` and `3.7.0`.


## Usage

1. Specify the [filters](#filtering) and columns for [grouping](#grouping) in the [print_report](#print_report) function.

1. Then run the script

    ```
    python log.py site.com.access*.log
    ```
    _You can process multiple *.log files at once._

1. Enjoy =)

### print_report()
```print_report(path_files=[] [, filters={} ]])```

```Python
    print_report(
        files,
        # Group by columns
        ['date', 'ip:20', ['code', 'method', 'uri:100']],
        # Exclude filters
        {
            'exclude': [
                # requests from my ip
                { 'ip': r'(?:127.0.0.1|192.168.0.1)' },
                # and exclude requests to the main page "/" and few legal requests
                { 'uri': r'^/$' },
                # for /about.html and /contact.html
                { 'uri': r'^/(?:about|contact)\.html$' },
            ],
            # Include filters
            'include': [
                # For example, will find requests from bots or empty User-Agent
                { 'ua': r'bot' },
                { 'ua': r'^$' },
            ]
        }
    )
```

## How it works?

* The script sequentially processes each file line by line.
* First of all each line is parsed by the ```parse_apache_line(line, sep=' ')``` function, splitting it by space into [named columns](#named-columns).
* Further, the line passes the *exclude* [filters](#filtering), and then the *include* ones.
* If the filters are passed, then a string is formed for [grouping](#grouping). A string is composed of one or [more](#grouping-several-columns) named columns. (If an array of arrays is passed).
* And at the end the line is grouped with exactly the same (counting).

_In fact, you can handle any types of logs. To do this, you need to add or modify the parsing function for the named columns (```parse_apache_line```) for your format and column separator._


## Named columns

Each line splitting by the ```parse_apache_line``` function into named columns, which uses for [filtering](#filtering) and [grouping](#grouping) purposes.

For example this line:

```
66.249.64.73 - - [12/Jul/2018:05:29:02 +0300] "GET /robots.txt HTTP/1.0" 200 2 "https://ref-site.net/" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Safari/537.36"
```

| Column name | ```Value```                                                                                                                        |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| ip          | ```66.249.64.73```                                                                                                                 |
| date        | ```12/Jul/2018``` when it passing throught filter and ```2018-07-12``` when printing                                               |
| code        | ```200```                                                                                                                          |
| method      | ```GET```                                                                                                                          |
| uri         | ```/robots.txt```                                                                                                                  |
| protocol    | ```HTTP/1.0```                                                                                                                     |
| request     | ```GET /robots.txt HTTP/1.0```                                                                                                     |
| ua          | ```Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Safari/537.36``` |
| ref         | ```https://ref-site.net/```                                                                                                        |


## Filtering

Filtering is performing by named columns. *Exclude* filter performing before *include*.

A filter is a string for a case-insensitive regular expression.

### Filters with AND logic

Filters with AND logic are passed as a dictionary.

```Python
{
    'method': r'POST',
    'uri': r'^/favicon\.ico$',
}
```
It corresponds to the ```POST``` request for ```/favacon.ico```.

### Filters with OR logic

Filters with OR logic are passed as a list.

```Python
[    
    {'method': r'POST'},
    {'uri': r'^/favicon\.ico$'},
]
```

It corresponds to any ```POST``` requests OR ```/favacon.ico``` separately.



## Grouping

Grouping defines a string whose occurrence is counted.

A string is the value of one or more named columns separated by a tab character.

The output is sorted by these lines.

### Grouping columns

Grouping columns are specified in list: ```['date', 'ip']```.

**Will be output something like:**

```
2018-07-01
        21      11.22.33.44
        1       11.22.33.55

2018-07-02
        6       11.22.33.55
        3       11.22.33.66
```

### Grouping several columns

In one line, you can group several columns at once: ```['date', ['code', 'ip']]```.

**Output:**

```
2018-07-03
        8       200     11.22.33.44
        2       404     11.22.33.44
        1       404     11.22.33.55
```

### Set width of column

After the column name through the colon, you can specify the minimal and|or maximal width of the column.

Minimal width of column: ```[['uri:20', 'code']]```

**Output:**

```
473     /                       200
372     /                       301
1       /aaaaaabbbbbbccccdddeeeeeeffffffggggghhhhhhhhhhhhh/    404
1       /.well-known/assetlinks.json    404
```

Maximal width of column: ```[['uri:.20', 'code']]```

**Output:**

```
473     /       200
372     /       301
1       /aaaaaabbbbbbccccddd    404
1       /.well-known/assetli    404
```

Minimal and maximal width of column: ```[['uri:20.20', 'code']]```

**Output:**

```
473     /                       200
372     /                       301
1       /aaaaaabbbbbbccccddd    404
1       /.well-known/assetli    404
```

## How I usually use it?

1. Browse all entries without filters
1. Gradually add regex for normal entries to exclude list
1. As result, only non-target entries remain
1. And then in another terminal I extract specific requests

## Examples

For example, I left in the script filters for my sites that I use.

### Workflow for new site

**In accordance with the [How I usually use it](#how-i-usually-use-it) :**

1. Browse all entries without filters

    ```Python
    print_report(files, [['code', 'method', 'uri:100']], {
        'exclude': [],
    })
    ```
    and run with ```less -S```: 
    ```
    python log.py site.net.access*.log | less -S
    ```

1. Gradually add regex for normal entries to exclude list

    Uncomment in turn and fill the filters. (_This is not very convenient =( but this is usually done for 1 site 1 time_)

    ```Python
    ## Grouping for easilly find normal requests
    print_report(files, [['code', 'method', 'uri:100']], {
    ## Grouping for precise find normal requests
    # print_report(files, [['code', 'method', 'uri:100'], 'ip:20'], {
    # print_report(files, ['ip:20', ['code', 'method', 'uri:100']], {
    # print_report(files, ['ref:20', ['code', 'method', 'uri:100']], {
    # print_report(files, ['ua', ['code', 'method', 'uri:100']], {
    # print_report(files, ['ua', ['ip']], {
        'exclude': [
            # Site Pages
            {'uri': r'^/$'},
            {'uri': r'^/robots\.txt$'},
            {'uri': r'^/favicon\.ico$'},
            {'uri': r'^/css/style\.css$'},
            {'uri': r'^/poisk[^/\\#?.]+te\.html.+'},
            {'uri': r'^/(support|radio|music|song)(?:\.html|\/)?$'},
            {'uri': r'^/js/[^\/?#\\]+\.js$'},
            {'uri': r'^/(?:bio|music|song|short_story)/[^\/?#\\]+(?:\.html|\/)?$'},
            {'uri': r'^/img/[a-z\d\-\_]+\.(?:png|jpg|gif)$'},
        ],
    })
    ```

1. As result, only non-target entries remain
        
    ```
    192.187.109.42
            1       200     POST    /wp-admin/admin-ajax.php
            1       200     GET     /wp-admin/admin-ajax.php?action=revslider_show_image&img=../wp-config.php
            1       404     GET     /wp-content/plugins/./simple-image-manipulator/controller/download.php?filepath=/etc/passwd
            1       404     GET     /wp-content/plugins/recent-backups/download-file.php?file_link=/etc/passwd
            1       404     POST    /uploadify/uploadify.php?folder=/
    ```

1. And then in another terminal I extract specific requests

    ```Python
    print_report(files, [['code', 'method', 'uri:100'], 'ip:20'], {
        'exclude': [skip_my_ip],
        'include': {'uri': r'^/wp-admin/admin-ajax.php'},
    })
    ```

1. ```Whois``` and ban hacker IP


### For daily view

```Python
## Grouping for daily view
# print_report(files, ['date', ['code', 'method', 'uri:100'], 'ip:20'], {
print_report(files, ['date', 'ip:20', ['code', 'method', 'uri:100']], {
    'exclude': [
        skip_my_ip,
        # site filters
        site['site1'],
    ],
})
```

## To do

- [ ]  Make it convenient to switch groups
- [ ]  `*.gz` and `*.log` files together


## P.S.

Pool requests are welcome =). Your experience is interesting.

**Thank you for attention!**
