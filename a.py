
import requests
from bs4 import BeautifulSoup
import csv
#

url="https://jntuh.ac.in/"
page=requests.get(url)
#

soup=BeautifulSoup(page.content,'html.parser')
#print(soup.text)
images=soup.find_all
print(images)