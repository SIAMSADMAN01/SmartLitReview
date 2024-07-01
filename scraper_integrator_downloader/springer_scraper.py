# import neccessary libraries:
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import seaborn as sb
import seaborn as sns
from matplotlib import pylab
from pylab import *
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import colors
import random
import os
import io
import spacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector
from langdetect import DetectorFactory, detect, detect_langs
from iso639 import languages
from pypdf import PdfReader
from time import sleep
import warnings
warnings.filterwarnings('ignore')


######################################################################################################################################################################

# get the user input:
def getUserInput():

    # user input => search keyword:
    search_keyword = input ("Hello.. Please enter your search keywords for the papers.\nKeywords --> ")
    split_inputs = '+'.join(search_keyword.split())
            

    # user input => year range for the crawl papers:
    print("To scrape papers from a specific publication year, please specify the maximum and minimum range of years. Example input: 2015, 2021, 2024\n")

    while True:
        try:
            max_year = int(input("Maximum year:"))
            min_year = int(input("\nMinimum year:"))
                
        except ValueError:
            print("\n\nInvalid input, please follow the example of the input and enter again correctly.\n")
            continue         
        
        else :
            break


    # user input => regex pattern for title match:
    title_match_regex_pattern = input ("For the regex pattern match, enter the keyword group number as 'a', 'b', 'c',  etc... to match the title and abstract of the relevant paper.\n\nExample: If you want to match two diffrent group of keywords then input as: a,b\n\nGroup: ")

    title_match_regex_pattern = list(title_match_regex_pattern)

    pattern_list = []
    for n in title_match_regex_pattern:
        x = re.search(r",|\s", n)
        if x == None:
            
            pattern_list.append(input (f"To only keep the relevant papers from the crawled papers, please enter specific keywords for the regex pattern match.\nExample:keyword_x|KEYWORD_x|keyword_x|KEYWORD_x|Keyword_x\n\nKeywords group {n}: --> "))


    # user input => which paper's language to keep:
    paper_lang_choice = int(input("Hello.. Please enter 1 for keeping the 'English' papers only.\n# Enter 2 for keeping 'All-Language papers'\n--> "))

    if paper_lang_choice == 1:
        keep_paper_lang = "English"
    elif paper_lang_choice == 2:
        keep_paper_lang = "All-Language"
    else:
        print("\n\nInvalid input, please follow the example of the input and enter again correctly.")


    return search_keyword, split_inputs, max_year, min_year, pattern_list, paper_lang_choice



######################################################################################################################################################################

# function to create acronym
def fxn(stng):
   
    # add first letter
    oupt = stng[0:2]
     
    # iterate over string
    for i in range(1, len(stng)):
        if stng[i-1] == ' ':
           
            # add letter next to space
            oupt += "_"+stng[i:i+2]

    return oupt


# function for re-arrange the columns:
def rearr_col_pos(dataframe,col_name, col_new_pos):
    col = dataframe.pop(col_name)
    dataframe.insert(col_new_pos, col.name, col)
    

# separate the detected paper's language and probability column:
def separateLangProb (dataframe, column):

    # language column:
    language_detect_list = dataframe[column].tolist()

    detect_lang = [] 

    for value in language_detect_list:
        
        if value != None:
            
            value = str(value)
            x = re.search(r"(.*?:){1}(.*?)\,", value)
            x = x.group(2)
        
            x = x.replace("'", "")
            x = x.strip()
        
            if x != None:
                detect_lang.append(x)
            else:
                detect_lang.append(None)
                
        else:
            detect_lang.append(None)
            
    dataframe.insert(loc=7, column="Paper_Language", value=detect_lang)


    # probablity column:
    language_probablity_list = dataframe[column].tolist()

    lang_probab = [] 

    for value in language_probablity_list:
        
        if value != None:
            
            value = str(value)
            x = re.search(r"(\d+.\d+)", value)
            x = float(x.group())
            x = round(x, 2)
        
            if x != None:
                lang_probab.append(x)
            else:
                lang_probab.append(None)
                
        else:
            lang_probab.append(None)
            
    dataframe.insert(loc=8, column="Probability_of_detected_Language", value=lang_probab)

    # drop the existing column "Language" from the dataset:
    dataframe = dataframe.drop(columns = column)

    # change language code to full name:
    dataframe['Paper_Language'] = dataframe['Paper_Language'].apply(lambda x: languages.get(alpha2=x).name)

    return dataframe


