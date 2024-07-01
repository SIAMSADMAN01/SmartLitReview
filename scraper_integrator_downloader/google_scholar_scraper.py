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
from habanero import Crossref
from time import sleep
import warnings
warnings.filterwarnings('ignore')


######################################################################################################################################################################

# get the user input:
def getUserInput():

    # user input => search keyword:
    search_keyword = input ("Hello.. Please enter your search keywords for the papers.\nKeywords --> ")
    split_inputs = '+'.join(search_keyword.split())


    # user input => number of the crawl papers:
    while True:
        try:
            user_input_number = int(input ("Please, enter the number of paper you want to scrape.\n\nInput --> "))
                
        except ValueError:
            print("Invalid input, please follow the example of the input and enter again correctly\n.")
            continue         
        
        else :
            break
            

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


    return search_keyword, split_inputs, user_input_number, max_year, min_year, pattern_list, paper_lang_choice


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

# user defined functions:

# function for adding data to the dataframe:
def add_Data(papertitle, abstract, title_language, author, publication_website, publication_title, year, paper_doi, cited_by, cited_by_link, versions, versions_link, link, pdf, User_id):
    
    dataframe['Paper_Title'].extend(papertitle)
    dataframe["Abstract"].extend(abstract)
    dataframe['Language'].extend(title_language)
    dataframe['Author'].extend(author)
    dataframe['Publication'].extend(publication_website)
    dataframe['Publication_Title'].extend(publication_title)
    dataframe['Publication_Year'].extend(year)
    dataframe['Paper_DOI'].extend(paper_doi)    
    dataframe['Cited_by'].extend(cited_by)
    dataframe['Cited_by_link'].extend(cited_by_link)  
    dataframe['Total_versions_of_the_paper'].extend(versions)
    dataframe['All_versions_link'].extend(versions_link)  
    dataframe['Url_of_paper'].extend(link)
    dataframe['PDF_link_of_paper'].extend(pdf)
    dataframe["Author's_GoogleScholar_userId"].extend(User_id)

    return pd.DataFrame.from_dict(dataframe, orient='index')


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


# function for get the paper doi number:
def getDoi(title):

    cr = Crossref()

    result = cr.works(query = title)
    doi_num = result['message']['items'][0]['DOI']

    return doi_num


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
    
    response=requests.get(url,headers=header)

    # check webpage response status
    if response.status_code != 200:
        print('Status code:', response.status_code)
        raise Exception('Failed to fetch the requested web page....! ')

    #parse by using beautiful soup library
    papers_info = BeautifulSoup(response.text,'html.parser')

    return papers_info


# function for extracting the information of the paper tags:
def getTags(information):
    
    title_tag = information.select('[data-lid]')
    abstract_tag = information.find_all("div", {"class": "gs_rs"})
    authors_tag = information.find_all("div", {"class": "gs_a"})
    cited_by_tag = information.find_all("div", {"class": "gs_ri"})
    version_tag = cited_by_tag
    link_tag = information.find_all('h3',{"class" : "gs_rt"})
    pdf_link_tag = information.find_all("div", {"class": "gs_r gs_or gs_scl"})

    authors_user_id_tag = information.find_all("div", {"class": "gs_a"})

    return title_tag, abstract_tag, authors_tag, cited_by_tag, version_tag, link_tag, pdf_link_tag, authors_user_id_tag


