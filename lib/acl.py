import urllib
import motor
from tornado import gen

__author__ = 'ila'

import functools
from tornado.gen import Return, Task, coroutine


def acl(permission):
    def outer(f):
        @coroutine
        def inner(self, *args, **kwargs):
            self._auto_finish = False
            if '@' not in permission:
                route = self.__class__.__name__.lower()
                full_permission = "%s@%s" % (route, permission)
            else:
                full_permission = permission
            user = yield Task(self.get_current_user_async)
            check = yield Task(self.check_acl_permissions, full_permission, user)
            if check:
                f(self, *args, **kwargs)
            else:
                self.clear()
                self.set_status(401)
                self.write('%s | No Permission' % self._status_code)
                self.finish()
        return inner
    return outer


def authenticated_async(f):

    @functools.wraps(f)
    @coroutine
    def wrapper(self, *args, **kwargs):
        self._auto_finish = False
        self.current_user = yield Task(self.get_current_user_async)
        if not self.current_user:
            self.redirect(self.get_login_url() + '?' +
                          urllib.urlencode(dict(next=self.request.uri)))
        else:
            f(self, *args, **kwargs)
    return wrapper


class AclMixin(object):

    @coroutine
    def check_acl_permissions(self, permission, user):
        groups = [{'name': group} for group in user['groups']]
        group_permissions = yield motor.Op(self.groups.aggregate, [
            {'$match': {'$or': [{'name': 'user'}]}},
            {'$unwind': '$permissions'},
            {'$group': {'_id': '$group', 'permissions': {'$push': '$permissions'}}}
        ])
        group_permissions = group_permissions['result'][0]['permissions']
        permissions = user['permissions'] + list(set(group_permissions) - set(user['permissions']))
        if permission in permissions:
            raise Return(True)
        else:
            raise Return(False)