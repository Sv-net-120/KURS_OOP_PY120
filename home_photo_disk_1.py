from pprint import pprint

import requests
import json

from tqdm import tqdm
from api_vk import TOKEN
import configparser

# из информационного файла загружаем токет и код авторизации

congig = configparser.ConfigParser()
congig.read('set_clientvk.ini')

TOKEN = congig['Tokens']['id_client']
auto = congig['Other']['auto_ydisk']

photo_all_size = {}
photos_max_size ={}
photos_max_size_info = []

# создаем класс клиента и скачиваем фото из его профиля
class VKClient:

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        self.url = 'https://api.vk.com/method/'

    def get_common_params(self):
        return {
            'access_token': self.token,
            'v': '5.131'
        }
    def get_profile_photos(self):
        params = self.get_common_params()
        params.update({'owner_id': self.user_id,'album_id': 'profile', 'extended': 1})
        try:
            response = requests.get(f'{self.url}/photos.get', params=params)
        except VKAPIError:
            print(f'Возникла ошибка')
        else:
            return response.json()

    # выбираем самые большие фотографии и формируем информационный словарь

    def choose_fotos_max_size(self):

        for fotos in photo_all_size['response']['items']:
            key = f' {fotos['likes']['count']}_{fotos['id']}.jpg'
            for foto in fotos['sizes']:
                if foto['type'] == 'w':
                    photos_max_size[key] = [foto['url'], foto['type']]

        for k, v in photos_max_size.items():
            photo_info_dict = {}
            photo_info_dict['filename'] = k
            photo_info_dict['size'] = v[1]
            photos_max_size_info.append(photo_info_dict)

        with open('photos.json', 'w') as f:
            json.dump(photos_max_size_info, f)

        return photos_max_size

#  создаем на яндекс диске папку для выбранных фотографий,
#  проверяем на наличие папки с тем же именем
#  если папка существует пишем предупреждение
#  и при получении подтверждения на перезапись перезаписываем папку с файлами

class YDClient:

    def __init__(self, name_papka, auto):
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.path = name_papka
        self.headers = auto

    def papka_create(self):
        params = { 'path': self.path}
        headers = {'Authorization': auto}

        response = requests.put(self.url, params=params, headers=headers)

        if response.status_code == 201:
            yd_client.yd_write_fotos()
        else:
            print(response.json()['message'])
            answer = input(f'Подтвердите перезапись файлов в папке {self.path} : да или нет -  ')

            if answer == 'да':
                response = requests.delete(self.url, params=params, headers=headers)
                response = requests.put(self.url, params=params, headers=headers)
                yd_client.yd_write_fotos()
            else:
                exit

    def yd_write_fotos(self):

        photos = vk_client.choose_fotos_max_size()

        for key, value in tqdm(photos.items()):
            file_name = key
            photo_url = photos[key][0]
            response = requests.get(photo_url)
            response = requests.get(f'{photo_url}&overwrite= True')

            with open(file_name, 'wb') as f:
                f.write(response.content)

            url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            params = {"path": f'{self.path}/{file_name}&overwrite= True'}
            headers = {'Authorization': auto}
            response = requests.get(url, params=params, headers=headers)
            upload_url = response.json()['href']

            with open(file_name, 'rb') as f:
                try:
                    response = requests.put(upload_url, files={"file": f})
                except KeyError:
                    print(response)

if __name__ == '__main__':
    vk_client = VKClient(TOKEN,160519787)
    photo_all_size = vk_client.get_profile_photos()
    photos_max_size = vk_client.choose_fotos_max_size()
    yd_client = YDClient('PHOTO_VK', auto)
    yd_client.papka_create()