# function for process the collected tags:
def processTags(title_tag, abstract_tag, authors_tag, cited_by_tag, version_tag, link_tag, pdf_link_tag, authors_user_id_tag):

    # function for getting the title of the paper:
    def get_papertitle(title_tag):

        global nlp
        paper_title = []
        title_lang = []
        paper_doi = []
        
        for title in title_tag:  
            if title is None:
                paper_title.append(None)
                title_language.append(None)
                
            else:
                t = title.select('h3')[0].get_text()
            
                t_temp = re.sub(r"[\(\[].*?[\)\]]", "", t)
                title_temp = t_temp.lstrip()
                paper_title.append(title_temp)
            
                ##########################################################################        
                # identify title language with spacy-language_detection
                try:
                    doc = nlp(title_temp)
                    detect_language = doc._.language
                    title_lang.append(detect_language)
                    
                except:
                    title_lang.append(None)

                ##########################################################################        
                # identify title language withlangdetect
                
                #DetectorFactory.seed = 0
                
                #lang = detect_langs(title_temp)
                #title_lang.append(lang)

                ##########################################################################        
                # identify doi from title
                try:
                    doi_n = getDoi(title_temp)
                    paper_doi.append(doi_n)
                    
                except:
                    paper_doi.append(None)
                ##########################################################################  

        return paper_title, title_lang, paper_doi


    # function for getting abstract of the paper:
    def get_abstract(abstract_tag):
        
        abstracts = []
        
        for a in abstract_tag:
            if a is None:
                abstracts.append(None)
            else:
                abs = a.text
                
                if abs != None:
                    abstracts.append(abs)
                else:
                    abstracts.append(None)
                
        return abstracts


    # function for the getting authors name:
    def get_author_name(authors_tag):
        
        authors = []

        for i in range(len(authors_tag)):
            if i is None:
                authors.append(None)
                
            else:
                authortag_text = (authors_tag[i].text).split('-')
            
                Author = authortag_text[0]
                authors.append(Author)
        
        return authors  


    # function for the getting author , year and publication information:
    def get_publication_year(authors_tag):
    
        publication = []
        publication_title = []
        years = []

        for i in range(len(authors_tag)):

            # publication:
            publication_info_temp = re.split(r" [-]", authors_tag[i].text)[-1]
            
            if publication_info_temp is None:
                publication.append(None)
            
            else:
                publication_info = publication_info_temp.replace('-' , '')
                publication_info = publication_info.strip()
                publication.append(publication_info)  
            
            # publication_title:
            publication_title_temp =re.search(r"-\s([^;]*),", authors_tag[i].text)
                    
            if publication_title_temp is None:
                publication_title.append(None)
                
            else:
                temp = publication_title_temp.group()
                
                publication_title_info = temp.replace('-' , '')
                
                # Substring that need to be replaced:
                strToReplace   = ","
                replacementStr = ""
                # Replace last occurrences of substring "," in string with "" :
                publication_title_info = replacementStr.join(publication_title_info.rsplit(strToReplace, 1))
                publication_title_info = publication_title_info.strip()
                publication_title.append(publication_title_info)

            # publication_year:  
            Year_temp = re.search(r"(,\s(?:18|19|20|21)[0-9]{2}\s-)", authors_tag[i].text)
            
            if Year_temp is None:
                years.append(0)
            
            else :
                temp = Year_temp.group()
                
                char_to_replace = {',': '', '-': ''}
                year = temp.translate(str.maketrans(char_to_replace))
                year = int(year.strip())
                years.append(year)
                                            
        return publication, publication_title, years


    # function for getting the citation of the paper:
    def get_cited_by(cite_tag):
        
        cite_count = []

        for i in cite_tag:
            cite = i.text
            temp_cite = re.search(r'Cited by \d+', cite) 
            
            if temp_cite is None :
                cite_count.append(0)   # if paper has no citatation then consider 0
            else :
                temp = temp_cite.group()
                temp = temp.replace("Cited by", "")
                temp = int(temp.strip())
                cite_count.append (temp)
            
        return cite_count


    # function for getting link for the different versions of the paper :
    def get_cited_by_link(cited_by_tag):
        
        all_cited_by = []

        for i in cited_by_tag :
            temp_list = []
        
            cited_by_temp = i.find_all('a', href=True)

            for j in cited_by_temp :
            
                c_l = re.search(r'Cited by \d+', j.text)
            
                if c_l != None:
                    all_c = j.get('href')
                    temp_list.append(all_c)
                    
                else:
                    temp_list.append(None)

            if temp_list.count(None) == len(temp_list):
                all_cited_by.append(None)
                        
            else:
                for i in temp_list:
                    if i != None:
                        all_cited_by.append("https://scholar.google.com"+i)            
                    
        return all_cited_by


    # function for getting total versions of the paper:
    def get_number_of_versions(version_tag):
        
        version_count = []

        for i in version_tag:
            version = i.text
            temp = re.search(r'All \d+ versions', version) 
            if temp is None :
                version_count.append(0)   # if paper has no citatation then consider None
            else :
                temp_version = temp.group()
                temp_version = temp_version.replace("All", "").replace("versions", "")
                temp_version = int(temp_version.strip())
                version_count.append (temp_version)

        return version_count


    # function for getting link for the different versions of the paper :
    def get_all_versions_link(version_tag):
        
        all_versions = []

        for i in version_tag :
            temp_list = []
        
            versions_temp = i.find_all('a', href=True)

            for j in versions_temp :
                v_l = re.search(r'All \d+ versions', j.text)
            
                if v_l != None:
                    all_v = j.get('href')
                    temp_list.append(all_v)
                    
                else:
                    temp_list.append(None)

            if temp_list.count(None) == len(temp_list):
                all_versions.append(None)
                        
            else:
                for i in temp_list:
                    if i != None:
                        all_versions.append("https://scholar.google.com"+i)            
                    
        return all_versions


    # function for the getting link information:
    def get_link(link_tag):

        paper_link = []

        for i in range(len(link_tag)) :
            try: 
                paper_link_temp = (link_tag[i].a['href'])   
                paper_link.append(paper_link_temp) 
            except:
                paper_link.append(None)
                
        return paper_link


    # function for the getting link information:
    def get_pdf_link(pdf_link_tag):

        pdf_link = []

        for i in pdf_link_tag :
    
            temp_list = []
            
            pdf_link_temp = i.find_all('a', href=True)

            for j in pdf_link_temp :
                p_l = re.search(r'(?:\[PDF\]|\[HTML\])', j.text)
            
                if p_l != None:
                    PDF_link = j.get('href')
                    temp_list.append(PDF_link)
                    
                else:
                    temp_list.append(None)

            if temp_list.count(None) == len(temp_list):
                pdf_link.append(None)
                        
            else:
                for i in temp_list:
                    if i != None:
                        pdf_link.append(i)         

        return pdf_link


    # function for the getting author user link information
    def get_author_user_id(authors_user_id_tag):

        user_id = []

        for i in authors_user_id_tag :
            
            if i is None:
                user_id.append(None)
        
            else:
                users_string = (str(i))
            
                users = re.findall(r'(user=[- _]?[a-z A-z 0-9]+[- _]?[a-z A-z 0-9]+&)', users_string)  
                user_id.append(users)

        return user_id
    

    # paper title from each page
    papertitle, title_language, paper_doi = get_papertitle(title_tag)
    
    # abstract of the paper:
    abstract = get_abstract(abstract_tag)

    # authors of the paper
    author = get_author_name(authors_tag)

    # publication, year of the paper
    publication_website, publication_title, year = get_publication_year(authors_tag)

    # cited by this paper 
    cited_by = get_cited_by(cited_by_tag)
    
    # papers are cited by this paper
    cited_by_link = get_cited_by_link(cited_by_tag)
    
    # All versions of the paper
    versions = get_number_of_versions(version_tag)
    
    # All versions of the paper
    versions_link = get_all_versions_link(version_tag)

    # url of the paper
    link = get_link(link_tag)

    # pdf link of the paper
    pdf= get_pdf_link(pdf_link_tag)

    # author user id link
    User_id = get_author_user_id(authors_user_id_tag)

    return papertitle, abstract, title_language, paper_doi, author, publication_website, publication_title, year, paper_doi, cited_by, cited_by_link, versions, versions_link, link, pdf, User_id


