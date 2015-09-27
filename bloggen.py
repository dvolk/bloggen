# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
import glob, codecs, os.path, math, datetime, argparse, re, types
from os import mkdir
from shutil import rmtree, copyfile
from bs4 import BeautifulSoup

args = None
site_name = 'dvolk.github.io'
site_url = 'https://dvolk.github.io'
author = 'Denis Volk'
index_description = 'Blog of {0}'.format(author)
post_time_parse_fmt = '%d/%m/%Y %H:%M'
post_time_output_fmt = '%Y-%m-%d'
posts_per_page = 10
create_rss = True
top_links = [
#    text,     bg color   link
    ("About",  "#CAFF70", "{0}/about_me.html"),
    ("Github", "#97FFFF", "https://github.com/dvolk"),
    ("Flickr", "#FF6EB4", "https://www.flickr.com/photos/denis_volk")
]

header = """<!DOCTYPE html>
<html>
<head>
<title>{0}</title>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
<meta name="generator" content="bloggen.py see https://github.com/dvolk/bloggen" />
<meta name="author" content="{1}" />
<meta name="viewport" content="width=device-width" />
"""

index_header = """<meta name="description" content="{2}" />
<link rel="canonical" href="{0}" />
<link rel="icon" href="./favicon.png" type="image/png" />
<link rel="stylesheet" type="text/css" href="./index.css" />
<link rel="alternate" type="application/rss+xml" href="./feed.rss" title="RSS feed for {1}">
</head>
<body>
<div class='outer'>
<div class='inner'>
<div class='header'>
<div class='logo'>
<h1><a style='color: black;' href='./index.html'>{1}</a></h1>
</div>
<div class='navigation'>"""

post_header = """<meta name="description" content="{1}" />
<link rel="icon" href="../favicon.png" type="image/png" />
<link rel="stylesheet" type="text/css" href="../index.css" />
<link rel="alternate" type="application/rss+xml" href="../feed.rss" title="RSS feed for {0}">
</head>
<body>
<div class='outer'>
<div class='inner'>
<div class='header'>
<div class='logo'>
<h1><a style='color: black;' href='../index.html'>{0}</a></h1>
</div>
<div class='navigation'>"""

footer = """</div>
</div>
</body>
</html>"""

class Post:
    def __init__(self, link, snip, time, author, title, rest, want_toc):
        self.link, self.snip, self.time = link, snip, time
        self.author, self.title, self.rest = author, title, rest
        self.want_toc = want_toc

def mk_index_filename(page):
    if page == 0: return "index.html"
    else: return 'index-{0}.html'.format(str(page))

def mk_pagination(index, page, pages):
    if pages == 1: return
    index.write("<div class='bottom'>")
    if page + 1 != pages:
        index.write("<p class='page_nav'><a class='page_nav' href='./index-{0}.html'><b>← prev</b></a></p> ".format(str(page + 1)))
    if page != 0:
        index.write("<p class='page_nav'><a class='page_nav' href='./{0}'><b>next →</b></a></p>".format(mk_index_filename(page - 1)))
    index.write("</div>")

def unicode_wrap(str):
    try:
        return unicode(str, 'utf-8')
    except NameError: # py3
        return str

def generate_toc(soup):
    """Table of contents"""
    h3s = []
    for i, h3 in enumerate(soup.find_all('h3')):
        h3['id'] = 'sec-{0}'.format(i)
        h3s.append(h3.get_text())
    if h3s == []: return ""

    out = "<div class='toc'><h3>Table of Contents</h3>\n<ul>\n"
    for i, h3 in enumerate(h3s):
        out += "<li><a href='#sec-{0}'>{1}</a></li>\n".format(i, h3)
    out += "</ul>\n</div>\n"
    return out

def process_vars(soup):
    posts = site_url + "/posts"
    for a in soup.find_all('a'):
        a['href'] = re.sub("__SITEROOT__", site_url, a['href'])
        a['href'] = re.sub("__SITEPOST__", posts, a['href'])
    return soup

