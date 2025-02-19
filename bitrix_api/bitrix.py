import requests
import time
import base64
import os


class BitrixAPI(object):
    DURATION = 2  # задержка в секундах между запросами, нужна чтобы не сработало ограничение

    def __init__(self, user_id, webhook, log):
        self.logger = log
        self.user_id = user_id
        self.basic_url = f'https://bitrix.sigur.com/rest/{self.user_id}/{webhook}/'
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json"
        }

    # Функция для проверки, выдает профиль пользователя, от которого обращаются к АПИ битрикса
    def profile(self):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'profile.json'

            response = self.session.get(url=url, headers=self.headers).json()

            try:
                self.logger.error("Ошибка при получении профиля: " + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Профиль получен")
                return response

        except Exception as error:
            self.logger.error("Ошибка при получении профиля: " + str(error))
            return None

    # Функция для получения информации по задаче
    def get_task_info(self, task_id):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'tasks.task.get'

            body = {
                "taskId": task_id,
                "select": ["*"]
            }

            response = self.session.post(url=url, headers=self.headers, json=body).json()

            try:
                self.logger.error(f"Ошибка при получении информации о задаче {task_id}: "
                                  + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Получена информация о задаче {task_id}")
                return response

        except Exception as error:
            self.logger.error(f"Ошибка при получении информации о задаче {task_id}: "
                              + str(error))
            return None

    # Функция для создания папки на диске
    def add_disk_folder(self, parent_folder_id, folder_name):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'disk.folder.addsubfolder'

            body = {
                "id": parent_folder_id,
                "data":
                    {
                        "NAME": folder_name
                    }
            }

            response = self.session.post(url=url, headers=self.headers, json=body).json()

            try:
                self.logger.error("Ошибка при создании папки: " + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Папка ({folder_name}) в Bitrix создана")
                return response['result']['ID']

        except Exception as error:
            self.logger.error("Ошибка при добавлении задачи: " + str(error))
            return None

    # Функция для добавления файла в указанную папку
    def add_file(self, folder_id, folder_name, file_name):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'disk.folder.uploadfile'

            path_file = os.sep.join([os.getcwd(), folder_name, file_name])

            with open(path_file, "rb") as file:
                encoded = base64.b64encode(file.read()).decode('utf-8')

            body = {
                "id": folder_id,
                "data":
                    {
                        "NAME": file_name
                    },
                "fileContent": [
                    file_name,
                    encoded
                ]
            }

            response = self.session.post(url=url, headers=self.headers, json=body).json()

            try:
                self.logger.error(f"Ошибка при добавлении файла {file_name} в папку {folder_id}: " + str(
                    response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Файл ({file_name}) в папку ({folder_id}) в Bitrix добавлен")
                result = 'n' + str(response['result']['ID'])
                return result

        except Exception as error:
            self.logger.error(f"Ошибка при добавлении файла {file_name} в папку {folder_id}: " + str(error))
            return None

    # Функция для получения информации о файле
    def get_file_info(self, file_id):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'disk.file.get'

            body = {
                "id": file_id
            }

            response = self.session.post(url=url, headers=self.headers, json=body).json()

            try:
                self.logger.error(f"Ошибка при получении информации о файле {file_id}: "
                                  + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Получена информация о файле {file_id}")
                return response

        except Exception as error:
            self.logger.error(f"Ошибка при получении информации о файле {file_id}: "
                              + str(error))
            return None

    # Функция для добавления задачи в проект
    def add_task(self, group_id, created_datetime, title, description, stage, files=None):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'tasks.task.add'
            created_datetime_string = created_datetime.isoformat(timespec='seconds')

            body = {
                "fields":
                    {
                        "STATUS": 5,
                        "GROUP_ID": group_id,
                        "CREATED_BY": self.user_id,
                        "RESPONSIBLE_ID": self.user_id,
                        "CREATED_DATE": created_datetime_string,
                        "TITLE": title,
                        "DESCRIPTION": description,
                        "STAGE_ID": stage
                    }
            }

            if files:
                body["fields"].update({"UF_TASK_WEBDAV_FILES": files})

            response = self.session.post(url=url, headers=self.headers, json=body).json()

            try:
                self.logger.error("Ошибка при добавлении задачи: " + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Задача ({title}) в Bitrix добавлена")
                return response['result']['task']['id']

        except Exception as error:
            self.logger.error("Ошибка при добавлении задачи: " + str(error))
            return None

    # Функция для добавления комментария к задаче
    def add_comment(self, task_id, description, files=None):
        time.sleep(self.DURATION)
        try:
            url = self.basic_url + f'task.commentitem.add'

            body = {
                "TASKID": task_id,
                "FIELDS":
                    {
                        "POST_MESSAGE": description
                    }
            }

            if files:
                body["FIELDS"].update({"UF_FORUM_MESSAGE_DOC": files})

            response = self.session.post(url=url, headers=self.headers, json=body).json()

            try:
                self.logger.error("Ошибка при добавлении комментария: " + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Комментарий в Bitrix добавлен")
                return response['result']

        except Exception as error:
            self.logger.error("Ошибка при добавлении комментария: " + str(error))
            return None
