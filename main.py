import os
from bitrix_api import BitrixAPI
import datetime as dt
import logging
from dotenv import load_dotenv

from youtrack_api import YouTrackAPI

# Настройки логирования
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

fh = logging.FileHandler('migration.log', mode='w', encoding='utf-8')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
log.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

load_dotenv()

# Настройки
youtrack_sprint_number = '106-65' # Номер спринта в YouTrack, из которого переносим данные
bitrix_group_id = 871 # Номер группы в Битриксе, в которую добавляем данные
bitrix_stage = 5627 # Внутренний номер этапа в Битриксе, в который попадают все перемещаемые задачи
bitrix_parent_folder_id = 1762605 # ID корневой папки проекта (группы), в которой будем создавать новые папки под каждую задачу
bitrix_user_id = 543 # ID юзера в Битриксе, от которого будут создаваться новые задачи и комментарии
folder_name = 'temporary' # Названия папки для временного размещения скачиваемых файлов из задачи

# Создаём экземпляры классов для работы с апи Битрикса и YouTrack
test_bitrix = BitrixAPI(bitrix_user_id, os.getenv('BITRIX_WEBHOOK'), log)
test_youtrack = YouTrackAPI(os.getenv('YOUTRACK_TOKEN'), os.getenv('YOUTRACK_BASIC_URL'), log, 50)

# Находим все issues (карточки) по конкретному спринту в YouTrack
issues = test_youtrack.get_list_issues(youtrack_sprint_number)

test_issues = [issues[135]] # Для теста, или полу-ручного режима, чтобы только одна карточка прокрутилась

# Айди задач, которые неудачно загрузились
error_migration_id = set()

# По каждой карточке в спринте
for id, issue in enumerate(test_issues): # Если нужно сразу все обработать, то вставляем issues сюда
    issue_id = issue['id']
    issue_author = issue['reporter']['fullName']
    issue_date_created = dt.datetime.fromtimestamp(issue['created'] / 1000)
    issue_head = issue['summary']
    issue_number = issue['idReadable']
    issue_attachment_list = issue['attachments']

    # Краткое описание для заголовка задачи
    issue_description = f"({issue_number}) {issue_head}"

    # Полный текст для задачи
    issue_text = f"[I]{issue_date_created.isoformat(timespec='seconds')}[/I] - [B]{issue_author}[/B]\n\n" + str(issue['description'])

    # Создаём в Битриксе новую папку для перемещаемой задачи
    bitrix_folder_id = test_bitrix.add_disk_folder(bitrix_parent_folder_id, f'{issue_number}')

    # Собираем список файлов, которые будем прикреплять к задаче в Битрикс
    files_to_task = []

    index = 1

    # Скачиваем вложения из issue (если они есть и не прикреплены к комментам)
    if len(issue_attachment_list) > 0:
        for attachment in issue_attachment_list:
            if attachment['comment']:
                pass
            else:
                attachment_url = attachment['url']
                file_name = str(attachment['name'])

                # Собираем новое имя файла на случай повторных, добавляем впереди число по порядку
                new_file_name = (str(index) + '_' + file_name)

                path_file = os.sep.join([os.getcwd(), folder_name, new_file_name])
                test_youtrack.download_attachment(attachment_url, path_file)

                file_to_task_id = test_bitrix.add_file(bitrix_folder_id, folder_name, new_file_name)

                # Если была ошибка при загрузке файла, то добавляем эту задачу в список с ошибками
                if file_to_task_id is None:
                    error_migration_id.add(id)

                files_to_task.append(file_to_task_id)

                index += 1

                # Удаляем файл
                os.remove(path_file)

    # Создаём новую задачу в Битриксе
    bitrix_task_id = test_bitrix.add_task(bitrix_group_id,
                                          issue_date_created,
                                          issue_description,
                                          issue_text,
                                          bitrix_stage,
                                          files_to_task)

    # Если была ошибка при создании задачи в Битриксе, то добавляем эту задачу в список с ошибками
    if bitrix_task_id is None:
        error_migration_id.add(id)

    # Находим все комментарии в YouTrack к этому issue
    list_comments = test_youtrack.get_list_comments(issue_id)

    # Добавляем все комментарии к новой задачи в Битриксе
    for comment in list_comments:
        # Преобразовываем в дату timestamp
        date = dt.datetime.fromtimestamp(comment['created'] / 1000)

        # Формируем текст комментария
        comment_text = f"[I]{date.isoformat(timespec='seconds')}[/I] - [B]{comment['author']['fullName']}[/B]\n\n{comment['text']}"

        # Собираем список файлов, которые будем прикреплять к комментарию в Битрикс
        files_to_comment = []

        # Скачиваем вложения из комментариев (если они есть)
        if len(comment['attachments']) > 0:
            for attachment in comment['attachments']:
                attachment_url = attachment['url']
                file_name = str(attachment['name'])

                # Собираем новое имя файла на случай повторных, добавляем впереди число по порядку
                new_file_name = (str(index) + '_' + file_name)

                path_file = os.sep.join([os.getcwd(), folder_name, new_file_name])
                test_youtrack.download_attachment(attachment_url, path_file)

                file_to_comment_id = test_bitrix.add_file(bitrix_folder_id, folder_name, new_file_name)

                # Если была ошибка при загрузке файла, то добавляем эту задачу в список с ошибками
                if file_to_comment_id is None:
                    error_migration_id.add(id)

                files_to_comment.append(file_to_comment_id)
                index += 1

                # Удаляем файл
                os.remove(path_file)

        # Добавляем комментарий к задаче
        bitrix_comment_id = test_bitrix.add_comment(bitrix_task_id, comment_text, files_to_comment)

        # Если была ошибка при создании задачи в Битриксе, то добавляем эту задачу в список с ошибками
        if bitrix_comment_id is None:
            error_migration_id.add(id)


log.info(f"Миграция завершена, всего задач ({len(issues)})"
         f", перенесено ({len(issues) - len(error_migration_id)}), с ошибками ({len(error_migration_id)})")
log.info(f"Список айди с ошибками {error_migration_id}")
