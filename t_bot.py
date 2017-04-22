#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import logging
import re
import mongo

import telepot
import util
import ya_disk
import config


def create_bot(bot_token):
    return telepot.Bot(bot_token)


def get_user_oauth(user_id):
    url = 'https://oauth.yandex.ru/authorize?response_type=token&client_id=' + ya_disk.app_id
    disk_bot.sendMessage(user_id, u"Пожалуйста, авторизуйте приложение для работы с ЯндексДиском " + url)


def on_chat_message(msg):
    """
    Main function. 
    :param msg: 
    :return: 
    """

    def response_status(status):
        if status == 403:
            logging.debug(u'Кажется папка пользователя удалена.\n')
            disk_bot.sendMessage(chat_id,
                                 u'К сожалению, не удалось записать файл.\n'
                                 u'Пожалуйста, проверьте, что существует папка {}'.format(
                                     path_to_app))

        elif status == 502:
            disk_bot.sendMessage(chat_id,
                                 u'К сожалению, не удалось записать файл.\n'
                                 u'Яндекс.Диск вернул внутреннюю ошибку сервера.\n'
                                 u'Пожалуйста, попробуйте еще раз.\n')
        elif status['status_code'] == 200:
            disk_bot.sendMessage(chat_id, u'Загрузка файла на диск успешна.\n'
                                          u'Если вы хотите получить публичную ссылку на файл, то выполните,'
                                          u' пожалуйста, команду /link')
            mongo.update_last_file(chat_id, collection, status['path_to_file'])

        else:
            disk_bot.sendMessage(chat_id, u'Что-то пошло нет так, попробуйте, пожалуйста, еще раз.')

    logging.debug(type(msg))
    logging.debug(msg)
    content_type, chat_type, chat_id = telepot.glance(msg)
    logging.debug("content_type: {}\nchat_type: {}\nchat_id: {}\n".format(content_type, chat_type, chat_id))
    # Get yandex OAuth token
    oauth = mongo.check_user_id(chat_id, collection)
    # Update user info, if fail - nevermind
    try:
        last_name = msg.get('chat', {}).get('last_name', '')
        first_name = msg.get('chat', {}).get('first_name', '')
        username = msg.get('chat', {}).get('username', '')
        update_user_info = mongo.update_user_info(chat_id, collection, last_name=last_name,
                                                  first_name=first_name,
                                                  username=username)
    except Exception:
        pass
    if oauth == 1:  # user exist, but don't have OAuth token.
        user_is_here = 0
    else:
        user_is_here = 1
        try:
            # if OAuth key changed.
            command, oauth_key = msg['text'].split()
            if command == '/start' and len(oauth_key) > 0:
                mongo.update_user_oauth(chat_id, oauth_key, collection)
                oauth = mongo.check_user_id(chat_id, collection)
        except Exception:
            pass
        # Check that we have permission to ya.disk folder.
        path_to_app = ya_disk.get_info(oauth)
        if path_to_app == 401:
            get_user_oauth(chat_id)
            return True

    logging.debug('Chat Message: {} {} {}'.format(content_type, chat_type, chat_id))
    for key in msg:
        logging.debug("{}: {}".format(key, msg[key]))
    logging.debug("*" * 80)

    if user_is_here:
        if 'text' in msg:
            if re.match('^/', msg['text']):
                is_bot_command_here = True  # we catch bot command.
            else:
                is_bot_command_here = False
        else:
            is_bot_command_here = False

        if is_bot_command_here:
            command = msg['text']
            if re.match('^/help', command):
                message = u'Я понимаю следующие команды:\n' \
                          u'/help - эта справка\n' \
                          u'/link - получение публичной ссылки на последний загруженный файл\n' \
                          u'/stop - удаление вашего OAuth токена из базы данных\n' \
                          u'Пожалуйста, оцените меня: https://telegram.me/storebot?start=yadisk_bot'
                disk_bot.sendMessage(chat_id, message)
            elif re.match('^/stop', command):
                if mongo.delete_user(chat_id, collection):
                    message = u'Ваш токен удален из базы данных\n' \
                              u'Хорошего дня!\n'
                    disk_bot.sendMessage(chat_id, message)
                    try:
                        disk_bot.sendMessage(12452435, u'Пользователь удалился :(\n'
                                                       '{}'.format(msg['chat']))
                    except Exception:
                        pass
                else:
                    message = u'Что-то пошло не так.\n' \
                              u'Пожалуйста, попробуйте еще раз или напишите моему создателю @azalio\n'
                    disk_bot.sendMessage(chat_id, message)
            elif re.match('^/start', command):
                disk_bot.sendMessage(chat_id,
                                     u'Все готово для работы с Яндекс Диском!\n'
                                     u'Попробуйте мне послать какой-нибудь файл или'
                                     u' просто что-нибудь написать.')
            # Sharing.
            elif re.match('^/link', command):
                try:
                    oauth, last_file = mongo.get_user_last_file(chat_id, collection)
                except Exception:
                    disk_bot.sendMessage(chat_id, u'Ошибка соединения с базой данных, попробуйте, пожалуйста, еще раз.')

                public_url = ya_disk.get_public_link_to_file(oauth, last_file)
                if public_url:
                    disk_bot.sendMessage(chat_id, u'Публичная ссылка на файл: {}'.format(public_url))
                else:
                    disk_bot.sendMessage(chat_id, u'К сожалению, не удалось сформировать публичную ссылку.')
            else:
                message = u'К сожалению, я не понял данной команды.\n'
                disk_bot.sendMessage(chat_id, message)

        else:  # not bot command.
            if content_type in text_documents:
                filepath = '/tmp/' + str(chat_id) + '_' + str(msg['date']) + '_' + str(msg['message_id']) + '.txt'
                logging.debug(filepath)

                with open(filepath, 'w') as f:
                    if 'forward_from_chat' in msg:
                        forward_info = "From {}: {}\n".format(msg['forward_from_chat']['type'],
                                                              msg['forward_from_chat']['title'])
                        f.write(forward_info)
                    if content_type == 'text':
                        f.write(msg['text'])
                    else:
                        data = []
                        for key in msg[content_type]:
                            value = msg[content_type][key]

                            if type(value) != str:
                                print("value type is: {}".format(type(value)))
                                value = str(value)
                            data.append(key + u': ' + value + u'\n')
                        logging.debug(data)
                        data = ''.join(data)
                        logging.debug(data)
                        f.write(data.encode('utf-8'))
                    if content_type == 'location':
                        address = util.get_location_address(msg['location']['latitude'], msg['location']['longitude'])
                        f.write(address.encode('utf-8'))
                    f.close()
                status = ya_disk.upload_to_ya_disk(path_to_app, filepath, content_type)
                response_status(status)

            elif content_type in file_documents:
                response = ''
                if content_type == 'photo':
                    try:
                        response = disk_bot.getFile(msg[content_type].pop()['file_id'])
                    except telepot.exception.TelegramError as ex:
                        send_message_on_error(chat_id, u'К сожалению, загрузка не удалась.\n'
                                                       u'Размер файла не должен превышать 20МB', ex)
                else:
                    try:
                        response = disk_bot.getFile(msg[content_type]['file_id'])
                    except telepot.exception.TelegramError as ex:
                        send_message_on_error(chat_id, u'К сожалению, загрузка не удалась.\n'
                                                       u'Размер файла не должен превышать 20МB', ex)
                logging.debug(response)
                if response != '':
                    url = 'https://api.telegram.org/file/bot' + token + '/' + response['file_path']
                    logging.debug(url)
                    filepath = url
                    if 'file_name' in msg[content_type]:
                        filename = msg[content_type]['file_name']
                    else:
                        filename = ''
                    status = ya_disk.upload_to_ya_disk(path_to_app, filepath, content_type, filename=filename)
                    response_status(status)

    else:  # user don't exits.
        command = ''
        logging.debug(msg)
        if 'entities' in msg:
            if 'bot_command' in msg['entities'][0].values():
                try:
                    command, text = msg['text'].split()
                    if command == '/start' and text == 'start':
                        get_user_oauth(chat_id)
                    elif command == '/start' and len(text) > 0:
                        logging.debug(text)
                        mongo.update_user_oauth(chat_id, text, collection)
                        oauth = mongo.check_user_id(chat_id, collection)
                        path_to_app = ya_disk.get_info(oauth)
                        if path_to_app == 401:
                            disk_bot.sendMessage(chat_id, u'Возникли проблемы с авторизаций на Яндекс.Диске')
                            get_user_oauth(chat_id)
                        else:
                            disk_bot.sendMessage(chat_id,
                                                 u'Все готово для работы с Яндекс Диском!\n'
                                                 u'Попробуйте мне послать какой-нибудь файл или'
                                                 u' просто что-нибудь написать.')
                            try:
                                disk_bot.sendMessage(12452435, u'Йеху! Новый пользователь!\n'
                                                               '{}'.format(msg['chat']))
                            except Exception:
                                pass
                except ValueError:
                    pass

        if command == '':
            get_user_oauth(chat_id)


def send_message_on_error(user_id, message, ex):
    disk_bot.sendMessage(user_id, message)
    logging.debug(ex)


def main(disk_bot):
    disk_bot.message_loop({'chat': on_chat_message})
    logging.info('Listening ...')

    while 1:
        time.sleep(10)


token = config.token

disk_bot = create_bot(token)

host = config.host
port = int(config.port)
db = config.db
collection = config.collection

client, db, collection = mongo.mongo_connect(host, port, db, collection)
text_documents = ['text', 'contact', 'location', 'venue']
file_documents = ['photo', 'document', 'audio', 'video', 'voice']
logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(message)s', level=logging.DEBUG,
                    filename=u'/var/log/YaDisk/t_bot.log')

if __name__ == '__main__':
    main(disk_bot)
