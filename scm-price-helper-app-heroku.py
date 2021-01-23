import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import ast
import base64

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

st.write("""
# Steam Community Market - Advanced Price Helper App
""")

scm_url = st.text_input('Please enter the url address of Steam Community Market Listing', 'https://steamcommunity.com/market/listings/440/The%20Killing%20Tree')

# Scraping and Storing Objects
# Input from user will need to be a url for steam community market
#resp_object = requests.get('https://steamcommunity.com/market/listings/440/The%20Killing%20Tree') #url will be an input from user
resp_object = requests.get(scm_url) #url will be an input from user
soup = BeautifulSoup(resp_object.text,'html.parser')

market_listing_largeimage_url = soup.find("div",{"class":"market_listing_largeimage"}).contents[1]['src'] # item image url
price_history_string = ast.literal_eval(re.findall('(?<=line1=)(.+?\]\])',resp_object.text)[0]) # price history string
item_name = re.findall('(?<=<title>Steam Community Market :: Listings for )(.+?(?=<\/))',resp_object.text)[0] # name of item

# constructing a df with entire price history
times = []
prices = []
solds = []

for row in range(len(price_history_string)):

    timestamp = price_history_string[row][0]
    median_price_sold = price_history_string[row][1]
    number_sold = price_history_string[row][2]

    times.append(timestamp)
    prices.append(median_price_sold)
    solds.append(number_sold)

final_df = pd.DataFrame(list(zip(times,prices,solds)),columns=['timestamp','price_median (USD)','quantity_sold']) # constructing a dataframe with all attributes
final_df['timestamp'] = [x[:14] for x in final_df['timestamp']] # removing +0s
final_df['timestamp'] = pd.to_datetime(final_df['timestamp'],format='%b %d %Y %H').dt.tz_localize('UTC', ambiguous=True) # convert to datetime
final_df['item_name'] = item_name
final_df = final_df[[final_df.columns[-1]] + list(final_df.columns[:len(final_df.columns)-1])]
final_df['quantity_sold'] = pd.to_numeric(final_df['quantity_sold'])
final_df.set_index('timestamp', inplace=True)

# download item pic from the url extracted from earlier
with open('item_pic.jpg', 'wb') as handle:
    response = requests.get(market_listing_largeimage_url, stream=True)

    if not response.ok:
        print(response)

    for block in response.iter_content(1024):
        if not block:
            break

        handle.write(block)

from PIL import Image
image = Image.open('item_pic.jpg')

# resize image
(width, height) = (image.width // 1, image.height // 1)
image = image.resize((width, height))

st.image(image, caption='')#,use_column_width=True)

st.write("""
# Median Price Sold (USD)

##### *Drag & Scroll inside the chart to Move & Zoom-in*
""")
st.line_chart(final_df['price_median (USD)'])

st.write("""
# Quantity Sold
""")
st.line_chart(final_df['quantity_sold'])


def download_link(object_to_download, download_filename, download_link_text):
    """
    Generates a link to download the given object_to_download.

    object_to_download (str, pd.DataFrame):  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
    download_link_text (str): Text to display for download link.

    Examples:
    download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
    download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')

    """
    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_csv()

    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()

    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'

st.write("""
### Download data for %s's Price and Volume Sold (at hourly level) in Excel
"""%item_name)

# Examples
st.write(final_df)

if st.button('Export to Excel (CSV)'):
    tmp_download_link = download_link(final_df, 'SCM Price and Volume Sold %s.csv'%item_name, 'Click here to download!')
    st.markdown(tmp_download_link, unsafe_allow_html=True)
