import os.path
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
number_of_weeks = 2

# Generate dates
for week in range(number_of_weeks):
    date = friday - timedelta(days=week * 7)
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


def save_file(parsed_page_data, name_to_save):
    with open(f'{path_to_save}{name_to_save}'.replace('.csv', '.txt'), 'w+') as f:
        data = parsed_page_data.find_all('td')
        number_of_winners = parsed_page_data.find_all('span', attrs={'class': 'td-top'})
        categories = parsed_page_data.find_all('div', attrs={'class': 'td-bottom'})
        numbers = parsed_page_data.find_all('li', attrs={'class': 'lottery-ball'})

        numbers_array = []
        prize_array = []
        winners_array = []
        categories_array = []

        for num in numbers:
            numbers_array.append(num.text)

        for row in data[1::2]:
            row = row.text.strip()
            row = row.replace('Winners', '')
            row = row.replace('Winner', '')
            row = row.replace('\n', '')
            prize_array.append(row)

        for count, row in enumerate(data[0::2]):
            winners = number_of_winners[count].text.replace('Winners', '')
            winners = winners.replace('Winner', '')
            winners = winners.strip()
            winners = winners.replace('\n', '')
            winners_array.append(winners)

        for row in categories:
            categories_array.append(row.text)

        data = {'Prize': prize_array,
                'Winners': winners_array
                }

        df = pd.DataFrame(data, columns=['Prize', 'Winners'])

        # Create csv file with prize and winners columns
        df.to_csv(f'{path_to_save}{name_to_save}', index=True, header=True)

        # Create txt file with all the data
        f.write('Numbers: ' + str(numbers_array) + '\n')
        f.write('Categories: ' + str(categories_array) + '\n')
        f.write('Number of winners: ' + str(winners_array) + '\n')
        f.write('Prize: ' + str(prize_array) + '\n')


# Loop through url collection
for url in urls:
    # Name files after the date the numbers were drawn
    file_name = str(url.split('/')[-1]) + '.csv'

    # If file already exists prevent overwriting them
    if os.path.isfile(f'{path_to_save}{file_name}'):
        print('This filename already exists.')
        continue
    # If file with file_name doesn't exist yet, create it
    else:
        # Check status code of response from the url
        status_code = requests.get(url).status_code
        if status_code == 200:
            parsed_page = parse(url)
            print('Creating new file...')
            save_file(parsed_page, file_name)
        else:
            print(f'{url} responded with status code: {status_code}')

print('Euro Jackpot data scraping has finished.')
