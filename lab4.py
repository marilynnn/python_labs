import json
import datetime
from aiohttp import web


# класс лабораторной работы, для инициализации обязательно нужно указать дедлайн
class Lab:
    def __init__(self, str_date):
        self.description = ""  # описание лабораторной
        self.date = datetime.datetime.strptime(str_date, '%d.%m.%Y')  # дедлайн
        self.students = list()  # список студентов

    def set_description(self, description):  # обновить описание (очищает старое описание)
        self.description = description

    def set_deadline(self, str_date):  # обновить дедлайн
        self.date = datetime.datetime.strptime(str_date, '%d.%m.%Y')

    @staticmethod
    def process_query_str(string):
        string.replace(" ", "")
        string.replace("[", "")
        string.replace("]", "")
        string.replace("\'", "")

    def add_students(self, string):   # добавить студентов в конец списка
        string_without_spaces = string.replace(" ", "")
        students_list = string_without_spaces.strip().split(',')
        self.students = self.students + students_list
        print(self.students)

    def delete_students(self, string):  # удалить студентов
        string_without_spaces = string.replace(" ", "")
        for student in string_without_spaces.strip().split(','):
            if student in self.students:
                self.students.remove(student)

    def update_students(self, string):  # очистить список студентов и задать новый
        string_without_spaces = string.replace(" ", "")
        self.students = string_without_spaces.strip().split(',')

    def __str__(self):  # вся информация о лабораторной
        s = '{{\"deadline\" : \"{0}\", \"description\" : \"{1}\", \"students\" : \"{2}\"}}'\
            .format(self.date.strftime('%d.%m.%Y'), self.description, ", ".join(self.students))
        return s


# класс сервера
class Server:
    def __init__(self):
        self.app = web.Application()
        self.host = 'localhost'
        self.port = 8080
        self.labs = dict()
        self.url = 'http://' + self.host + ':' + str(self.port) + '/labs'

        #  добавляем все нужные маршруты и связываем запросы с функциями
        self.app.router.add_post('/labs', self.handle_create_lab)
        self.app.router.add_get('/labs', self.handle_get_all_labs)
        self.app.router.add_patch('/labs/{name}', self.handle_edit_lab)
        self.app.router.add_get('/labs/{name}', self.handle_get_lab)
        self.app.router.add_delete('/labs/{name}', self.handle_delete_lab)

    #  функция для GET-запроса информации о всех лабораторных
    async def handle_get_all_labs(self, request):
        try:
            response_obj = {"status": "success"}
            if len(self.labs) == 0:
                response_obj["message"] = "no labs"
            else:
                for key in self.labs:
                    response_obj[key] = str(self.labs[key])

            return web.Response(text=json.dumps(response_obj), status=200)

        except Exception as ex:
            print("Getting all labs failed")

            response_obj = {"status": "failed", "message": str(ex)}
            return web.Response(text=json.dumps(response_obj), status=400)

    #  функция для POST-запроса на создание лабораторной работы, обязательно нужно указать дедлайн,
    #  опционально -- описание
    async def handle_create_lab(self, request):
        try:
            # print(request.query)
            lab_name = request.query["name"]
            lab_deadline = request.query["date"]
            self.labs[lab_name] = Lab(lab_deadline)
            if "description" in request.query:
                self.labs[lab_name].set_description(request.query["description"])

            response_obj = {"status": "success", 'Location': "{0}/{1}".format(self.url, lab_name)}
            return web.Response(text=json.dumps(response_obj), status=201)

        except Exception as ex:
            print("Creating new lab failed", str(ex))

            response_obj = {"status": "failed", "message": str(ex)}
            return web.Response(text=json.dumps(response_obj), status=400)

    #  функция для PATCH-запроса на изменение существующей лабораторной
    async def handle_edit_lab(self, request):
        try:
            lab_name = self.get_lab_name(request)

            if lab_name not in self.labs:
                response_obj = {"status": "failed", "message": str('lab with name \'{}\' doesn\'t exist'.format(lab_name))}
                print(self.labs)
                return web.Response(text=json.dumps(response_obj), status=404)

            current_lab = self.labs[lab_name]
            if "description" in request.query:
                current_lab.set_description(request.query["description"])
            if "date" in request.query:
                current_lab.set_deadline(request.query["date"])
            if "students" in request.query:
                current_lab.update_students(request.query["students"])
            if "add_students" in request.query:
                # print(type(request.query["add_students"]))
                current_lab.add_students(request.query["add_students"])
            if "delete_students" in request.query:
                current_lab.delete_students(request.query["delete_students"])

            response_obj = {"status": "success", "message": 'lab is updated'}
            return web.Response(text=json.dumps(response_obj), status=200)

        except Exception as ex:
            print("Editing lab failed", ex)

            response_obj = {"status": "failed", "message": str(ex)}
            return web.Response(text=json.dumps(response_obj), status=400)

    #  функция GET-запроса информации по конкретной лабораторной
    async def handle_get_lab(self, request):
        try:
            lab_name = self.get_lab_name(request)

            if lab_name not in self.labs:
                response_obj = {"status": "failed", "message": str('lab with name \'{}\' doesn\'t exist'.format(lab_name))}
                return web.Response(text=json.dumps(response_obj), status=404)

            current_lab = self.labs[lab_name]

            response_obj = {"status": "success", lab_name: str(current_lab)}
            return web.Response(text=json.dumps(response_obj), status=200)

        except Exception as ex:
            print("Getting lab failed")

            response_obj = {"status": "failed", "message": str(ex)}
            return web.Response(text=json.dumps(response_obj), status=400)

    #  функция DELETE-запроса на удаление лабораторной
    async def handle_delete_lab(self, request):
        try:
            lab_name = self.get_lab_name(request)

            if lab_name not in self.labs:
                response_obj = {"status": "failed", "message": str('lab with name \'{}\' doesn\'t exist'.format(lab_name))}
                return web.Response(text=json.dumps(response_obj), status=404)

            self.labs.pop(lab_name)
            response_obj = {"status": "success", "message": 'lab was deleted'}
            return web.Response(text=json.dumps(response_obj), status=200)

        except Exception as ex:
            response_obj = {"status": "failed", "message": str(ex)}
            return web.Response(text=json.dumps(response_obj), status=400)

    #  функция для получения имени текущей лабораторной работы
    def get_lab_name(self, request):
        return str(request.url).removeprefix(self.url + '/').split('?')[0]

    #  запуск сервера
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)


server = Server()
server.run()