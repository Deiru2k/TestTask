__author__ = 'ila'

import tornado.ioloop
import tornado.escape
from lib.acl import authenticated_async, acl, AclMixin
import motor
from bson import json_util as json
from bson import ObjectId
from bson.errors import InvalidId
from tornado.web import RequestHandler, Application, asynchronous, os
from tornado.gen import Return, coroutine, Task
import hashlib


client = motor.MotorClient().open_sync()


class BaseHandler(AclMixin, RequestHandler):

    @coroutine
    def get_current_user_async(self, callback=None):
        user = None
        key = self.get_secure_cookie('session_key')
        if key:
            session = yield motor.Op(self.sessions.find_one, ObjectId(key))
            if session:
                user = yield motor.Op(self.users.find_one, {"email": session['email']})
        if callback:
            callback(user)
        else:
            raise Return(user)

    def initialize(self):
        self.db = client['test']
        self.users = self.db['users']
        self.groups = self.db['groups']
        self.sessions = self.db['sessions']
        self.posts = self.db['posts']


class Main(BaseHandler):

    @authenticated_async
    @asynchronous
    def get(self):
        self.render('index.html')


class Posts(BaseHandler):

    @authenticated_async
    @acl('retrieve')
    @coroutine
    def get(self, _id=None):
        if _id:
            try:
                print _id
                _id = ObjectId(_id)
                post = yield motor.Op(self.posts.find_one, id)
                print post
                self.write(json.dumps(post))
                self.finish()
            except InvalidId:
                self.clear()
                self.set_status(500, reason="Invalid ID")
                self.write('Invalid ID')
                self.finish()
        else:
            posts = self.posts.find()
            posts = yield motor.Op(posts.to_list)
            self.write(json.dumps(posts))
            self.finish()

    @authenticated_async
    @acl('create')
    @coroutine
    def post(self, _id=None):
        data = tornado.escape.json_decode(self.request.body)
        post_id = yield motor.Op(self.posts.insert, data)
        post = yield motor.Op(self.posts.find_one, post_id)
        self.write(json.dumps(post))
        self.finish()


class Users(BaseHandler):

    @authenticated_async
    @acl('retrieve')
    @coroutine
    def get(self, _id=None):
        if _id:
            try:
                _id = ObjectId(_id)
                user = yield motor.Op(self.users.find_one, _id)
                self.write(json.dumps(user))
                self.finish()
            except InvalidId:
                self.clear()
                self.set_status(500, reason="Invalid ID")
                self.write('Invalid ID')
                self.finish()
        else:
            users = self.users.find()
            users = yield motor.Op(users.to_list)
            self.write(json.dumps(users))
            self.finish()

    @authenticated_async
    @acl('update')
    @coroutine
    def put(self, _id):
        data = tornado.escape.json_decode(self.request.body)
        data.pop('_id')
        try:
            _id = ObjectId(_id)
            user = yield motor.Op(self.users.find_and_modify, _id, {'$set': data}, new=True)
            self.write(json.dumps(user))
            self.finish()
        except InvalidId:
            self.clear()
            self.set_status(500, reason="Invalid ID")
            self.write('Invalid ID')
            self.finish()


class Groups(BaseHandler):

    @authenticated_async
    @acl('retrieve')
    @coroutine
    def get(self, _id=None):
        if _id:
            try:
                _id = ObjectId(_id)
                group = yield motor.Op(self.groups.find_one, _id)
                self.write(json.dumps(group))
                self.finish()
            except InvalidId:
                self.clear()
                self.set_status(500, reason="Invalid ID")
                self.write("Invalid ID")
                self.finish()
        else:
            groups = self.groups.find()
            groups = yield motor.Op(groups.to_list)
            self.write(json.dumps(groups))
            self.finish()

    @authenticated_async
    @acl('create')
    @coroutine
    def post(self, _id=None):
        data = tornado.escape.json_decode(self.request.body)
        print data
        group_id = yield motor.Op(self.groups.insert, data)
        group = yield motor.Op(self.groups.find_one, group_id)
        self.write(json.dumps(group))
        self.finish()

    @authenticated_async
    @acl('update')
    @coroutine
    def put(self, _id):
        data = tornado.escape.json_decode(self.request.body)
        data.pop('_id')
        try:
            _id = ObjectId(_id)
            group = yield motor.Op(self.groups.find_and_modify, _id, {'$set': data}, new=True)
            self.write(json.dumps(group))
            self.finish()
        except InvalidId:
            self.clear()
            self.set_status(500, reason="Invalid ID")
            self.write("Invalid ID")
            self.finish()


class LoginHandler(BaseHandler):
    @asynchronous
    def get(self):
        self.render('login.html')

    @coroutine
    def post(self):
        email = self.get_argument('email')
        password = hashlib.sha256(self.get_argument('password')).hexdigest()
        user = yield motor.Op(self.users.find_one, {'email': email})
        if user and user['password'] == password:
            session_id = yield motor.Op(self.sessions.insert, {'email': email})
            self.set_secure_cookie('session_key', str(session_id))
            self.redirect('/')
        else:
            self.clear()
            self.set_status(401)
            self.write('Bad login')
            self.finish()


class LogoutHandler(BaseHandler):
    @authenticated_async
    @asynchronous
    def get(self):
        session_key = self.get_secure_cookie('session_key')
        self.clear_cookie('session_key')
        result = yield motor.Op(self.sessions.remove, session_key)
        self.redirect('/login')
        self.finish()


class RegisterHandler(BaseHandler):
    @asynchronous
    def get(self):
        self.render('register.html')

    @coroutine
    def post(self):
        email = self.get_argument('email')
        password = hashlib.sha256(self.get_argument('password')).hexdigest()
        user = yield motor.Op(self.users.insert, {'email': email,
                                                  'password': password,
                                                  'permissions': ['posts@create'],
                                                  'groups': ['user']})
        if type(user) == type(ObjectId):
            self.redirect('main')
            self.finish()


static_path = os.path.join(os.path.dirname(__file__), "res")

application = Application(
    [
        (r'/', Main),
        (r'/posts', Posts),
        (r'/posts/(\d+\w+)', Posts),
        (r'/users', Users),
        (r'/users/(\d+\w+)', Users),
        (r'/groups', Groups),
        (r'/groups/(\d+\w+)', Groups),
        (r'/login', LoginHandler),
        (r'/logout', LogoutHandler),
        (r'/signup', RegisterHandler),
        (r'/res/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
    ],
    cookie_secret="WHOISYOURDADDY",
    login_url="/login",
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
)
application.listen(9999)

try:
    print "Start"
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    print "Stop"
    exit()