######################################################################################################################################################################

# define empty dictionary:
dataframe = {
            "Paper_Title" : [],
            "Abstract" : [],
            "Language" : [],
            "Author" : [],
            "Publication" : [],
            "Publication_Title" : [],
            "Publication_Year" : [],
            "Paper_DOI" : [],
            "Cited_by" : [],
            "Cited_by_link" : [],
            "Total_versions_of_the_paper" : [],
            "All_versions_link" : [],
            "Url_of_paper" : [],
            "PDF_link_of_paper" : [],
            "Author's_GoogleScholar_userId" : []
            }

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
search_keyword, split_inputs, user_input_number, max_year, min_year, pattern_list, paper_lang_choice = getUserInput()

x = range(0,user_input_number,10)

for i in x:
    
  if i ==110 or i ==210 or i ==310 or i ==410 or i ==510 or i ==610 or i ==710 or i ==810 or i ==910:
    # use sleep to avoid status code 429
    sleep(600)
    
    # get url for the each page:
    url = f"https://scholar.google.com/scholar?start={i}&q={split_inputs}&hl=en&as_sdt=0,5&as_ylo={min_year}&as_yhi={max_year}"

    # get data of each page:
    information = get_webpage_data(url)

    # collecting the tags:
    title_tag, abstract_tag, authors_tag, cited_by_tag, version_tag, link_tag, pdf_link_tag, authors_user_id_tag = getTags(information)

    # process the tags:
    papertitle, abstract, title_language, paper_doi, author, publication_website, publication_title, year, paper_doi, cited_by, cited_by_link, versions, versions_link, link, pdf, User_id = processTags(title_tag, abstract_tag, authors_tag, cited_by_tag, version_tag, link_tag, pdf_link_tag, authors_user_id_tag)

    # create dataset and insert data
    dataset= add_Data(papertitle, abstract, title_language, author, publication_website, publication_title, year, paper_doi, cited_by, cited_by_link, versions, versions_link, link, pdf, User_id)

    # use sleep to avoid status code 429
    sleep(120)

  else:
    # get url for the each page:
    url = f"https://scholar.google.com/scholar?start={i}&q={split_inputs}&hl=en&as_sdt=0,5&as_ylo={min_year}&as_yhi={max_year}"

    # get data of each page:
    information = get_webpage_data(url)

    # collecting the tags:
    title_tag, abstract_tag, authors_tag, cited_by_tag, version_tag, link_tag, pdf_link_tag, authors_user_id_tag = getTags(information)

    # process the tags:
    papertitle, abstract, title_language, paper_doi, author, publication_website, publication_title, year, paper_doi, cited_by, cited_by_link, versions, versions_link, link, pdf, User_id = processTags(title_tag, abstract_tag, authors_tag, cited_by_tag, version_tag, link_tag, pdf_link_tag, authors_user_id_tag)

    # create dataset and insert data:
    dataset= add_Data(papertitle, abstract, title_language, author, publication_website, publication_title, year, paper_doi, cited_by, cited_by_link, versions, versions_link, link, pdf, User_id)

    # use sleep to avoid status code 429
    sleep(120)

