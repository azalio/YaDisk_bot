# -*- coding: utf-8 -*-
import logging
from os import path
from time import sleep

import requests

from t_bot import config


headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
base_url = 'https://cloud-api.yandex.net/v1'
app_name = 'Файлы из Телеграма'
app_id = config.app_id
text_documents = ['text', 'contact', 'location', 'venue']
file_documents = ['photo', 'document', 'audio', 'video', 'voice']


def create_app_dirs(oauth, path_to_app):
    headers['Authorization'] = 'OAuth ' + oauth

    url = base_url + 'disk/resources/?path=' + path_to_app
    response = requests.put(url, headers=headers)
    if response.status_code == 201:
        logging.debug("Created root dir")
    else:
        for key in response.json():
            logging.debug(key, response.json()[key])
        logging.debug("Failed to create root dir with code {}".format(response.status_code))

    dirs = ['text_documents', 'files']
    response_dict = {}
    for dir_type in dirs:
        url = base_url + 'disk/resources/?path=' + path_to_app + '/' + dir_type
        response = requests.put(url, headers=headers)
        logging.debug(url)
        logging.debug(response.status_code)
        if response.status_code == 201:
            response_dict[dir_type] = True
        else:
            for key in response.json():
                logging.debug(key, response.json()[key])
            response_dict[dir_type] = False
        if response_dict['text_documents'] and response_dict['files']:
            return True
        else:
            return response_dict


def get_info(oauth):
    url = base_url + '/disk/'
    headers['Authorization'] = 'OAuth ' + oauth
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res_dict = response.json()
        path_to_app = res_dict['system_folders']['applications'] + "/" + app_name
        return path_to_app
    else:
        return int(response.status_code)


def upload_to_ya_disk(path_to_app, filepath, content_type, **kwargs):
    """
    https://cloud-api.yandex.net/v1/disk/resources/upload ?
    path=<путь, по которому следует загрузить файл>
    [& overwrite=<признак перезаписи>]
    [& fields=<нужные ключи ответа>]

    """
    if 'filename' in kwargs:
        filename = kwargs['filename']
    else:
        filename = ''
    if content_type in text_documents:
        if filename == '':
            filename = path.basename(filepath)
        logging.debug(filename)
        if type(filename) != str:
            logging.debug("filename is not string: {}".format(filename))
            filename = str(filename)
        logging.debug("path_to_app type: {}, filename type: {}".format(path_to_app, filename))
        path_to_file = path_to_app + '/' + filename
        url = base_url + '/disk/resources/upload?path=' + path_to_file
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            url = res_json['href']
            with open(filepath, 'rb') as data:
                response = requests.put(url, data)
                if response.status_code == 201:
                    return {"status_code": 200, "path_to_file": path_to_file}
                else:
                    return False
        elif response.status_code == 403:
            logging.debug(u'Пропала папка пользователя\n')
            return 403
        elif response.status_code == 502:
            logging.debug(u'Яндекс.Диск вернул 502\n')
            return 502
    elif content_type in file_documents:
        """
        https://cloud-api.yandex.net/v1/disk/resources/upload ?
        url=<ссылка на скачиваемый файл>
        & path=<путь к папке, в которую нужно скачать файл>

        """
        if filename == '':
            filename = filepath.split('/').pop()
        logging.debug(filename)
        if type(filename) != str:
            logging.debug("filename is not string: {}".format(filename))
            filename = str(filename)
        path_to_file = path_to_app + '/' + filename
        url = base_url + '/disk/resources/upload?url=' + filepath + '&path=' + path_to_file
        logging.debug(url)
        response = requests.post(url, headers=headers)
        if response.status_code == 202:
            response = response.json()
            url = response['href']
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                logging.debug("check_file_status")
                status = check_download_status(url)
                logging.debug("download status is: {}".format(status))
                return {"status_code": 200, "path_to_file": path_to_file}
            else:
                logging.debug(response.status_code)
                logging.debug(response.json())
        elif response.status_code == 403:
            return 403
        elif response.status_code == 502:
            return 502


def check_download_status(url):
    sleep(1)
    response = requests.get(url, headers=headers)
    try:
        logging.debug(response.json())
        logging.debug(response.status_code)
    except:
        pass
    if response.status_code == 200:
        response_json = response.json()
        if response_json['status'] == 'in-progress':
            return check_download_status(url)
        elif response_json['status'] == 'success':
            return True
        elif response_json['status'] == 'failed':
            return False
        else:
            return response_json['status']
    else:
        logging.error(response.status_code)
        logging.error(response.json())


def get_public_link_to_file(oauth, last_path):
    headers['Authorization'] = 'OAuth ' + oauth
    url = base_url + '/disk/resources/publish?path=' + last_path
    response = requests.put(url, headers=headers)
    if response.status_code == 200:
        logging.debug(response.json())
    else:
        return False

    url = base_url + '/disk/resources?path=' + last_path
    meta = requests.get(url, headers=headers)
    if meta.status_code == 200:
        logging.debug(meta.json())
        return meta.json()['public_url']
    else:
        return False
