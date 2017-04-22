# -*- coding: utf-8 -*-

import requests
import config


ya_maps_api_key = '&key=' + config.yamaps_key

ya_maps_base_url = 'https://geocode-maps.yandex.ru/1.x/?geocode='
ya_maps_options = '&sco=latlong&format=json&kind=house'


def get_location_address(latitude, longitude):
    url = ya_maps_base_url + str(latitude) + ',' + str(longitude) + ya_maps_options + ya_maps_api_key
    response = requests.get(url)
    if response.status_code == 200:
        address = \
            response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                'GeocoderMetaData']['text']
        print(address)
        return address
    else:
        return u'Адрес не найден'
