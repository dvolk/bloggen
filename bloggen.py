# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
import glob, codecs, os.path, math, datetime
from sys import version_info
from os import mkdir
from shutil import rmtree, copyfile
from bs4 import BeautifulSoup

site_name = 'dvolk.github.io'
site_url = 'https://dvolk.github.io'
author = 'Denis Volk'
description = 'things'
post_time_parse_fmt = '%d/%m/%Y %H:%M'
post_time_output_fmt = '%Y-%m-%d'
posts_per_page = 10
create_rss = True
#              text,    css id,    link
top_links = [("About",  "about",   "http://dv.devio.us"),
             ("Github", "github",  "https://github.com/dvolk")]

header = """<!DOCTYPE html>
<html>
<head>
<title>{0}</title>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
<meta name="generator" content="bloggen.py see https://github.com/dvolk/bloggen" />
<meta name="author" content="{1}" />
<meta name="description" content="{2}" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />"""

index_header = """<link rel="canonical" href="{0}" />
<link rel="icon" href="./favicon.png" type="image/png" />
<link rel="stylesheet" type="text/css" href="./index.css" />
</head>
<body>
<div class='outer'>
<div class='inner'>
<div class='header'><div class='logo'><h1><a style='color: black;' href='./index.html'>{1}</a></h1></div>
<div class='navigation'>"""

post_header = """<link rel="stylesheet" type="text/css" href="../index.css" />
</head>
<body>
<div class='outer'>
<div class='inner'>
<div class='header'><div class='logo'><h1><a style='color: black;' href='../index.html'>{0}</a></h1></div>
<div class='navigation'>"""

footer = """</div>
</div>
</body>
</html>"""

class Post:
    def __init__(self, link, snip, time, author, title, rest):
        self.link, self.snip, self.time = link, snip, time
        self.author, self.title, self.rest = author, title, rest

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

def mk_entry(out_doc, post, in_entry):
    out_doc.write('<div class="entry">')
    link = ""
    if not in_entry:
        link = "<a href='./posts/{0}.html'>".format(post.link)
    else:
        link = "<a href='./{0}.html'>".format(post.link)
    out_doc.write("<h2 style='display: inline'>{0}{1}</a></h2>\n".format(link, post.title))
    if post.author or post.time:
        out_doc.write("<br/><p style='font-size:0.8em;display: inline'>")
        if post.time:   out_doc.write(" <b>{0}</b>".format(datetime.datetime.strftime(post.time, post_time_output_fmt)))
        if post.author: out_doc.write(" by <b>{0}</b>".format(post.author.text))
        out_doc.write("</p>")
    if post.snip is not None:
        out_doc.write(unicode_wrap(str(post.snip)))
    if post.rest is not None:
        if not in_entry:
            out_doc.write("<p>{0}(read more)</a></p>".format(link))
        else:
            out_doc.write(unicode_wrap(str(post.rest)))
    out_doc.write("</div>")

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
                         description = description,
                         lastBuildDate = datetime.datetime.now(),
                         items = rss_items)

    with codecs.open('./generated/feed.rss', mode='w', encoding='utf-8') as rss_file:
        rss.write_xml(rss_file)

def nav_links(out):
    # this span maintains the layout if there are no top links or rss
    out.write("<p ><span style='font-size: 1.2em; visibility: hidden'>.</span>")
    for link in top_links:
        out.write("<a id='{0}' href='{1}'>{2}</a> ".format(link[1], link[2], link[0]))
    if create_rss: out.write("<a id = 'rss' href='./feed.rss'>RSS</a>")
    out.write("</p></div></div>")

def main():
    if os.path.exists('./generated/'):
        rmtree('./generated/')

    mkdir('./generated/')
    mkdir('./generated/posts/')

    for css_filename in glob.glob('./css/*'):
        copyfile(css_filename, './generated/' + os.path.basename(css_filename))
    for media_filename in glob.glob('./media/*'):
        copyfile(media_filename, './generated/' + os.path.basename(media_filename))

    posts = []

    for in_filename in glob.glob('./content/posts/*'):
        with codecs.open(in_filename, mode="r", encoding="utf-8") as doc:
            # parse the input post file
            soup = BeautifulSoup(doc.read())
            title_content  = soup.find("span", {"class": "title"})
            time_content   = soup.find("span", {"class": "time"})
            author_content = soup.find("span", {"class": "author"})
            snip_content   = soup.find("div", {"class": "summary"})
            rest_content   = soup.find("div", {"class": "rest"})
            if time_content is not None:
                time_content = datetime.datetime.strptime(time_content.text, post_time_parse_fmt)
            if title_content is not None: title_content = title_content.text
            else: title_content = os.path.basename(in_filename)
            post = Post(os.path.basename(in_filename),
                        snip_content, time_content, author_content, title_content, rest_content)
            posts.append(post)

            # write blog post file
            out_filename = './generated/posts/{0}.html'.format(os.path.basename(in_filename))
            with codecs.open(out_filename, mode = 'w', encoding="utf-8", errors="xmlcharrefreplace") as out_doc:
                out_doc.write(header.format("{0} - {1}".format(post.title, site_name), author, description))
                out_doc.write(post_header.format(site_name))
                nav_links(out_doc)
                mk_entry(out_doc, post, in_entry = True)
                out_doc.write(footer)

    # sort posts by date with posts with no date at the bottom
    posts = sorted(posts, key=lambda x: (x.time is not None, x.time), reverse=True)

    pages = int(math.ceil(float(len(posts)) / posts_per_page))

    if create_rss: make_rss(posts, posts_per_page)

    # generate index pages
    for page in range(pages):
        with codecs.open('./generated/' + mk_index_filename(page), mode='w', encoding="utf-8", errors="xmlcharrefreplace") as index:
            index.write(header.format(site_name, author, description))
            index.write(index_header.format(site_url, site_name))
            nav_links(index)

            for post in posts[(page * posts_per_page):((page + 1) * posts_per_page)]:
                print(" ({0}) {1}".format(page, post.title))
                mk_entry(index, post, in_entry = False)

            mk_pagination(index, page, pages)
            index.write(footer)

main()
