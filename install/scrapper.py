import csv
import pandas as pd
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By


URLs = pd.read_csv("urls.csv")["urls"]
options = Options()

# this option prevent creating Firefox window
options.add_argument("--headless")

webd = Firefox(options=options)

results = [["Name", "Site"]]


def scrap(url):
    webd.get(url)
    webd.implicitly_wait(10)

    for card in webd.find_elements(By.CLASS_NAME, "lMCard"):
        try:
            card.click()

            data = []

            for title in webd.find_elements(By.CLASS_NAME, "nameContainer"):
                data.append(title.text)

            for title in webd.find_elements(By.CLASS_NAME, "ibs_3btns"):
                if str(title.get_attribute("aria-label")).lower() == "website":
                    data.append(title.get_attribute("href"))

            if len(data) == 1:
                data.append("0")

            results.append(data)
        except Exception as e:
           print(e) 
           _ = e
    try:
        next_p = webd.find_element(By.CLASS_NAME, "bm_rightChevron")
        if next_p:
            if next_p.get_attribute("aria-label") == "Next Page":
                print("next page ...")
                next_p.click()
                scrap(url)
    except Exception as e:
        _ = e 


for u in URLs:
    print(f"[+] scrapping {u} ...")
    scrap(u)


with open("restaurants.csv", "w") as file:
#    print(results)
    writer = csv.writer(file)
    writer.writerows(results)

