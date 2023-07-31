import camelot
import pandas as pd
import numpy as np
import os

# function that gets the name of the table
def get_name(df, page_num, type):
    if type == 'msci':
        # Getting msci table name
        contains_string = df.apply(lambda row: 'Performance' in ' '.join(row.astype(str)), axis=1)
        if contains_string.any():
            indices = contains_string[contains_string].index.to_list()
            name = df.iloc[indices[0] - 1, 1].strip()
            if not name:
                # This case means it is a one line table that formatted wrong
                raise ValueError
        else:
            input(f"Could not find name for the table on page {page_num}. What would you like to name it?")
    
    elif type == 'ftse':
        # Getting ftse table name
        name = df.iloc[0,1]
    
    elif type == 'single':
        # Getting name from a table that has one line because they format weird
        name = df.iloc[2,0]
    
    name += ".csv"
    name = name.replace(" ", "_")
    return name

# Helper method for header(), footer() and for handling small tables
def is_number(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False


# function that processes the headers of page's table
def header(df, type):
    r,c = df.shape
    new_header = []
    
    
    if type == 'msci':
        # Finding header start of msci page by finding row with 'Price as of' in it
        contains_string = df.apply(lambda row:'Price as of' in ' '.join(row.astype(str)), axis=1)
        indices = contains_string[contains_string].index.to_list()
        rows_start = indices[0] # + 1

    if type == 'ftse':
        # Finding header start of ftse page by finding row with 'Est.' in it
        contains_string = df.apply(lambda row:'Est.' in ' '.join(row.astype(str)), axis=1)
        indices = contains_string[contains_string].index.to_list()
        rows_start = indices[0]

    
    # Finding end of header by finding first row with an int value
    header_end = 0
    while header_end < r:
        row = df.iloc[header_end]
        if row.apply(is_number).any():  # Check if any value in the row is an number
            break
        header_end += 1


    # Constructing new header by iterating from start -> end rows of each column to form that columns heading
    for j in range(c):
        cell = ""
        for i in range(rows_start, header_end):
            if isinstance(df.iloc[i,j], str):
                cell = cell + df.iloc[i,j] + " "
        cell = cell.strip()
        new_header.append(cell)

    # Assigning new header, dropping old rows, reindexing
    df.columns = new_header
    df = df.iloc[header_end:]
    df.reset_index(drop=True, inplace=True)

    # Handles any conjoined columns based on header by checking for a header with '\n'
    def split_headers(df):
        df = df.copy()

        # Get headers that contain '\n'
        headers_with_newline = [col for col in df.columns if '\n' in col]

        # Iterate over each header and split into two separate columns if it contains '\n'
        for header in headers_with_newline:
            split_columns = df[header].str.split('\n', expand=True)

            # Insert the new columns to the DataFrame at the right position
            parts = header.split('\n')
            df.insert(loc=df.columns.get_loc(header), column=parts[0], value=split_columns[0])
            df.insert(loc=df.columns.get_loc(header) + 1, column=parts[1], value=split_columns[1])

            # Delete the original column
            df = df.drop(columns=[header])
        
        return df
    # If split_headers breaks it likely means that the table is a single line so it got formatted wrong, this will be caught
    # in the section where it tries to join the dataframes, that way we know it for sure.
    try:    
        return split_headers(df)
    except:
        raise ValueError
    
# function that processes the bottom (footer) of both msci and ftse pages
def footer(df):
    r,c = df.shape
    
    bottom = r
    for i in range(r - 1, -1, -1):
        row = df.iloc[i]
        if row.apply(is_number).any(): # if the row contains any number
            bottom = i + 1 # next row after the row with number
            break
            
    df = df.iloc[:bottom]
    return df

# function that drops empty rows of df, this handles '(below)' rows
def drop_empty_rows(df):   
    for index,row in df.iterrows():
        if row.apply(is_number).any() == False:
            df.drop(index, inplace=True)
    return df

# list of valid MSCI EM/DM Countries
countries = ["Canada", "USA", "Austria", "Belgium", "Denmark", "Finland", "France", 
             "Germany", "Ireland", "Israel", "Italy", "Netherlands", "Norway", 
             "Portugal", "Spain", "Sweden", "Switzerland", "UK", "Australia", 
             "Hong Kong", "Japan", "New Zealand", "Singapore", "Brazil", "Chile", 
             "Colombia", "Mexico", "Peru", "Czech Republic", "Egypt", "Greece", 
             "Hungary", "Kuwait", "Poland", "Qatar", "Saudi Arabia", "South Africa", 
             "Turkey", "UAE", "China", "India", "Indonesia", "Korea", "Malaysia", 
             "Philippines", "Taiwan", "Thailand"]

# fixes the countries that didn't format correctly
def fix_country(df):
    if 'Country' in df.columns:
        nan_rows = df['Country'].isna()
        missing_countries = nan_rows[nan_rows].index.tolist()
        
        for i in missing_countries:
            for country in countries:
                if country in df['Name'][i]:
                    df['Name'][i] = df['Name'][i].replace(country, '')
                    df['Country'][i] = country
    return df


def merge_columns_with_blank_headers(df):
    df_new = df.copy()
    i = 0
    cols_to_drop = []
    
    # helper to check if a value is empty or a string of whitespace
    def is_empty_or_whitespace(x):
        return pd.isnull(x) or str(x).strip() == ''

    while i < df_new.shape[1] - 1:
        if df_new.iloc[:, i].apply(is_empty_or_whitespace).all() and not is_empty_or_whitespace(df_new.columns[i]):
            if is_empty_or_whitespace(df_new.columns[i + 1]):
                df_new.columns.values[i] = df_new.columns.values[i] + df_new.columns.values[i + 1]
                df_new.iloc[:, i] = df_new.iloc[:, i].fillna('') + df_new.iloc[:, i + 1].fillna('')
                cols_to_drop.append(df_new.columns[i + 1])
        i += 1

    df_new.drop(columns=cols_to_drop, inplace=True)
    return df_new


def handle_overflow(main_df, df):
    r,c = df.shape
    for i in range(r - 1, -1, -1):
        new_row = []
        for j in range(c):
            string = df.iloc[i,j]
            split = string.split('\n')
            for cell in split:
                new_row.append(cell)
        new_row_series = pd.Series(new_row)
        if new_row_series.apply(is_number).any(): # if the row contains any number
            column_names = main_df.columns.tolist()
            s = pd.Series(new_row, name='row_name', index=column_names)
            s_df = s.to_frame().T
            main_df = pd.concat([main_df, s_df], ignore_index=True)
    return main_df


def china_ticker_fix(df):
    df['Ticker'] = df['Ticker'].apply(lambda x: x[:x.find('CH')+2])
    return df

# Actual Scrape function that outputs a csv the table on the page
def scrape_page(path, page_num, output_path):
    tables = camelot.read_pdf(path, 
                              flavor='stream', 
                              pages=f'{page_num}')
    
    # Finding file type
    if 'msci' in path.lower():
        type = 'msci'
    elif 'ftse' in path.lower():
        type = 'ftse'
        
        
    # Processing dataframe using helper methods
    df = tables[0].df
    try:
        name = get_name(df, page_num, type)
        df = header(df, type)
        df = footer(df)
        df = drop_empty_rows(df)
        df = fix_country(df)
        df = merge_columns_with_blank_headers(df)
    except ValueError:
        # Handling a one line table that was formatted incorrectly
        df = tables[0].df
        new_name = get_name(df, page_num, 'single')
        output = os.path.join(output_path, new_name)
        main_df = pd.read_csv(output, index_col=0)
        df = handle_overflow(main_df, df)
        os.remove(output)
        name = new_name


    # Outputting to a csv in the respective directory in proc_tables
    output = os.path.join(output_path, name)
    if os.path.exists(output):
        main_df = pd.read_csv(output, index_col=0)
        df = pd.concat([main_df,df], ignore_index=True)

    if 'china' in output.lower():
        df = china_ticker_fix(df)

    df.to_csv(output)
    print(f"Done with page {page_num} in {output_path}")



# Helper function that calls scrape_page for each page
def scrape(path, output_path):
    start_page = int(input(f"\nPlease enter the first page you would like to scrape of {path} (Only works on security-level flows)\n"))
    end_page = int(input(f"\nPlease enter the last page you would like to scrape of {path} (Only works on security-level flows)\n"))
    if end_page < start_page:
        raise ValueError("The start page must come before the end page")
    
    while start_page <= end_page:
        scrape_page(path, start_page, output_path)
        start_page += 1



# Iterating through each pdf in '\pdfs' directory 
 
# Finding paths and checking if files are of proper type (msci or ftse)
directory = 'pdfs'
files = []

for filename in os.listdir(directory):
    if 'msci' in filename.lower():
        files.append(filename)
    elif 'ftse' in filename.lower():
        files.append(filename)
    else:
        raise ValueError('Invalid Filename, each file must be identified with "msci" or "ftse"')
  
for file in files:
    
    # Making output directory for each pdf to read and store the tables in individual csv's
    path = os.path.join(directory, file)
    output_path = r"C:\Users\vkarthik\Documents\vscode\pdf_scraper\proc_tables" + f"\{file.strip('.pdf')}_tables"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    scrape(path, output_path)


