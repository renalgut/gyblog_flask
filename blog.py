from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#loginkontrol
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
       if "logged_in" in session:

           return f(*args, **kwargs)
       else:
           flash("Bu sayfaya gitmeden önce giriş yapmanız gerekiyor","danger")
           return redirect(url_for("login"))

    return decorated_function
#addarticle form
class AddarticleForm(Form):
    title = StringField("Makale Adı", validators=[validators.input_required()])
    content = TextAreaField("Makale İçeriği", validators=[validators.input_required()])
#login form
class LoginForm(Form):
    kullanici_adi = StringField("Kullanıcı Adınız", validators=[validators.input_required()])
    password = PasswordField("Şifreniz", validators=[validators.input_required()])

#register form
class RegisterForm(Form):
    isim = StringField('İsminiz', validators=[validators.input_required()])
    kullanici_adi  = StringField('Kullanıcı adınız', validators=[validators.input_required()])
    email = StringField("Email Adresi",validators=[validators.Email(message="Mail adresiniz yanlış..."),validators.input_required()])
    password = PasswordField("Şifrenizi giriniz",validators=[
        validators.input_required(message="Lütfen bir parola girin"),
        validators.equal_to("confirm",message="Parolanız uyuşmuyor..")
    ])
    confirm = PasswordField("Parolayı Doğrulayın")
#mysql bağlantısı
app = Flask(__name__)
app.secret_key = "gyblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "gyblok"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

#ana sayfa
@app.route("/")
def index():
    return render_template("index.html")
#login
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():

        username = form.kullanici_adi.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "select * from users where username=%s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            realpassword = data["password"]
            if sha256_crypt.verify(password_entered,realpassword):
                flash("Başarıyla giriş yaptınız","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor","danger")
            return redirect(url_for("login"))
        cursor.close()
        flash("Başarıyla Giriş Yaptınız...", "success")
        return redirect(url_for("index"))
    else:
        return render_template("login.html", form=form)
#articles
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles"
    data = cursor.execute(sorgu)
    if data > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

#addarticle
@app.route("/addarticle",methods = ["GET","POST"])
@login_required
def addarticle():
    form = AddarticleForm(request.form)
    if request.method == "POST":
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "insert into articles(title,author,content) values(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form=form)
#makaleara
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("articles"))
    else:
        cursor = mysql.connection.cursor()
        keyword = request.form.get("keyword")
        sorgu = "select * from articles where title like '%"+keyword+"%'"
        data = cursor.execute(sorgu)
        if data > 0:
            articles = cursor.fetchall()
            print(articles)
            return (render_template("articles.html",articles=articles))
        else:
            flash("Makale bulunamadı...","danger")
            return redirect(url_for("articles"))



#makaleguncelle
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def edit(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id=%s and author=%s"
    data = cursor.execute(sorgu, (id, session["username"]))
    if data > 0:

        if request.method == "GET":
            article = cursor.fetchone()
            form = AddarticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("edit.html",form=form)
        else:
            form = AddarticleForm(request.form)
            sorgu_update = "update articles set title=%s,content=%s where id=%s"
            cursor.execute(sorgu_update,(form.title.data,form.content.data,id))
            mysql.connection.commit()
            flash("Makale başarı ile güncellendi..","success")
            return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya düzenleme yetkiniz yok","danger")
        return redirect(url_for("dashboard"))


#makalesilme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id=%s and author=%s"
    data = cursor.execute(sorgu, (id,session["username"]))
    if data > 0:
        sorgu = "delete from articles where id=%s"
        cursor.execute(sorgu, (id,))
        mysql.connection.commit()
        flash("Makale başarıyla silindi","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya silmeye yetkiniz yok","danger")
        return redirect(url_for("dashboard"))
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id=%s"
    data = cursor.execute(sorgu, (id,))
    if data > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        flash("Böyle bir makale yok..","danger")
        return redirect(url_for("articles"))
#dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author=%s"
    data = cursor.execute(sorgu,(session["username"],))
    if data > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")
#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
#kayıt ol
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():

        name = form.isim.data
        username = form.kullanici_adi.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "insert into users(name,username,email,password) values(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

if __name__ == "__main__":
    app.run(debug=True)