def mk_entry(post, in_entry):
    ret = '<div class="entry">\n'
    path = site_url + "/posts"
    ret += "<h2 style='display: inline'><a href='{0}/{1}.html'>{2}</a></h2>\n".format(path, post.link, post.title)
    if post.author or post.time:
        ret += "<br/><p style='font-size: 0.8em; display: inline'>"
        if post.time:   ret += " <b>{0}</b>".format(datetime.datetime.strftime(post.time, post_time_output_fmt))
        if post.author: ret += " by <b>{0}</b>".format(post.author.text)
        ret += "</p>\n"
    if post.snip is not None:
        ret += unicode_wrap(str(post.snip))
    if post.rest is not None:
        if not in_entry:
            ret += "<p><a href='{0}/{1}.html'>(read more)</a></p>\n".format(path, post.link)
        else:
            if post.want_toc:
                ret += generate_toc(post.rest)
            ret += unicode_wrap(str(post.rest))
    ret += "</div>\n"
    return ret;

def make_rss(posts, how_many):
    import PyRSS2Gen
    rss_items = []
    for post in posts[0:how_many]:
        link = "{0}/{1}.html".format(site_url, post.link)
        content = ""
        time = datetime.datetime(1970, 1, 1)
        if post.snip is not None: content += unicode_wrap(str(post.snip))
        if post.rest is not None: content += unicode_wrap(str(post.rest))
        if post.time is not None: time = post.time
        rss_item = PyRSS2Gen.RSSItem(
            title = post.title,
            link = link,
            guid = PyRSS2Gen.Guid(link),
            pubDate = time,
            description = content)
        rss_items.append(rss_item)
    rss = PyRSS2Gen.RSS2(title = site_name,
                         link = site_url,
                         description = index_description,
                         lastBuildDate = datetime.datetime.now(),
                         items = rss_items)

    with codecs.open('./generated/feed.rss', mode='w', encoding='utf-8') as rss_file:
        rss.write_xml(rss_file)

def nav_links(out, in_entry):
    # this span maintains the layout if there are no top links or rss
    out.write("<p><span style='font-size: 1.2em; visibility: hidden'>.</span>\n")
    for link in top_links:
        back = "." if in_entry else "./posts"
        out.write("<a style='background-color: {0}' class='top-link' href='{1}'>{2}</a> \n".format(link[1], link[2].format(back), link[0]))
    if create_rss:
        if in_entry: out.write("<a id='rss' href='../feed.rss'>RSS</a>")
        else: out.write("<a id='rss' href='./feed.rss'>RSS</a>")
    out.write("</p>\n</div>\n</div>\n")

def parse_post(contents, in_filename):
    # parse the input post file
    soup = BeautifulSoup(contents)
    process_vars(soup)
    title_content  = soup.find("span", {"class": "title"})
    time_content   = soup.find("span", {"class": "time"})
    author_content = soup.find("span", {"class": "author"})
    snip_content   = soup.find("div", {"class": "summary"})
    rest_content   = soup.find("div", {"class": "rest"})
    want_toc       = soup.find("span", {"class": "want_toc"}) # TODO: better way to set booleans?
    if time_content is not None:
        time_content = datetime.datetime.strptime(time_content.text, post_time_parse_fmt)
    if title_content is not None: title_content = title_content.text
    else: title_content = os.path.basename(in_filename)
    want_toc = True if want_toc is not None else False
    post = Post(os.path.basename(in_filename),
                snip_content, time_content, author_content, title_content, rest_content, want_toc)
    return post

def write_post(post, in_filename):
    # write blog post file
    out_filename = './generated/posts/{0}.html'.format(os.path.basename(in_filename))
    with codecs.open(out_filename, mode = 'w', encoding="utf-8", errors="xmlcharrefreplace") as out_doc:
        out_doc.write(header.format("{0} - {1}".format(post.title, site_name), author))
        # text to put into the description meta tag
        description = post.snip.get_text() if post.snip else ""
        description = description.replace('"', '')
        description = description.replace('\n', ' ')
        description = description.strip()
        out_doc.write(post_header.format(site_name, description))
        nav_links(out_doc, in_entry = True)
        out_doc.write(mk_entry(post, in_entry = True))
        out_doc.write(footer)
    return post

posts = []

def all_posts_by_date():
    global posts
    rest = ""
    for post in posts:
        rest += "<p><a href='{0}.html'>{1}</a>".format(post.link, post.title)
        if post.time:
            time_str = datetime.datetime.strftime(post.time, post_time_output_fmt)
            rest += " <span class='date_text'>{0}</span>".format(time_str)
        rest += "</p>\n"
    return Post("all_posts_by_date", None, None, None,
                "All posts by date", rest, False)