# transpose the dataset:
data_set = dataset.transpose()

dataset_temp_1 = data_set

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

# create search result dataset and insert data:
total_searched_paper = [user_input_number]
total_scraped_paper = [len(data_set)]
total_paper_after_removed_irrelevant_paper = [len(dataset_temp_1)]
total_paper_after_removed_duplicate_paper = [len(dataset_temp_2)]
total_paper_after_removed_out_of_range_year_paper = [len(dataset_temp_3)]
total_final_paper_after_removed_non_desired_lang_paper = [len(final_dataset)]

search_result_dataset = add_SearchResult_data(total_searched_paper, total_scraped_paper, total_paper_after_removed_irrelevant_paper, total_paper_after_removed_duplicate_paper, total_paper_after_removed_out_of_range_year_paper, total_final_paper_after_removed_non_desired_lang_paper)

# transpose the dataset:
search_result_dataset = search_result_dataset.transpose()

# to the final dataset, add a column as a paper_id and datasource: 
paperId = fxn(search_keyword)
final_dataset.insert(0, "Paper_id", "g.s-" + paperId+ "_" + final_dataset.index.astype(str))
final_dataset.insert( 17, "Data_source", "Google Scholar" )


try:
    # create the .csv file:
    final_dataset.to_csv(fr"../data/google_scholar/dataset/google_scholar-{paperId}.csv", sep=',', index=False, header=True) # save final dataset as a CSV file
    final_dataset.to_csv(fr"../data/dataset_mix/google_scholar-{paperId}.csv", sep=',', index=False, header=True) # save final dataset to the common folder for all data source

    search_result_dataset.to_csv(fr"../data/google_scholar/dataset/google_scholar-{paperId}_search_result_info.csv", sep=',', index=False, header=True) # save search result dataset as a CSV file

    print("The scraping process has been completed successfully.")

except:
    print("The scraping was unsuccessful, please try again..!")
######################################################################################################################################################################