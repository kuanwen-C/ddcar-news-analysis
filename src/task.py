import requests
from bs4 import BeautifulSoup
import pandas as pd
class DdcarCrawler():

    def __init__(self):
        self.url="https://www.ddcar.com.tw/news/categories/0/%E5%8D%B3%E6%99%82%E6%96%B0%E8%81%9E/list/"
        self.brand_to_keywords: dict[str,list[str]] = {}  #brand → list of associated keywords
        self.keyword_to_brand : dict[str,str] = {}   #keyword → brand (lowercased for matching)
        self.all_keywords :list[str] = []  #flattened keyword list for efficient scanning

    #Fetch HTML content from DDCAR brand section using requests and BeautifulSoup
    def get_soup(
            self,
    ) -> BeautifulSoup:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    
    #get the EV car brands listed on the webpage & and their Mandarin keyword
    def get_brand_data(
            self,
            soup:BeautifulSoup,
    )->None:
        #select all <a> tags under <li> in ul.brand-list, Extract brand names from ul.brand-list li a
        brand_links = soup.select("ul.brand-list li a")
        for link in brand_links:
            zh_span = link.select_one("span.hidden-xs") #e.g <span class="hidden-xs">Volvo | 富豪</span>
            en_span = link.select_one("span.visible-xs") 

            if zh_span and en_span:
                en_name = en_span.get_text(strip=True) #(English name)
                zh_full = zh_span.get_text(strip=True) #(full string: "Brand | 中文名") e.g Volvo | 富豪
                if "|" in zh_full:  
                    zh_name = zh_full.split("|")[1].strip()
                    self.brand_to_keywords[en_name] = [en_name,zh_name]
                    for kw in [en_name, zh_name]:
                        lower_kw = kw.lower() # 忽略大小寫問題
                        self.keyword_to_brand[lower_kw] = en_name
                        self.all_keywords.append(lower_kw)
            
    
    def run(
            self,
    )->None:
        soup=self.get_soup()
        self.get_brand_data(soup=soup)