import os.path
import re
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

import pandas as pd
import requests
from bs4 import BeautifulSoup

base_url = 'https://www.eurojackpot.org/en/results/'
# Example url: https://www.eurojackpot.org/en/results/28-08-2020/

# Get today's date
today = datetime.utcnow()

# Get last friday (Euro Jackpot is on every Friday)
friday = today - timedelta(days=today.weekday()) + timedelta(days=4, weeks=-1)

# Create array to hold date values
last_100_fridays = []

# Get last n number of Fridays
number_of_weeks = 1  # There's only 451 weeks of data available online

# Generate dates
for week in range(number_of_weeks):
    date = friday - timedelta(days=week * 7)
    # Url accepts one digit months and days with a starting 0
    day = date.day if len(str(date.day)) != 1 else f'0{date.day}'
    month = date.month if len(str(date.month)) != 1 else f'0{date.month}'
    last_100_fridays.append(f'{day}-{month}-{date.year}')

# Create array of urls to parse
urls = [base_url + str(week) for week in last_100_fridays]

# Define directory to save Euro Jackpot results
path_to_save = '../Data/Euro_Jackpot/'


def parse(url_to_parse):
    req = Request(url_to_parse, headers={'User-Agent': 'Mozilla/5.0'})
    content = urlopen(req).read()
    result_page = BeautifulSoup(content, features="html.parser")
    return result_page


def extract_data(soup):
    # Create arrays for the information we want to extract
    numbers_array = []
    prize_array = []
    winners_array = []
    categories_array = []

    # Find the data we need
    table = soup.find_all('td')
    number_of_winners = soup.find_all('span', attrs={'class': 'td-top'})
    categories = soup.find_all('div', attrs={'class': 'td-bottom'})
    numbers = soup.find_all('li', attrs={'class': 'lottery-ball'})

    # Extract winner numbers
    for num in numbers:
        numbers_array.append(int(num.text))

    # Extract prize values and strip away whitespace and unnecessary text
    for row in table[1::2]:
        row = re.sub('[^0-9]', '', row.text)
        prize_array.append(int(row))

    # Extract number of winners for each category and strip away whitespace and unnecessary text
    for count, row in enumerate(table[0::2]):
        winners = number_of_winners[count].text
        winners = re.sub('[^0-9]', '', winners)
        winners_array.append(int(winners))

    # Extract categories
    for row in categories:
        categories_array.append(row.text.strip())

    data_dict = {'numbers': numbers_array, 'categories': categories_array, 'prizes': prize_array,
                 'winners': winners_array, 'winners_total': sum(winners_array), 'prize_total': sum(prize_array)}

    return data_dict


# With save_file we create both txt and csv file, unless its values are explicitly defined to be False
def save_file(extracted_data, name_to_save, txt=True, csv=True):
    # This function assumes already extracted and cleaned data arrays

    if txt:
        with open(f'{path_to_save}{name_to_save}.txt', 'w+') as f:
            # Create txt file with all the data
            f.write('Numbers: ' + str(extracted_data['numbers']) + '\n')
            f.write('Categories: ' + str(extracted_data['categories']) + '\n')
            f.write('Number_of_winners: ' + str(extracted_data['winners']) + '\n')
            f.write('Prizes: ' + str(extracted_data['prizes']) + '\n')
            f.write('Winners_total: ' + str(extracted_data['winners_total']) + '\n')
            f.write('Prize_total: ' + str(extracted_data['prize_total']) + '\n')

    if csv:
        # Define columns
        data_dict = {'Prizes': extracted_data['prizes'], 'Winners': extracted_data['winners']}

        # Create dataframe
        df = pd.DataFrame(data_dict, columns=['Prizes', 'Winners'])

        # Create csv file with prize and winners columns
        df.to_csv(f'{path_to_save}{name_to_save}.csv', index=True, header=True)


# Loop through url collection
for url in urls:
    # Name files after the date the numbers were drawn
    file_name = str(url.split('/')[-1])

    # If file already exists prevent overwriting them
    if os.path.isfile(f'{path_to_save}{file_name}.txt'):
        if os.path.isfile(f'{path_to_save}{file_name}.csv'):
            print(f'Both txt and cvs file exist with name: {file_name}.')
            continue
        else:
            print(f'Txt file already exists with name: {file_name}.txt but csv wasn\'t created yet. \n'
                  'Review your configuration if you want to save csv file too. Skipping to the next file.')
    # If file with file_name doesn't exist yet, create it
    else:
        # Check status code of response from the url
        status_code = requests.get(url).status_code
        if status_code == 200:
            parsed_page = parse(url)
            data = extract_data(parsed_page)
            print('Creating new file...')
            save_file(data, file_name)
        elif status_code == 404:
            print('Page not found.')
            break
        else:
            print(f'{url} responded with status code: {status_code}')

print('Euro Jackpot data scraping has finished.')

print(urls[-1])