######################################################################################################################################################################

# function for adding search rersult data to the dataframe:
def add_SearchResult_data(total_searched_paper, total_scraped_paper, total_paper_after_removed_irrelevant_paper, total_paper_after_removed_duplicate_paper, total_paper_after_removed_out_of_range_year_paper, total_final_paper_after_removed_non_desired_lang_paper):
    
    search_result_df['search_for_total_number_of_paper'].extend(total_searched_paper)
    search_result_df["total_scraped_paper"].extend(total_scraped_paper)
    search_result_df['total_paper_after_removed_irrelevant_paper'].extend(total_paper_after_removed_irrelevant_paper)
    search_result_df['total_paper_after_removed_duplicate_paper'].extend(total_paper_after_removed_duplicate_paper)
    search_result_df['total_paper_after_removed_out_of_range_year_paper'].extend(total_paper_after_removed_out_of_range_year_paper)
    search_result_df['total_final_paper_after_applied_language_filter'].extend(total_final_paper_after_removed_non_desired_lang_paper)
    
    return pd.DataFrame.from_dict(search_result_df, orient='index')


# define spacy language detector pipeline:
def get_lang_detector(nlp, name):
    return LanguageDetector()
nlp = spacy.load("en_core_web_sm")
Language.factory("language_detector", func=get_lang_detector)
nlp.add_pipe('language_detector', last=True)


# function for crawl the inforamtion of the web page:
def get_webpage_data(url):
  
    H = ("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36", 
        "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15")

    Agent = H[random.randrange(len(H))]
    header = {
    'authority': 'www.google.com',
    'user-agent': Agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
            }
    
    try:
        response = requests.get(url, headers=header, verify=False).content

    except:
        raise Exception('Failed to fetch the requested data....!')

    # create the dataset:
    dataset = pd.read_csv(io.StringIO(response.decode('utf-8')))

    return dataset

######################################################################################################################################################################

# searcing info and result dataframe:
search_result_df = {
                    "search_for_total_number_of_paper" : [],
                    "total_scraped_paper" : [],
                    "total_paper_after_removed_irrelevant_paper" : [],
                    "total_paper_after_removed_duplicate_paper" : [],
                    "total_paper_after_removed_out_of_range_year_paper" : [],
                    "total_final_paper_after_applied_language_filter" : []
                }


######################################################################################################################################################################

# get user inputs:
search_keyword, split_inputs, max_year, min_year, pattern_list, paper_lang_choice = getUserInput()

# springer url:
url = f"https://link.springer.com/search/csv?date-facet-mode=between&showAll=false&query={split_inputs}&facet-end-year={max_year}&facet-start-year={min_year}"

# get dataset:
springer_dataset = get_webpage_data(url)

# drop the non-necessary columns from the dataset:
springer_dataset = springer_dataset.drop(columns= ['Book Series Title', 'Journal Volume', 'Journal Issue'])

# rename the columns:
springer_dataset.columns = springer_dataset.columns.str.replace('Item Title', 'Paper_Title')
springer_dataset.columns = springer_dataset.columns.str.replace('Publication Year', 'Publication_Year')
springer_dataset.columns = springer_dataset.columns.str.replace('Authors', 'Author')
springer_dataset.columns = springer_dataset.columns.str.replace('URL', 'PDF_link_of_paper')
springer_dataset.columns = springer_dataset.columns.str.replace('Publication Title', 'Publication_Title')
springer_dataset.columns = springer_dataset.columns.str.replace('Item DOI', 'Paper_DOI')
springer_dataset.columns = springer_dataset.columns.str.replace('Content Type', 'Content_Type')

