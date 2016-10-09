import requests
from lxml import html, etree
from html.parser import HTMLParser
from html.entities import name2codepoint
import os

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print("Start tag:", tag)
        for attr in attrs:
            print("     attr:", attr)

    def handle_endtag(self, tag):
        print("End tag  :", tag)

    def handle_data(self, data):
        print("Data     :", data)

    def handle_comment(self, data):
        print("Comment  :", data)

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        print("Named ent:", c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        print("Num ent  :", c)

    def handle_decl(self, data):
        print("Decl     :", data)


class IQ5010:
    """query the IQ 5010 web site for information on airports"""
    def __init__(self):
        self.parser = MyHTMLParser()
        pass

    def query(self, faa_id):
        payload = {'Site': faa_id, 'AptSecNum': '0'}
        r = requests.post("http://www.gcr1.com/5010web/airport.cfm", params=payload)
        html_prescrub = '<TABLE' + 'TABLE'.join(r.text.split('TABLE')[1:])
        self.parser.feed(html_prescrub)
        tree = html.fromstring(html_prescrub)
        return tree

if __name__ == '__main__':
    cls = IQ5010()
    html = cls.query('AIK')
    print(html)
