# import neccessary libraries:

from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import numpy as np
import random
import math
import seaborn as sb
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import colors
import os
from os import listdir
from os.path import isfile, join
from pypdf import PdfReader
import spacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector
from iso639 import languages
import glob
import difflib
from difflib import SequenceMatcher
from time import sleep
import warnings
warnings.filterwarnings('ignore')


#################################################################################################################################

# get the user input:
def getUserInput():

    # user input => regex pattern for title match:
    title_match_regex_pattern = input ("For the regex pattern match, enter the keyword group number as 'a', 'b', 'c',  etc... to match the title and abstract of the relevant paper.\n\nExample: If you want to match two diffrent group of keywords then input as: a,b\n\nGroup: ")
    title_match_regex_pattern = list(title_match_regex_pattern)

    pattern_list = []
    for n in title_match_regex_pattern:
        x = re.search(r",|\s", n)
        if x == None:
            
            pattern_list.append(input (f"To only keep the relevant papers from the crawled papers, please enter specific keywords for the regex pattern match.\nExample:keyword_x|KEYWORD_x|keyword_x|KEYWORD_x|Keyword_x\n\nKeywords group {n}: --> "))

    
    # user input => year range for the crawl papers:
    print("To keep papers from a specific publication year range, please specify the maximum and minimum range of years. Example input: 2015, 2021, 2024\n")

    while True:
        try:
            max_year = int(input("Maximum year:"))
            min_year = int(input("\nMinimum year:"))
                
        except ValueError:
            print("\n\nInvalid input, please follow the example of the input and enter again correctly.\n")
            continue         
        
        else :
            break


    # user input => which paper's language to keep:
    paper_lang_choice = int(input("Hello.. Please enter 1 for keeping the 'English' papers only.\n# Enter 2 for keeping 'All-Language papers'\n--> "))

    if paper_lang_choice == 1:
        keep_paper_lang = "English"
    elif paper_lang_choice == 2:
        keep_paper_lang = "All-Language"
    else:
        print("\n\nInvalid input, please follow the example of the input and enter again correctly.")


    # user input => page range for applying the page filter:
    print("Below specify the range of pages you would like to keep the papers. Example input: 2, 5, 50, 60, 100\n")

    while True:
        try:
            max_pages = int(input("Maximum pages:"))
            min_pages = int(input("\nMinimum pages:"))
                
        except ValueError:
            print("\n\nInvalid input, please follow the example of the input and enter again correctly.\n")
            continue         
        
        else :
            break

    return pattern_list, max_year, min_year, paper_lang_choice, max_pages, min_pages


#################################################################################################################################################################

# define spacy language detector pipeline:
def get_lang_detector(nlp, name):
    return LanguageDetector()
nlp = spacy.load("en_core_web_sm")
Language.factory("language_detector", func=get_lang_detector)
nlp.add_pipe('language_detector', last=True)


#################################################################################################################################################################

# function for re-arrange the columns:
def rearr_col_pos(dataframe,col_name, col_new_pos):
    col = dataframe.pop(col_name)
    dataframe.insert(col_new_pos, col.name, col)


#################################################################################################################################################################