def all_posts_about(*fun_args):
    name = fun_args[0]
    tag = fun_args[1]
    global posts
    rest = "<p>Auto-generated list of all posts containing \"{0}\" in the title:<p>".format(name)
    for post in posts:
        if not re.search(name, post.title): continue
        rest += "<p><a href='{0}.html'>{1}</a>".format(post.link, post.title)
        if post.time:
            rest += " <span class='date_text'>{0}</span>".format(datetime.datetime.strftime(post.time, post_time_output_fmt))
        rest += "</p>\n"
    return Post("all_posts_about_{0}".format(tag), None, None, None, "All posts about {0}".format(name), rest, False)

def index_special_pages(s_posts):
    rest = "<p>This page contains a list of all auto-generated pages:</p>"
    for post in s_posts:
        rest += "<p><a href='{0}.html'>{1}</a></p>".format(post.link, post.title)
    return Post("autogenned_page_index", None, None, None, "Auto-generated pages", rest, False)

# to generate posts from functions rather than files,
# add them to special_pages. The elements of special pages are either
# function returning a post, or a tuple of a function returning a Post
# and a tuple of arguments to that function
special_pages = [all_posts_by_date,
                 (all_posts_about, ('Project X', 'project_x')),
                 (all_posts_about, ('bloggen.py', 'bloggen_py'))]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-g', '--generate',   type = str, nargs = 1)
    ap.add_argument('-n', '--no-index',   action = "store_true", help = "don't generate index")
    ap.add_argument('-s', '--skip-files', action = "store_true", help = "skip files beginning with . # or -")
    ap.add_argument('-q', '--quiet',      action = "store_true")
    ap.add_argument('-r', '--root',       type = str, nargs = 1, help = "override site root path")
    args = ap.parse_args()

    if args.root is not None:
        global site_url
        site_url = args.root[0]

    if not args.generate and not args.no_index:
        if os.path.exists('./generated/'):
            rmtree('./generated/')

        mkdir('./generated/')
        mkdir('./generated/posts/')

    for css_filename in glob.glob('./css/*'):
        copyfile(css_filename, './generated/' + os.path.basename(css_filename))
    for media_filename in glob.glob('./other/*'):
        copyfile(media_filename, './generated/' + os.path.basename(media_filename))

    global posts
    in_filenames = []

    if args.generate is not None:
        in_filenames = args.generate
    else:
        in_filenames = glob.glob('./content/posts/*')

    for in_filename in in_filenames:
        if args.skip_files and os.path.basename(in_filename)[0] in ['.', '#', '-']:
            continue
        with codecs.open(in_filename, mode="r", encoding="utf-8") as doc:
            post = parse_post(doc.read(), in_filename)
            posts.append(post)
            write_post(post, in_filename)

    # sort posts by date with posts with no date at the bottom
    posts = sorted(posts, key=lambda x: (x.time is not None, x.time), reverse=True)

    pages = int(math.ceil(float(len(posts)) / posts_per_page))

    special_posts = []
    for special_page in special_pages:
        if type(special_page) == types.FunctionType:
            post = special_page()
            write_post(post, special_page.__name__)
        if type(special_page) == tuple:
            fun = special_page[0]
            assert type(fun) == types.FunctionType
            post = fun(*(special_page[1]))
            write_post(post, post.link)
        posts.append(post)
        special_posts.append(post)

    autogen_index_post = index_special_pages(special_posts)
    write_post(autogen_index_post, autogen_index_post.link)
    posts.append(autogen_index_post)

    if args.no_index:
        exit(0)

    if create_rss: make_rss(posts, posts_per_page)

    # generate index pages
    for page in range(pages):
        with codecs.open('./generated/' + mk_index_filename(page), mode='w', encoding="utf-8", errors="xmlcharrefreplace") as index:
            index.write(header.format(site_name, author))
            index.write(index_header.format(site_url, site_name, index_description))
            nav_links(index, in_entry = False)

            for post in posts[(page * posts_per_page):((page + 1) * posts_per_page)]:
                if not args.quiet:
                    print(" ({0}) {1}".format(page, post.title))
                index.write(mk_entry(post, in_entry = False))

            mk_pagination(index, page, pages)
            index.write(footer)

main()