#spacy-language_detection
title_list = springer_dataset['Paper_Title'].tolist()
title_language = []

try:
    for title in title_list:
        doc = nlp(title)
        detect_language = doc._.language
        title_language.append(detect_language)

except:
        title_language.append(None)

springer_dataset.insert(loc=2, column="Language", value = title_language)

dataset_temp_1 = springer_dataset

# remove the irrelevant papers:
for pattern in pattern_list:
  regex_pattern = re.compile(fr"\b({pattern})\b", re.IGNORECASE)
  dataset_temp_1 = dataset_temp_1[dataset_temp_1["Paper_Title"].apply(lambda s: bool(regex_pattern.search(s)))]

# remove duplicates papers: 
dataset_temp_1["Paper_Title"] = dataset_temp_1["Paper_Title"].str.strip()
dataset_temp_1["Paper_Title"] = dataset_temp_1["Paper_Title"].str.lower()
dataset_temp_2 = dataset_temp_1.drop_duplicates(subset = "Paper_Title", keep="first", inplace=False)

# re-arrange &filter the dataset by depending on the year, in descending order:
dataset_temp_3 = dataset_temp_2.drop(dataset_temp_2[(dataset_temp_2.Publication_Year > max_year) | (dataset_temp_2.Publication_Year < min_year)].index)
dataset_temp_3 = dataset_temp_3.sort_values(by = 'Publication_Year' , ascending = False)

# separate 'Language' into language and probablity column:
dataset_temp_3 = separateLangProb(dataset_temp_3, "Language")

# keep the selected language papers only:
if paper_lang_choice == 1:
    dataset_temp_4 = dataset_temp_3.drop(dataset_temp_3[dataset_temp_3["Paper_Language"] != "English"].index, inplace=False)
elif paper_lang_choice ==2:
    dataset_temp_4 = dataset_temp_3

# reset index:
final_dataset = dataset_temp_4.reset_index(drop = True)
final_dataset.index += 1

# re-arrange the columns:
rearr_col_pos(final_dataset, 'Author', 1)
rearr_col_pos(final_dataset, 'Publication_Year', 3)

# create search result dataset and insert data:
total_searched_paper = [1000]
total_scraped_paper = [len(springer_dataset)]
total_paper_after_removed_irrelevant_paper = [len(dataset_temp_1)]
total_paper_after_removed_duplicate_paper = [len(dataset_temp_2)]
total_paper_after_removed_out_of_range_year_paper = [len(dataset_temp_3)]
total_final_paper_after_removed_non_desired_lang_paper = [len(final_dataset)]

search_result_dataset = add_SearchResult_data(total_searched_paper, total_scraped_paper, total_paper_after_removed_irrelevant_paper, total_paper_after_removed_duplicate_paper, total_paper_after_removed_out_of_range_year_paper, total_final_paper_after_removed_non_desired_lang_paper)

# transpose the dataset:
search_result_dataset = search_result_dataset.transpose()

# to the final dataset, add a column as a paper_id and datasource: 
paperId = fxn(search_keyword)
final_dataset.insert(0, "Paper_id", "spr-" + paperId+ "_" + final_dataset.index.astype(str))
final_dataset.insert(3, "Publication", "Springer Link")
final_dataset.insert(11, "Data_source", "Springer")

try:
    # create the .csv file:
    final_dataset.to_csv(fr"../data/springer/dataset/springer-{paperId}.csv", sep=',', index=False, header=True) # save final dataset as a CSV file
    final_dataset.to_csv(fr"../data/dataset_mix/springer-{paperId}.csv", sep=',', index=False, header=True) # save final dataset to the common folder for all data source

    search_result_dataset.to_csv(fr"../data/springer/dataset/springer-{paperId}_search_result_info.csv", sep=',', index=False, header=True) # save search result dataset as a CSV file

    print("The scraping process has been completed successfully.")

except:
    print("The scraping was unsuccessful, please try again..!")

######################################################################################################################################################################

