#-*- coding: utf-8
from flask import Flask, g, request, render_template, session
from flask import url_for, redirect
import sys, unicodedata, os, time
import sqlite3, hashlib


app = Flask(__name__)
app.secret_key = 'a'
USER_DB = "./db/user.db"
BOARD_DB = "./db/board.db"

#USER_DB 연결
def user_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(USER_DB)
    return db

#USER 테이블 생성
def user_table():
    with app.app_context():
        db = user_db()
        f = open('user.sql', 'r')
        db.execute(f.read())
        db.commit()

#BOARD_DB 연결
def board_db():
    db = getattr(g, 'database', None)
    if db is None:
        db = g.database = sqlite3.connect(BOARD_DB)
    return db

#BOARD 테이블 생성
def board_table():
    with app.app_context():
        db = board_db()
        f = open('board.sql', 'r')
        db.execute(f.read())
        db.commit()

#USER 추가
def add_user(user_id, user_pw, user_name, user_email, user_phone):
    sql = 'INSERT INTO users(id, password, name, email, phone) VALUES ("%s", "%s", "%s", "%s", "%s")' % (user_id, user_pw, user_name, user_email, user_phone)
    db = user_db()
    db.execute(sql)
    db.commit()

#USER 정보 가져오기(session[name]으로)
def get_user1(user_id):
    sql = 'SELECT * FROM users WHERE id="{}"'.format(user_id)
    db = user_db()
    res = db.execute(sql)
    res = res.fetchone()
    return res

#USER 정보 가져오기(id, pw로)
def get_user2(user_id, user_pw):
    sql = 'SELECT * FROM users WHERE id="%s" and password="%s"' % (user_id, user_pw)
    db = user_db()
    res = db.execute(sql)
    res = res.fetchone()
    return res

#BOARD 추가
def add_board(title, content):
    user_id = session['username']
    now = time.localtime()
    date = "%04d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)

    sql = 'INSERT INTO board(id, today_date, title, content) VALUES("%s","%s","%s","%s")' % (user_id, date, title, content)
    db = board_db()
    db.execute(sql)
    db.commit()

#BOARD 정보 가져오기
def get_board():
    sql = 'SELECT * FROM board order by idx desc'
    db = board_db()
    res = db.execute(sql)
    res = res.fetchall()
    return res

@app.route('/')
def main():
    if session.get('username', None) != None:
        return render_template('main.html', name=session['username'])
    else:
        return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        user_id = request.form.get('user_id')
        user_pw = request.form.get('user_pw')
        user_pw = hashlib.sha224(user_pw).hexdigest()
        #if get_user(user_id, user_pw):
        if get_user2(user_id, user_pw) is not None:
            session['username'] = user_id
           # return render_template('main.html', name=session['username'])
            return redirect(url_for('main'))
        else:
            return render_template('login.html', login_failed=True)

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')
    elif request.method == 'POST':
        user_id = request.form.get('user_id')
        user_pw = request.form.get('user_pw')
        user_pw = hashlib.sha224(user_pw).hexdigest()
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')
        user_phone = request.form.get('user_phone')
        add_user(user_id, user_pw, user_name, user_email, user_phone)
        return "<script>alert('회원가입이 완료되었습니다.'); window.location='/login';</script>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main'))

@app.route('/board', methods=['GET', 'POST'])
def board():
    if session.get('username', None) != None:
        if request.method == 'POST':
            print "POST"
            keyword = request.form['keyword']
            column = request.form['column']

            db = board_db()

            if str(column) == 'title':
                sql_str = "select * from board where title = '%s' order by idx desc" % (keyword)
            if str(column) == 'content':
                sql_str = "select * from board where content= '%s' order by idx desc" % (keyword)

            res = db.execute(sql_str)
            result = []
            res = res.fetchall()

            if res:
                result = list(res)
                for i in range(0, len(result)):
                    if type(i) != int:
                        result[i] = ''.join(result[i])
                        result[i] = unicodedata.normalize('NFKD', result[i]).encode('ascii', 'ignore')

            return render_template('board.html', name=session['username'], data=result)
        return render_template('board.html', name=session['username'], data=get_board())

    if session.get('username', None) == None:
        return render_template('board.html', data=get_board())




@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'GET':
        return render_template("write.html", name=session['username'])
    elif request.method == 'POST':
        title = request.form.get('title').encode('utf8')
        content = request.form.get('content').encode('utf8')
        add_board(title, content)
        return render_template('board.html', name=session['username'], data=get_board())

#글보기
@app.route('/view', methods=['GET', 'POST'])
def view():
    idx = request.args.get('idx')
    sql = 'select * from board where idx="%s"' % (idx)
    db = board_db()
    res = db.execute(sql)
    res = res.fetchone()
    if session.get('username', None) != None:
        return render_template('view.html', name=session['username'], data=res)
    else:
        return render_template('view.html', data=res)


#글 수정
@app.route('/modified', methods=['GET', 'POST'])
def modified():
    if request.method == 'GET':
        idx = request.args.get('idx')
        sql = "select * from board where idx='%s'" % (idx)
        db = board_db()
        res = db.execute(sql)
        res = res.fetchone()
        return render_template('modified.html', name=session['username'], data=res)

#글 수정 체크
@app.route('/modified_chk', methods=['GET', 'POST'])
def modified_chk():
        idx = request.form.get('idx')
        title = request.form.get("title").encode('utf8')
        content = request.form.get("content").encode('utf8')
        sql = 'UPDATE board SET title="%s", content="%s" WHERE idx="%s"' % (title, content, idx)
        db = board_db()
        db.execute(sql)
        db.commit()
        return redirect(url_for('view', idx=idx))

@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if request.method == 'GET':
        return render_template('mypage.html', name=session['username'], data=get_user1(session['username']))
    elif request.method == 'POST':
        user_name = request.form.get("user_name")
        user_pw1 = request.form.get("user_pw1")
        user_pw2 = request.form.get("user_pw2")
        user_email = request.form.get("user_email")
        user_phone = request.form.get("user_phone")
        if user_pw1 == user_pw2:
            user_pw1 = hashlib.sha224(user_pw1).hexdigest()
            sql = 'UPDATE users SET password="%s", name="%s", email="%s", phone="%s" WHERE id="%s"' % (user_pw1, user_name, user_email, user_phone, session['username'])
            db = user_db()
            db.execute(sql)
            db.commit()
            return "<script>alert('회원정보가 수정되었습니다.'); window.location='/mypage';</script>"
        else:
            return "<script>alert('입력한 비밀번호가 일치하지 않습니다.'); window.location='/mypage';</script>"

if __name__=='__main__':
    app.run(debug=True, port=2222, host='0.0.0.0')