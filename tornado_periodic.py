#!/usr/bin/env python
# -*- coding: utf-8 -*-


from time import time
import tornado.ioloop
import tornado.web
from threading import Timer
from tornado import gen
from datetime import date
import tornado.escape
import tornado_mysql
import random
import hashlib

h = hashlib.new('md5')

def corsHeaders(inst):
    inst.add_header('Access-Control-Allow-Origin', inst.request.headers.get('Origin', '*'))
	
def startSession(name):
    session_id = name + str(random.randint(0, 10000))
    return session_id
	

class MainHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.add_header('Access-Control-Allow-Origin', self.request.headers.get('Origin', '*'))
		
    @gen.coroutine			
    def on_connection_close(self):
        t.cancel()
        print 'Finish ', session_id
        conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='drunk_adventures')
        cur = conn.cursor()
        yield cur.execute("UPDATE avatar SET session = NULL WHERE login = %s; COMMIT;" , (player,) )
        cur.close()    
        del conn	


    @tornado.web.asynchronous
    def post(self):
        global session_id
        global player
        session_id = self.get_argument('session_id', '')
        player = self.get_argument('u','')
        print 'Start ', session_id
        global t
        t = Timer(60, self.on_response)
        t.start()
		
	
    def on_response(self):
        print 'Finish'
        self.write("completed at " + str(time()))
        self.finish()


class LoginHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        corsHeaders(self)

    @gen.coroutine
    def post(self):
        username = self.get_argument('username', '')
        passwd = self.get_argument('passwd', '')
		
        print '!!!!!!!!!!!!!!!!!!'
        print username
        print username.encode('cp1251')
        print '!!!!!!!!!!!!!!!!!!!'
		
        conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='drunk_adventures')
        cur = conn.cursor()
        yield cur.execute("SELECT password, session FROM avatar WHERE login = '%s' ;" % username)
        cur.close()    
        del conn
        creds = []
        
        for row in cur:
            creds.append(row)	
				
        if creds and creds[0][0] == passwd:
            session_id = startSession(username)
            h.update(session_id)
            self.write({'auth_status': 'Authorization successful', 'se': h.hexdigest(), 'u': username})
            conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='drunk_adventures')
            cur = conn.cursor()
            yield cur.execute("UPDATE avatar SET session = %s WHERE login = %s; COMMIT;" , (session_id, username))
            cur.close()    
            del conn
            		
        else:
            self.write({'auth_status': 'Go fuck yourself asshole', 'se':''})

class CheckIfLoggedInHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.add_header('Access-Control-Allow-Origin', self.request.headers.get('Origin', '*'))
		
    @gen.coroutine
    def post(self):
        session_id = self.get_argument('session_id', '')
        if not session_id or session_id == "null":
            self.write("not_authenticated")
        		
class RegistartionHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.add_header('Access-Control-Allow-Origin', self.request.headers.get('Origin', '*'))

    @gen.coroutine
    def post(self):
        username = self.get_argument('reg-username', '')
        passwd = self.get_argument('reg-passwd', '')
        email = self.get_argument('reg-email','')
		
        conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='drunk_adventures')
        cur = conn.cursor()
        yield cur.execute("SELECT login FROM avatar WHERE login = '%s' ;" % (username,))
        cur.close()    
        del conn
		
        names = []
        
        for row in cur:
            names.append(row)	
		
        if names:
            self.write({'reg_status': 'Go fuck yourself asshole', 'se':''})
        else:
            session_id = startSession(username)
            h.update(session_id)
            conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='drunk_adventures')
            cur = conn.cursor()
            yield cur.execute("INSERT INTO avatar (login, password, email, session) VALUES (%s,%s,%s, %s) ; COMMIT;" , (username, passwd, email, session_id))
            cur.close()    
            del conn
            self.write({'reg_status': 'Registration successful', 'se': h.hexdigest(), 'u': username})
            	
		

class DeleteSessionHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.add_header('Access-Control-Allow-Origin', self.request.headers.get('Origin', '*'))

    @gen.coroutine
    def post(self):
        session_id = self.get_argument('session_id','')
        player = self.get_argument('u','')
        print session_id
        conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='drunk_adventures')
        cur = conn.cursor()
        yield cur.execute("UPDATE avatar SET session = NULL WHERE login = %s; COMMIT;" , (player,))
        cur.close()    
        del conn

        				
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", MainHandler),
				(r"/login", LoginHandler),
				(r"/registration", RegistartionHandler),
				(r"/delete_session", DeleteSessionHandler),
                (r"/check_if_logged_in", CheckIfLoggedInHandler),
                ]
        tornado.web.Application.__init__(self, handlers)

if __name__ == "__main__":
    app  = Application()
    app.listen(8880)

    tornado.ioloop.IOLoop.instance().start()