import requests


class YouTrackAPI(object):

    def __init__(self, token, basic_url, log):
        self.basic_url = basic_url
        self.logger = log
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + token
        }

    # Функция для поиска спринтов на доске YouTrack
    def get_agile_content(self, agile_id):
        try:
            url = self.basic_url + f'/api/agiles/{agile_id}'

            params = {
                'fields': 'id,name,owner(id,name,login),projects(id,name),sprints(id,name,issues(id,created,idReadable,description,summary,reporter(fullName),attachments(id,url,name,comment)))'}

            response = self.session.get(url=url, headers=self.headers, params=params).json()

            try:
                self.logger.error("Ошибка при поиске спринтов в YouTrack: " + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Информация по спринтам в YouTrack получена")
                return response

        except Exception as error:
            self.logger.error("Ошибка при поиске спринтов в YouTrack: " + str(error))
            return None

    # Функция для получения списка задач по указанному спринту YouTrack
    def get_list_issues(self, agile_id):
        try:
            sprint = self.get_agile_content(agile_id)['sprints'][0]

            issues = sprint['issues']

            self.logger.info(f"Достаём список задач из спринта ({agile_id}) из YouTrack")
            return issues

        except Exception as error:
            self.logger.error(f"Не удалось достать список задач из спринта ({agile_id}) из YouTrack" + str(error))
            return None

    # Функция для получения списка комментариев к указанной задаче YouTrack
    def get_list_comments(self, issue_id):
        try:
            url = self.basic_url + f'/api/issues/{issue_id}/comments'

            params = {'fields': 'id,attachments(id,url,name),author(fullName),created,text'}

            response = self.session.get(url=url, headers=self.headers, params=params).json()

            try:
                self.logger.error(f"Ошибка при поиске комментариев к задаче ({issue_id}) в YouTrack: " + str(response['error_description']))
                return None

            except Exception:
                self.logger.info(f"Комментарии к задаче ({issue_id}) в YouTrack получены")
                return response

        except Exception as error:
            self.logger.error(f"Ошибка при поиске комментариев к задаче ({issue_id}) в YouTrack: " + str(error))
            return None

    # Функция для скачивания файла в YouTrack
    def download_attachment(self, url_attachment, file_path):
        try:
            url = self.basic_url + url_attachment

            response = self.session.get(url=url, headers=self.headers)

            try:
                self.logger.error(f"Ошибка при скачивании файла ({url_attachment}) в YouTrack: " + str(response.json()['error_description']))
                return None

            except Exception:
                with open(file_path, 'wb') as file:
                    file.write(response.content)

                self.logger.info(f"Файл из YouTrack ({url_attachment}) успешно скачан")
                return response

        except Exception as error:
            self.logger.error(f"Ошибка при скачивании файла ({url_attachment}) в YouTrack: " + str(error))
            return None
