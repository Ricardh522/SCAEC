import requests
from django.views import View
from django.shortcuts import render
from .tools import webScrape, pdfPopulate
from django.utils import html


class IQ5010(View):
    """query the IQ 5010 web site for information on airports"""
    template_name = r'app/scraper.html'

    def get(self, request):
        crsr = pdfPopulate.crsr
        airports = pdfPopulate.get_airports(cursor=crsr)
        faa_ids = [x[0] for x in airports]
        single_html = []
        for faa_id in faa_ids:
            payload = {'Site': faa_id, 'AptSecNum': '0'}
            r = requests.get("http://www.gcr1.com/5010web/airport.cfm", params=payload)
            txt = r'<TABLE class={}_table'.format(faa_id)
            html_prescrub = txt + txt.join(r.text.split('TABLE')[1:-1]) + 'TABLE>'
            d = html.format_html("{}", html_prescrub)
            single_html.append(d)
            print(d)

        return render(request, "app/scraper.html", {"main_content": " ".join(single_html)})



