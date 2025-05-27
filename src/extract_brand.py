import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.ddcar.com.tw/news/categories/0/%E5%8D%B3%E6%99%82%E6%96%B0%E8%81%9E/list/"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

#select all <a> tags under <li> in ul.brand-list
brand_links = soup.select("ul.brand-list li a")

#used to save the brands listed on the website
brands = []

#we only parse span.hidden-xs and span.visible-xs so other contents under data-event-cate="文章分區 will not be parsed
for link in brand_links:
    zh_span = link.select_one("span.hidden-xs") #Chinese brand name
    en_span = link.select_one("span.visible-xs") #English brand name

    # Filter only links with both English and Chinese brand names
    if zh_span and en_span:
        brands.append({
            "English Name": en_span.get_text(strip=True),
            "Chinese Name": zh_span.get_text(strip=True)
        })

# save the listed brand names to CSV
df = pd.DataFrame(brands)
#breakpoint()  #used for data examination
df.to_csv("data/ddcar_brands.csv", index=False)