# functions for download the papers(pdf):
def paperDownlaoder(paperid_downloadlink):

    # Headers to access the google scholar website:
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
    
    global pdf_save_dir
    output_dir = pdf_save_dir
    paper_id = paperid_downloadlink[0]
    pdf_url = paperid_downloadlink[1]

    # check for 'none' values in pdf download link:

    if pdf_url != None:

    # try to download the papers(pdf) directly:
        
        try:
            pdf = re.search(r'(pdf)+|(download)+', pdf_url)
    
            if pdf != None:
                response = requests.get(pdf_url, headers=header, verify=False)
    
                if response.status_code == 200:
    
                    file_path = os.path.join(output_dir, str(f"{paper_id}") + str(".pdf"))
                    with open(file_path, 'wb') as f:
                        f.write(response.content)

        except:
            print(f"\n{paper_id} link has error..!")
            

        # try to get the pdf link for the paper from the html link and download the paper:
        else:

            # get the url from requests get method

            try:
        
                html_url_1 = re.search(r'(?:[^\/]*\/){3}', pdf_url)
                html_url_2 = html_url_1.group()
                html_url = re.sub(".$", "", html_url_2)
        
                read = requests.get(pdf_url, headers=header, verify=False)
        

                # Parse the html content
                information = BeautifulSoup(read.text, "html.parser")
    

                # accessed all the anchors tag
                a_href = information.find_all('a', href=True)

                # iterate through a_herf for getting all the href links
                for link in a_href:
                    pdf_link = re.search(r'(PDF)+', link.text)
        
                    if pdf_link != None:


                        new_url = html_url + str(link.get('href'))
                        check = re.search(r"https:\/\/[a-z A-Z 0-9 .-_=]*https:\/\/", new_url)
                
                        if check != None :
                            new_url_1 = re.sub(r"https:\/\/[a-z A-Z 0-9 .-_=]*https:\/\/", "https://",new_url)

                            response_1 = requests.get(new_url_1, headers=header, verify=False)
    
                            file_path = os.path.join(output_dir, str(f"{paper_id}") + str(".pdf"))
                            with open(file_path, 'wb') as f:
                                f.write(response_1.content)        
                    
                        else:
                            response_2 = requests.get(new_url, headers=header, verify=False)
    
                            if response_2.status_code == 200:
    
                                file_path = os.path.join(output_dir, str(f"{paper_id}") + str(".pdf"))
                                with open(file_path, 'wb') as f:
                                    f.write(response_2.content)
    
            # final try to get the papers(pdf) if previous steps fail:
            except:
        
                try:  
                    response = requests.get(pdf_url, headers=header, verify=False)
    
                    if response.status_code == 200:
    
                        file_path = os.path.join(output_dir, str(f"{paper_id}") + str(".pdf"))
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                except:
                    print(f"\n{paper_id} link has error..!")



#######################################################################################################################################################################

# function for get the total pages of the pdf and pdf language:
def get_totalPagePdfLang(paper_id_title):
    
    global nlp
    global pdf_save_dir
    output_dir = pdf_save_dir
    paper_id = paper_id_title[0]
    paper_title = paper_id_title[1]

    files_dir = f"{output_dir}/{paper_id}.pdf"
    
    def getOnlylang(value):
        value = str(value)
        x = re.search(r"(.*?:){1}(.*?)\,", value)
        x = x.group(2)
    
        x = x.replace("'", "")
        x = x.strip()
    
        if x != None:
            return x
        else:
            return None   

    try:
        with open(files_dir, 'rb') as file:
                readpdf = PdfReader(file)
                totalpages = len(readpdf.pages)
                first_page = readpdf.pages[0]
                text = first_page.extract_text()
                doc = nlp(text)
                detect_language = doc._.language
                detect_lang = getOnlylang(detect_language)
                detect_full_lang = languages.get(alpha2=detect_lang).name

                return pd.Series((totalpages, detect_full_lang))

    except:
        return pd.Series((None, None))


#######################################################################################################################################################################

# function for match the paper and pdf title:
def titleMatch(paperid_papertitle):

    global pdf_save_dir
    output_dir = pdf_save_dir
    paper_id = paperid_papertitle[0]
    paper_title = paperid_papertitle[1]

    files_dir = f"{output_dir}/{paper_id}.pdf"

    def get_match_percentage(string1, string2):
            matcher = SequenceMatcher(None, string1, string2)
            return matcher.ratio()*100

    try:
        with open(files_dir, 'rb') as file:
            readpdf = PdfReader(file)
            meta = readpdf.metadata
            pdf_title = meta.title

            if pdf_title == None:
                return ("title_unreadable")

            else:
                match_percentage = get_match_percentage(paper_title.lower(), pdf_title.lower())
                if match_percentage >= 90:
                    return ("title_matched")
                else:
                    return ("title_not_matched")
    except:
         return "pdf_not_downloaded or pdf_is_broken"
    
    
