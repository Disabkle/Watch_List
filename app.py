from flask import Flask,escape,render_template

from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click

from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin

# 用户登录/../.../../.
from flask_login import LoginManager # 用户管理
from flask_login import login_user # 用户入
from flask_login import logout_user # 用户登出
from flask_login import login_required # 视图保护
from flask_login import current_user # 当前用户

from flask import request # 请求
from flask import url_for # 定位
from flask import redirect # 重定向
from flask import flash

# 
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


# 实例化app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# secret_key 密钥
app.config['SECRET_KEY'] = 'dev' # 等同于 app.secret_key = 'dev'
db = SQLAlchemy(app)
movies = [
         {'title': '利刃出鞘', 'year': '2019'},     
         {'title': '看不见的客人', 'year': '2018'},     
         {'title': '翻译疑云', 'year': '2020'},     
         {'title': '误杀', 'year': '2020'},     
         {'title': '极限逃生', 'year': '2019'},     
         {'title': '寄生虫', 'year': '2019'},     
         {'title': '安娜', 'year': '2019'},     
         {'title': '黑暗面', 'year': '2018'},     
         {'title': '消失的爱人', 'year': '2016'},     
         {'title': '天注定', 'year': '2012'}]


# 用户登入
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user) # 登入用户
            flash('Login success.')
            return redirect(url_for('index')) # 重定向到主页
        flash('Invalid username or password.') # 如果验证失败，显示错误消息
        return redirect(url_for('login')) # 重定向回登录页面
    return render_template('login.html')

# 用户登出
@app.route('/logout')
@login_required # 用于视图保护，后面会介绍
def logout():
    logout_user() # 登出用户
    flash('退出系统')
    return redirect(url_for('index')) # 重定向回首页

# 用户设置
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('无效的输入')
            return redirect(url_for('settings'))
        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('设置已更新')
        return redirect(url_for('index'))
    return render_template('settings.html')

# 用户
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id): # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id)) # 用 ID 作为 User 模型的主键查询对应的用户
    return user # 返回用户对象

login_manager.login_view = 'login'



# 404错误
@app.errorhandler(404) # 传入要处理的错误代码
def page_not_found(e): # 接受异常对象作为参数
    user = User.query.first()
    return render_template('404.html'), 404 # 返回模板和状态码

@app.context_processor
def inject_user(): # 函数名可以随意修改
    user = User.query.first()
    return dict(user=user) # 需要返回字典，等同于 return {'user': user}

# 注册为命令
@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.') # 提示


@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()
    movies = [
    {'title': '利刃出鞘', 'year': '2019'},
    {'title': '看不见的客人', 'year': '2018'},
    {'title': '翻译疑云', 'year': '2020'},
    {'title': '误杀', 'year': '2020'},
    {'title': '极限逃生', 'year': '2019'},
    {'title': '寄生虫', 'year': '2019'},
    {'title': '安娜', 'year': '2019'},
    {'title': '黑暗面', 'year': '2018'},
    {'title': '消失的爱人', 'year': '2016'},
    {'title': '天注定', 'year': '2012'},
    ]
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done.')

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=False, confirmation_prompt=False, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')


class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20)) # 用户名
    password_hash = db.Column(db.String(128)) # 密码散列值
    def set_password(self, password): # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password) # 生成的密码存到对应字段
    def validate_password(self, password): # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password) # 返回布尔值

# movie
class Movie(db.Model):
    # 主键
    id = db.Column(db.Integer,primary_key=True)
    # title
    title = db.Column(db.String(60))
    # year
    year = db.Column(db.String)


# @app.route('/')
# def index():
#     user = User.query.first() # 读取用户记录
#     movies = Movie.query.all() # 读取所有电影记录
#     return render_template('index.html', movies=movies)



# …中间省略的代码
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST': # 判断是否是 POST 请求
        if not current_user.is_authenticated: # 如果当前用户未认证
            return redirect(url_for('index')) # 重定向到主页
        # 获取表单数据
        title = request.form.get('title') # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') # 显示错误提示
            return redirect(url_for('index')) # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year) # 创建记录
        db.session.add(movie) # 添加到数据库会话
        db.session.commit() # 提交数据库会话
        flash('Item created.') # 显示成功创建的提示
        return redirect(url_for('index')) # 重定向回主页
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))
    return render_template('edit.html', movie=movie)

@app.route('/movie/delete/<int:movie_id>', methods=['POST']) # 限定只接受 POST 请求
@login_required # 登录保护
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id) # 获取电影记录
    db.session.delete(movie) # 删除对应的记录
    db.session.commit() # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index')) # 重定向回主页

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)
