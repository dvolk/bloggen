import markdown
import glob
import codecs
import os.path
from os import mkdir
from shutil import rmtree, copyfile
import BeautifulSoup
import math
import datetime

site_name = 'dvolk.github.io'
site_url = 'https://dvolk.github.io'
author = 'Denis Volk'
description = 'things'

header = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<title>{0}</title>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
<meta name="author" content="{1}" />
<meta name="description" content="{2}">
<meta name=viewport content="width=device-width, initial-scale=1.0">
"""

index_header = """
<link rel="canonical" href="{0}">
<link rel="icon" href="./favicon.png" type="image/png">
<link rel="stylesheet" type="text/css" href="./index.css">
</head>
<body>
<div class='outer'>
<div class='inner'>
<a href='./index.html'><h1>{1}</h1></a>
"""

post_header = """
<link rel="stylesheet" type="text/css" href="../index.css">
</head>
<body>
<div class='outer'>
<div class='inner'>
<a href='../index.html'><h1>{0}</h1></a>
"""

footer = """
</div>
</div>
</body>
</html>
"""

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
        index.write("<a href='./index-{0}.html'><p style='font-size: 1.4em; display: inline;'><b>&lt; prev</b></p></a> ".format(str(page + 1)))
    if page != 0:
        index.write("<a href='./{0}'><p style='font-size: 1.4em; display: inline;'><b>next &gt;</b></p></a><br/>".format(mk_index_filename(page - 1)))
    index.write("</div>")

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
        if post.time:   out_doc.write(" <b>{0}</b>".format(datetime.datetime.strftime(post.time, '%Y-%m-%d')))
        if post.author: out_doc.write(" by <b>{0}</b>".format(str(post.author)))
        out_doc.write("</p>")
    if post.snip is not None:
        out_doc.write(str(post.snip))
    if post.rest is not None and not in_entry:
        out_doc.write("<p>{0}(read more)</a></p>".format(link))
    out_doc.write("</div>")

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
            soup = BeautifulSoup.BeautifulSoup(doc.read())
            title_content  = soup.find("span", {"class": "title"})
            snip_content   = soup.find("div", {"class": "summary"})
            time_content   = soup.find("span", {"class": "time"})
            author_content = soup.find("span", {"class": "author"})
            rest_content   = soup.find("div", {"class": "rest"})
            if time_content is not None:
                time_content = datetime.datetime.strptime(time_content.text, '%d/%m/%Y %H:%M')
            if title_content is not None: title_content = title_content.text
            else: title_content = os.path.basename(in_filename)
            post = Post(os.path.basename(in_filename),
                        snip_content,
                        time_content,
                        author_content,
                        title_content,
                        rest_content)
            posts.append(post)

            # write blog post file
            out_filename = './generated/posts/{0}.html'.format(os.path.basename(in_filename))
            with codecs.open(out_filename, mode = 'w', encoding="utf-8", errors="xmlcharrefreplace") as out_doc:
                out_doc.write(header.format('{0} - {1}'.format(post.title, site_name), author, description))
                out_doc.write(post_header.format(site_name))
                mk_entry(out_doc, post, in_entry = True)
                if rest_content is not None:
                    out_doc.write(str(rest_content))
                out_doc.write(footer)

    # sort posts by date with posts with no date at the bottom
    posts = sorted(posts, key=lambda x: (x.time is not None, x.time), reverse=True)

    posts_per_page = 10
    pages = int(math.ceil(float(len(posts)) / posts_per_page))

    # generate index pages
    for page in range(pages):
        with codecs.open('./generated/' + mk_index_filename(page), mode='w', encoding="utf-8", errors="xmlcharrefreplace") as index:
            index.write(header.format(site_name, author, description))
            index.write(index_header.format(site_url, site_name))

            for post in posts[(page * posts_per_page):((page + 1) * posts_per_page)]:
                print page, post.link
                mk_entry(index, post, in_entry = False)

            mk_pagination(index, page, pages)
            index.write(footer)

main()
