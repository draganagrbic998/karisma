import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

from utils.email import send_email

COUNTRIES_SHEET = 'Countries'
HOTELS_SHEET = 'Hotels'
COUNTRY_COLUMN = 'Source Country'
COUNTRY_URL_COLUMN = 'URL'
HOTEL_COLUMNS = ['Destination', 'Hotel', 'Travel Lag (Days)', 'Stay (Nights)', 'Occupancy']
REQUEST_URL = 'https://reservations.karismahotels.com/?theme={}&destinationFilter={}&productCode={}&txtHotelPref={}&tbCheckInHotelReq={}&tbCheckOutHotelReq={}&searchMask={}'

THEME_MAPPING = {
    'www.karismahotels.com': 'KARISMA',
    'www.karismahotels.com/es': 'KARISMA-ES',
    'www.karismaadriatic.com': 'KARISMA',
}

PRODUCT_CODE_MAPPING = {
    'mexico': 'ALL-KAR',
    'dominican republic': 'ALL-KAR',
    'jamaica': 'ALL-KAR',
    'montenegro': 'ME-KARADR',
}

HOTEL_CODES = {
    'margaritaville island reserve cap cana': 'DO-PUJMVCC',
    'margaritaville island reserve riviera cancún': 'MX-CUNMVRC',
    'st. somewhere by karisma punta coco, holbox island': 'MX-CUNSSH',
    'margaritaville st. somewhere by karisma punta coco, holbox island': 'MX-CUNSSH',
    'nickelodeon hotels & resorts punta cana': 'DO-PUJNPC',
    'azul beach resort riviera cancun': 'MX-CUNAZS',
    'azul villa casa del mar': 'MX-CUNAZCM',
    'azul villa esmeralda': 'MX-CUNAZVE',
    'azul beach resort negril': 'JM-NEGAZS',
    'nickelodeon hotels & resorts riviera maya': 'MX-CUNNRM',
    'el dorado royale': 'MX-CUNEDR',
    'el dorado casitas royale': 'MX-CUNEDC',
    'el dorado maroma': 'MX-CUNEDM',
    'el dorado seaside suites': 'MX-CUNEDS',
    'el dorado seaside palms': 'MX-CUNEDP',
    'palafitos - overwater bungalows': 'MX-CUNPAL',
    'el dorado villa maroma': 'MX-CUNVM',
    'generations riviera maya': 'MX-CUNGRM',
    'hidden beach au naturel resort': 'MX-CUNHBR',
    'azul beach resort punta cana': 'DO-PUJSPC',
    'azul beach resort cap cana': 'DO-PUJAZCC',
    'azul beach resort montenegro': 'MNE-TGDABH',
}


def get_search_mask(occupancy):
    search_mask = ''

    for item in occupancy.split('+'):
        number = int(item.replace('AD', '').replace('CH', '').replace('JR', ''))
        for i in range(number):
            if 'AD' in item:
                search_mask += 'A'
            elif 'CH' in item:
                search_mask += 'C7'

    return search_mask


def scrap_room(room_dom, occupancy):
    category = room_dom.find('h2').text.strip()
    try:
        pax = room_dom.find('p').find('span').previous_sibling.text.strip()
    except:
        pax = occupancy
    try:
        rate = '{:.2f}'.format(float(room_dom.select_one('.khr-booking-price').text.split()[0].strip()))
    except:
        rate = None
    return [category, pax, 'yes' if rate else 'no', rate]


def load_input(input_file):
    input_data = []
    countries_sheet = pd.read_excel(input_file, sheet_name=COUNTRIES_SHEET)
    hotels_sheet = pd.read_excel(input_file, sheet_name=HOTELS_SHEET)

    countries = list(countries_sheet[COUNTRY_COLUMN])
    for country in countries:
        country_url = list(countries_sheet[COUNTRY_URL_COLUMN][countries_sheet[COUNTRY_COLUMN] == country])[0]
        for index, row in hotels_sheet[hotels_sheet[country] == country][HOTEL_COLUMNS].iterrows():
            input_data.append([country, country_url] + list(row))

    return input_data


def process_input(input_data):
    output_data = []
    rooms_cash = {}
    # country, country url, destination, hotel, travel lag, stay, occupancy

    for row in input_data:
        theme = THEME_MAPPING[row[1].lower().strip()]
        destination = row[2]
        product_code = PRODUCT_CODE_MAPPING[row[2].lower().strip()]
        hotel_code = HOTEL_CODES[row[3].lower().strip()]
        count_in = datetime.datetime.today() + datetime.timedelta(days=int(row[4]))
        count_out = count_in + datetime.timedelta(days=int(row[5]))
        search_mask = get_search_mask(row[6])
        url = REQUEST_URL.format(theme, destination.replace(' ', '%20'), product_code, hotel_code, count_in.strftime('%Y-%m-%d'), count_out.strftime('%Y-%m-%d'), search_mask)
        print(url)

        if url not in rooms_cash:
            rooms_cash[url] = []
            response = requests.get(url)
            html = response.text
            html_dom = BeautifulSoup(html, 'html.parser')
            rooms_dom = html_dom.select('.khr-booking-property')
            for room_dom in rooms_dom:
                rooms_cash[url].append(scrap_room(room_dom, row[6]))

        for room in rooms_cash[url]:
            output_data.append(row + [count_in.strftime('%m/%d/%Y'), count_out.strftime('%m/%d/%Y')] + room + [url])

    return output_data


def store_output(output_file, output_data, email_result=False):
    # country, country url, destination, hotel, travel lag, stay, occupancy, count_in, count_out, room category, pax, available, rate, ref url
    countries = {}
    columns_index = [2, 3, 7, 8, 9, 10, 11, 12, 13]

    for row in output_data:
        if row[0] not in countries:
            countries[row[0]] = []
        countries[row[0]].append([row[i] for i in columns_index])

    with pd.ExcelWriter(output_file) as writer:
        for country in countries:
            data = pd.DataFrame(countries[country], columns=['Destination', 'Hotel', 'Count In', 'Count Out', 'Room', 'Pax', 'Available', 'Rate (USD)', 'Ref URL'])
            data.to_excel(writer, sheet_name=country, index=False)

    if email_result:
        send_email('Karisma Web Check', output_file)


def main():
    input_data = load_input('input.xlsx')
    output_data = process_input(input_data)
    store_output('output.xlsx', output_data, True)


main()