########################################################################################################################################################################

# function for delete non-english pdf:
def delPDF_lang (paperid_pdflang):

    global pdf_save_dir
    global paper_lang_choice
    output_dir = pdf_save_dir
    paper_id = paperid_pdflang[0]
    pdf_lang = paperid_pdflang[1]

    # keep English language papers only:
    if pdf_lang != "English" and pdf_lang != None:
        file_path = fr"{output_dir}/{paper_id}.pdf"

        # Try to delete the file:
        try:
            os.remove(file_path)
        except:
            pass


########################################################################################################################################################################

# function for delete non-english pdf:
def delPDF_page (paperid_pdfpage):

    global pdf_save_dir
    global max_pages
    global min_pages
    output_dir = pdf_save_dir
    paper_id = paperid_pdfpage[0]
    page_number = paperid_pdfpage[1]

    if page_number < min_pages or page_number > max_pages :
           
        file_name = f"{output_dir}/{paper_id}.pdf"

        # Try to delete the file #
        try:
            os.remove(file_name)
        except:
            pass

    elif page_number == None:
        # Try to delete the file #
        try:
            os.remove(file_name)
        except:
            pass

########################################################################################################################################################################

# function for adding search rersult data to the dataframe:
def add_Merged_data_info(total_paper_merged, total_paper_after_removed_irrelevant_paper, total_paper_after_removed_duplicate_paper, total_paper_after_removed_out_of_range_year_paper, total_paper_after_removed_non_desired_lang_paper, total_final_paper_after_removed_non_desired_page_range_paper):
    
    merged_df_info_dataset['total_number_of_paper_after_merged_datasets'].extend(total_paper_merged)
    merged_df_info_dataset['total_paper_after_removed_irrelevant_paper'].extend(total_paper_after_removed_irrelevant_paper)
    merged_df_info_dataset['total_paper_after_removed_duplicate_paper'].extend(total_paper_after_removed_duplicate_paper)
    merged_df_info_dataset['total_paper_after_removed_out_of_range_year_paper'].extend(total_paper_after_removed_out_of_range_year_paper)
    merged_df_info_dataset['total_paper_after_applied_language_filter'].extend(total_paper_after_removed_non_desired_lang_paper)
    merged_df_info_dataset['total_final_paper_after_applied_page_filter'].extend(total_final_paper_after_removed_non_desired_page_range_paper)
    
    return pd.DataFrame.from_dict(merged_df_info_dataset, orient='index')

########################################################################################################################################################################

# searcing info and result dataframe:
merged_df_info_dataset = {
                    "total_number_of_paper_after_merged_datasets" : [],
                    "total_paper_after_removed_irrelevant_paper" : [],
                    "total_paper_after_removed_duplicate_paper" : [],
                    "total_paper_after_removed_out_of_range_year_paper" : [],
                    "total_paper_after_applied_language_filter" : [],
                    "total_final_paper_after_applied_page_filter" : []
                }


# get user inputs:
pattern_list, max_year, min_year, paper_lang_choice, max_pages, min_pages = getUserInput()

# location path to import the Data Frame:
path = r"../data/dataset_mix/*.csv"
csv_file_list = (glob.glob(path))

all_df = []
for f in csv_file_list:
    df = pd.read_csv(f, sep=',')
    all_df.append(df)



# Merge every single dataframe into one dataframe:
dataset_merged = all_df[0]

for df_temp in all_df[1:]:
    dataset_merged = pd.merge(dataset_merged,df_temp, how='outer')


# dataset for processing: 
data_set = dataset_merged.replace({np.nan: None})

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
#dataset_temp_3 = dataset_temp_3.sort_values(by = 'Publication_Year' , ascending = False)


# reset index:
dataset_temp_3 = dataset_temp_3.reset_index(drop = True)
dataset_temp_3.index += 1


# output directory for save the pdfs:
pdf_save_dir = r"../data/downloaded_papers"

