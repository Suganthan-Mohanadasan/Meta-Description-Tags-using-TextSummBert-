# -*- coding: utf-8 -*-
"""Generating Meta Description Tags using TextSummBert by WordLift UPDATED APRIL 2020

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1W8Iggm-51joQPFoAJQWQ52mUuJ-h_azZ

# Generating Meta Description Tags

<table align="left">
  <td>
  <a href="https://wordlift.io">
    <img width=130px src="https://wordlift.io/wp-content/uploads/2018/07/logo-assets-510x287.png" />
    </a>
    </td>
    <td>
      by 
      <a href="https://wordlift.io/blog/en/entity/andrea-volpini">
        Andrea Volpini
      </a>
      <br/>
      <br/>
      MIT License
      <br/>
      <br/>
      <i>Last updated: <b>December 3rd, 2019</b></i>
  </td>
</table>

You can read the blog post here: https://wordlift.io/blog/en/write-meta-descriptions-bert/

## Importing and installing the libraries we need
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x
!pip install spacy==2.2.2
!pip install transformers
!pip install bert-extractive-summarizer==0.2.*

from bs4 import BeautifulSoup

import csv
import os
import requests, sys
import pandas as pd
import re
import numpy as np

"""## Downloading crawl data from Google Sheet 

The script uses the _url` CSV file generated with **WooRank Crawler** (or alternatively the data from **Screaming Frog**) that provides the list of URLs and the information of where the MD is missing.  

The data has been imported into Google Sheet so that we can inspect it. Change the URL below after publishing your CSV:


> 1. Open file from "My Drive" or "Upload"
2. File -> Publish to the web -> "Sheet name" option and "csv" option

### Using Screaming Frog
"""

# Download the list of URLs from Google Docs (file generated with Screaming Frog SEO Spider) 
# Replace the following with a crawl from your favorite website that you have published on Google Drive

!wget -O file.csv 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTwpVwmjW8xWd2VhNhfBv3FqBS0xyzzQVqu-WvnOyv1RjkTO6cT2hT4E7xZ47DZ_G5sPgUCJvDW7G5N/pub?output=csv'

"""#### Creating a Pandas DataFrame from Screaming Frog data


Following the file structure generated using the Screaming Frog's crawler, we will use the following columns:

- *url* (`cols='0'` | `Address`), 
- *http status* (`cols='2'` | `Status Code`), 
- *meta description lenght* (`cols='11'` | `Meta Description 1 Length`),
- *position* (`cols='48'` | `Position`),

We will then use *http status* to focus our analysis only to urls responding with `HTTP 200`.
"""

df = pd.read_csv('file.csv', # Update the string here to change the file
                 usecols=[0,2,10],  
                 header=0,
                 encoding="utf-8" )

"""#### Finding all URLs where meta description are missing"""

# Keep all rows representing a page with status = 200, with md 0, from the Italian blog and with Position < 15 
print("we have a total of:", len(df), " urls") 

df = df[(df['Status Code'] == 200) & ((df['Meta Description 1 Length'] == 0))] # Use this with Screaming Frog

print("we have to process:", len(df), " urls")

# Reindex df
df.index = range(len(df.index))

df.head()

"""## Summarizing

## Running the analysis 

In the next cells we have one function called `url_to_string` to get the text from a URL (make sure to fine-tune this one if you know the class that contains the body of the article on your website)
"""

# Get clean text from URL

def url_to_string(url):
  try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
    res = requests.get(url, headers=headers)
    html = res.text
    soup = BeautifulSoup(html, 'html5lib')
    for script in soup(["script", "style", 'aside']):
        script.extract()
    
    # uncomment the lines in the if/else block and comment the one after if you know the name of the class containing the article body 
    if isinstance(soup.find('div', {'class' :'entry-content'}), type(None)): # here is the div containing the content
      return " ".join(re.split(r'[\n\t]+', soup.get_text()))
    else:
      return " ".join(re.split(r'[\n\t]+', soup.find('div', {'class' :'entry-content'}).text))   

  except requests.exceptions.HTTPError as err:
    print(err)
    sys.exit(1)
    return err

# Create a list to store the MDs
data_x = [] 

from summarizer import Summarizer
# For each URL in the input CSV run the analysis and store the results in the list 
for i in range(len(df)):
    # Here is the URL to be analyzed
    line = df.iloc[i][0]

	# Error handling for HTTP connection problems
    try:
       body = url_to_string(line)
    except:
    	print('error while fetching', line, err)
    
	# BERT
    print("Summarizing URL via BERT: " + line)
    model = Summarizer()
    result = model(body, min_length=60, ratio=0.005)
    full = ''.join(result)
    print(full)

	# Storing all values into the list 
    data_x.append({"url":line, "BERT":full})

"""### Testing BERT Multilingual

This cell is alternative to the cells above and will load a varian of BERT called `bert-base-multilingual-cased`.

Trained on cased text in the top **104 languages** with the largest Wikipedias.
"""

# Create a list to store the MDs
data_x = [] 

from transformers import BertTokenizer, BertModel

bert_model = BertModel.from_pretrained('bert-base-multilingual-cased', output_hidden_states=True)
bert_tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

from summarizer import Summarizer
# For each URL in the input CSV run the analysis and store the results in the list 
for i in range(len(df)):
    # Here is the URL to be analyzed
    line = df.iloc[i][0]

	# Error handling for HTTP connection problems
    try:
       body = url_to_string(line)
    except:
    	print('error while fetching', line, err)
    
	# BERT
    print("Summarizing URL via BERT  ML: " + line)
    model = Summarizer(custom_model=bert_model, custom_tokenizer=bert_tokenizer)
    result = model(body, min_length=60, ratio=0.005)
    full = ''.join(result)
    print(full)

	# Storing all values into the list 
    data_x.append({"url":line, "BERT":full})

"""### Testing the brand new ALBERT implementation

This cell is alternative to the cell above and will load ALBERT (see: "[ALBERT: A Lite BERT For Self-Supervised Learning of Language Representations](https://arxiv.org/abs/1909.11942)")
"""

# Create a list to store the MDs
data_x = [] 

from transformers import AlbertTokenizer, AlbertModel

albert_model = AlbertModel.from_pretrained('albert-base-v1', output_hidden_states=True)
albert_tokenizer = AlbertTokenizer.from_pretrained('albert-base-v1')

from summarizer import Summarizer
# For each URL in the input CSV run the analysis and store the results in the list 
for i in range(len(df)):
    # Here is the URL to be analyzed
    line = df.iloc[i][0]

	# Error handling for HTTP connection problems
    try:
       body = url_to_string(line)
    except:
    	print('error while fetching', line, err)
    
	# BERT
    print("Summarizing URL via ALBERT: " + line)
    model = Summarizer(custom_model=albert_model, custom_tokenizer=albert_tokenizer)
    result = model(body, min_length=60, ratio=0.005)
    full = ''.join(result)
    print(full)

	# Storing all values into the list 
    data_x.append({"url":line, "BERT":full})

"""## Storing data 

In the following cells we are going to save a CSV containing for each url the summaries generated by the different algos.
"""

# Save results to the output CSV
df_new = pd.DataFrame(data_x, columns=["url", "BERT"])

df_new.head()

from google.colab import files

# We set the variable forthe name of the CSV where we will store the new MDs 
outputcsv = 'new-md.csv'
print("output csv name: ", outputcsv)

df_new.to_csv(outputcsv, encoding='utf-8', index=False)
print("Saving results on:", outputcsv)
files.download(outputcsv)

"""# License

MIT License

Copyright (c) 2019 Andrea Volpini, WordLift

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# New Section
"""