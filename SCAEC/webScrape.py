import requests
from lxml import html
from html.parser import HTMLParser

class IQ5010:
    """query the IQ 5010 web site for information on airports"""
    def __init__(self):
        self.parser = HTMLParser()
        pass

    def query(self, faa_id):
        payload = {'Site': faa_id, 'AptSecNum': '0'}
        r = requests.post("http://www.gcr1.com/5010web/airport.cfm", params=payload)
        self.parser.feed(r.text)
        tree = html.fromstring(r.content)
        manager = tree.xpath('//*[@id="DataArea"]/table/tbody/tr/td[1]/table/tbody/tr[10]/td[2]/text()')
        return manager

if __name__ == '__main__':
    cls = IQ5010()
    html = cls.query('AIK')
    print(html)