# download papers from the pdfs' links:
dataset_temp_3[['Paper_id', 'PDF_link_of_paper']].apply(paperDownlaoder, axis=1)

# get the page number and languaeg for each pdf file:
dataset_temp_3[["PDF_page_number", "PDF_Language"]] = dataset_temp_3[['Paper_id', "Paper_Title"]].apply(get_totalPagePdfLang, axis=1)

# download papers from the pdfs' links:
dataset_temp_3["PDF_title_match"] = dataset_temp_3[['Paper_id', 'Paper_Title']].apply(titleMatch, axis=1)


# keep the selected language papers only:
if paper_lang_choice == 1:
    
    dataset_temp_3[['Paper_id', 'PDF_Language']].apply(delPDF_lang, axis=1)
    dataset_temp_4 = dataset_temp_3.drop(dataset_temp_3[(dataset_temp_3["PDF_Language"].notna()) & (dataset_temp_3["PDF_Language"] != "English")].index, inplace=False)

elif paper_lang_choice ==2:
    dataset_temp_4 = dataset_temp_3


# Apply the page filter to the dataset and downloaded pdf:
dataset_temp_4[['Paper_id', 'PDF_page_number']].apply(delPDF_page, axis=1)
dataset_temp_5 = dataset_temp_4.drop(dataset_temp_4[(dataset_temp_4["PDF_page_number"].notna()) & ((dataset_temp_4["PDF_page_number"] > max_pages) | (dataset_temp_4["PDF_page_number"] < min_pages))].index, inplace=False)

# re-arrange the columns:
rearr_col_pos(dataset_temp_5, "Paper_DOI", 2)

# reset index:
final_slr_dataset = dataset_temp_5.reset_index(drop = True)
final_slr_dataset.index += 1
final_slr_dataset = final_slr_dataset.convert_dtypes()

# create search result dataset and insert data:
total_paper_merged = [len(dataset_merged)]
total_paper_after_removed_irrelevant_paper = [len(dataset_temp_1)]
total_paper_after_removed_duplicate_paper = [len(dataset_temp_2)]
total_paper_after_removed_out_of_range_year_paper = [len(dataset_temp_3)]
total_paper_after_removed_non_desired_lang_paper = [len(dataset_temp_4)]
total_final_paper_after_removed_non_desired_page_range_paper = [len(dataset_temp_5)]

merged_datasets_final_info = add_Merged_data_info(total_paper_merged, total_paper_after_removed_irrelevant_paper, total_paper_after_removed_duplicate_paper, total_paper_after_removed_out_of_range_year_paper, total_paper_after_removed_non_desired_lang_paper, total_final_paper_after_removed_non_desired_page_range_paper)

# transpose the dataset:
merged_datasets_final_info = merged_datasets_final_info.transpose()

try:
    # create the .csv file:
    final_slr_dataset.to_csv("../data/final_slr_dataset_figure/final_slr_dataset.csv", sep=',', index=False, header=True) # save as a new CSV file
    merged_datasets_final_info.to_csv("../data/final_slr_dataset_figure/merged_datasets_final_info.csv", sep=',', index=False, header=True) # save as a new CSV file


    ######################################################################################################################################################################

    # group by publications' data source :
    x_data_source = final_slr_dataset['Data_source']
    ax_data_source = sns.countplot(x=x_data_source, color="darkblue")

    # Set the y-axis ticks to integers
    plt.yticks(np.arange(0, plt.gca().get_ylim()[1]+1, 1))

    for p in ax_data_source.patches:
        ax_data_source.annotate(f'{int(p.get_height())}', 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', 
                    xytext=(0, 10), 
                    textcoords='offset points')

    ax_data_source.set_title("Papers grouped by Data Source", fontsize=14)

    figure_data_source = ax_data_source.get_figure()    
    figure_data_source.savefig("../data/final_slr_dataset_figure/Papers_grouped_by_data_source.png", dpi=900)

    print("The Integration and Downlaod process has been completed successfully.")

except:
    print("The Integration and Downlaod process were unsuccessful, please try again..!")