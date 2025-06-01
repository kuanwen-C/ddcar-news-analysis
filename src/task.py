import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import json
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
    
    def get_ddcar_articles(
        self,
        cate_id: int = 0,   #category id = all articles
        initial_page: int = 1,
        max_pages: int = 1000,
        checkpoint_file: str = "ddcar_checkpoint.json", #used to avoid losing data if crawling fail
        checkpoint_every: int = 5, #update checkpoint file every 5 pages
    ) -> pd.DataFrame:
        base_url = "https://www.ddcar.com.tw/api/web/news/categories/articles/list/"
        #Add headers to simulate a browser request and avoid being detected as a bo
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        # Load checkpoint if exists
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
                articles = checkpoint.get("articles", [])
                page = checkpoint.get("last_page", initial_page)
            print(f"Resuming from page {page}, already collected {len(articles)} articles.")
        else:
            articles = []
            page = initial_page

        while page <= max_pages:
            params = {"cateId": cate_id, "page": page}
            try:
                response = requests.get(base_url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                article_list = data.get("res", [])
            except Exception as e:
                print(f"---XXX---Crawl fail on page {page}: {e}---XXX---")
                break

            if not article_list:
                print("----***---No more articles found. Ending crawl---***---.")
                break

            for item in article_list:
                articles.append({
                    "title": item.get("title"),
                    "url": item.get("url")
                })
            
            #update checkpoint file
            if page % checkpoint_every == 0:
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "articles": articles,
                        "last_page": page + 1
                    }, f, ensure_ascii=False, indent=2)
                print(f"---File Updated---Checkpoint saved at page {page} with {len(articles)} articles.---File Updated---")

            page += 1
            time.sleep(random.uniform(0.5, 1.5))

        df = pd.DataFrame(articles)
        #output final crawling result
        df.to_csv("ddcar_articles.csv", index=False)
        print(f"---^__^--- All done. Total articles: {len(articles)}. Saved to ddcar_articles.csv ---^__^---")
        return df
    
    def run(
            self,
    )->None:
        soup=self.get_soup()
        self.get_brand_data(soup=soup)