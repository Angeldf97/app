from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template, redirect, request, url_for, session
import time
from datetime import datetime
import pymongo
import bcrypt
import threading
from beebotte import *
import sys
from urllib.request import urlopen

def hilo():
    while True:
        r = requests.get('https://es.investing.com/currencies/eur-usd') #GET de la pagina que tiene el dato
        soup = BeautifulSoup(r.text, 'lxml') #COnversión al objeto de tipo soup
        name=soup.find('span', class_='text-2xl').get_text(strip=True) #busqueda del dato que nos interesa
        myclient = pymongo.MongoClient("mongodb://localhost:27017/") #Conexión con la BBDD local
        mydb = myclient["mydatabase"] #crear base de datos
        mycol = mydb["EURO-DOLLAR"] #crear coleccion BBDD
        mydict = { "FECHA" : datetime.now() , "VALOR" : name } #creamos objeto tipo diccionario
        y = mycol.insert_one(mydict) #insertamos el objeto diccionario en la colección EURO-DOLLAR BBDD
        bclient = BBT( token='token_H24rjoPXwQm0cSjD') #nos loggeamos en la bbdd de internet beebotte
        res1 = Resource(bclient,'dev','res1') #creamos un recurso
        res1.write(name) #escribimos el datos en la bbdd
        name = float(name.replace(',', '.')) #reemplazamos como por punto
        name = str(name) #convertimos a string
        print(name)
        #bclient.write('dev', 'res1',  name)
        f = urlopen('https://api.thingspeak.com/update?api_key=V53U5YVG3NEJN1SB&field1=' + name) #metemos el dato en la BBDD de thingspeak
        time.sleep(10)


email_user = " " #variable para guardar el usuario que se ve en la pagina cuando te logeas
num = 0 #variable para controlar el numero de veces que el usuario pide la media
num_bbdd_local = 0
app = Flask(__name__) 
t = threading.Thread(target=hilo) #creamos un hilo para guardar cada 120 segundos un dato de la pagina web
t.start() #empieza el hilo

#salida de los usuarios que está loggeados
@app.route("/logout", methods=['GET'])
def logout():
  if " " in globals()["email_user"]: #comprobamos que hay algun usuario loggeado
    return '<p>user already logged out</p>'  
  else: 
    globals()["email_user"] = " "
    globals()["num"] = 0
    return render_template('logoutpage2.html'); #devolvemos la pagina en custion


#devuelve la pagina para entrada de los usuario
@app.route("/entrada", methods=['GET'])
def entrada():
    return render_template('entrada.html') #devolvemos la pagina en cuestion


#devuelve el html de la pagina de registro de usuarios
@app.route("/login", methods=['GET'])
def login():
     return render_template("loginpage3.html") #devolvemos la pagina en cuestion

#devuelve el html de la pagina de registro de usuarios
@app.route("/umbral_historico", methods=['GET'])
def umbral_historico():
     return render_template("umbral_historico.html") #devolvemos la pagina en cuestion


#metodo POST para el formulario de registro de usuarios
@app.route("/success", methods=['POST'])
def success():
    if request.method == "POST":
        myclient1 = pymongo.MongoClient("mongodb://localhost:27017/") #conexión con la BBDD
        mydb1 = myclient1["mydatabase"] 
        mycol1 = mydb1["LOGIN"]
        email=request.form["email"] #recoleccion del email del usuario, con el que se va a registrar
        if mycol1.find_one({"EMAIL" : email}) is None: #Comprobamos que el usuario no está registrado
            password = request.form["pass"] #recolectamos la password de el usurio con la que entrará mas adelante
            password = password.encode() #codificamos la password
            globals()["sal"] = bcrypt.gensalt() #Creo la sal
            password_hasheada = bcrypt.hashpw(password, globals()["sal"]) #hasheamos la password
            mydict1 = { "EMAIL":email, "USERNAME":request.form["username"], "PASSWORD":password_hasheada} #creamos diccionario con los datos que ha metido el usuario en el formulario
            x = mycol1.insert_one(mydict1) #insertamos el diccionario en la BBDD
            globals()["email_user"] = x.inserted_id #Guardamos el ID que hemos insertado en una variable global
            for globals()["email_user"] in  mycol1.find({"_id" : x.inserted_id}, {"_id": 0,  "USERNAME": 1 }): #buscamos en la BBDD según el id que acabamos de insertar el email del usuario
                print("")
            globals()["email_user"]=globals()["email_user"]['USERNAME'] #guardamos SOLO el campo USERNAME del diccionario que ha devuelto la función find
            return redirect(url_for("hello")) #nos redirecciona a la pagina principal
        else:
            return  '<p>USUARIO YA REGISTRADO</p>' #si el usuario ya está registrado, te devuelve un pagina donde aparece que ya está registrado


#METODO POST para formulario de entrada de usuarios
@app.route("/success_entrada", methods=['POST'])
def success_entrada():
    if request.method == "POST":
        myclient1 = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb1 = myclient1["mydatabase"]
        mycol1 = mydb1["LOGIN"]
        email=request.form['email'] #recogemos el email
        if mycol1.find_one({"EMAIL" : email}) is None: #comprobamos si el email está en la BBDD
            return '<p>USUARIO NO REGISTRADO</p>' #Si no está sacamos el mensaje anterior
        else:
            password=request.form['pass'] #Recolectamos la password que ha metido el usuario en el formulario
            for password_devuelto in mycol1.find({"EMAIL" : email}, {"_id": 0,  "PASSWORD": 1, "USERNAME": 1 }): #Buscamos el usuario y la contraseña en la BBDD según el email que ha introducido en el formulario 
                 print("")
            if bcrypt.checkpw(password.encode(), password_devuelto['PASSWORD']): #Se compara el password que ha introducido el usuario en el formulario y el que nos ha devuelto la BBDD
                globals()["email_user"]=password_devuelto['USERNAME'] #Si conincide el password, nos loggeamos
                return redirect(url_for("hello"))
            else:
                return '<p>CONTRASEÑA INCORRECTA</p>'  #Si no coincide no nos loggeamos

#metodo post para sacar la media por pantalla de la base de datos local.
@app.route("/success_media", methods=['POST']) 
def success_media(): 
    i=0 #contador para sacar la media
    datos_aux=0 #variable auxiliar para hacer la media
    if request.method == "POST":
        if email_user == " ":
            return '<p>Primero debes meter tus credenciales</p>'
        else:
            globals()["num_bbdd_local"]=globals()["num_bbdd_local"]+1
            myclient1 = pymongo.MongoClient("mongodb://localhost:27017/") #conexión con la base de datos
            mydb1 = myclient1["mydatabase"] #identificamos la base de datos
            mycol1 = mydb1["EURO-DOLLAR"] #objeto que refiere a la coleccion en la que guardamos
            for datos in  mycol1.find({}, {"_id":0 ,"VALOR": 1 }): #obtención de todos los valores guardados
                aux=datos["VALOR"].replace(',','.')
                datos_aux+=float(aux)
                i=i+1
            media = datos_aux/i
            return '<p>media: ' + str(media) + ' Has pedido la media un total de '+str(num_bbdd_local) +' veces<p>'

#metodo post para sacar la media por pantalla de la base de datos de Beebotte
@app.route("/beebotte", methods=['POST'])
def success_media_internet():
    i=0 #contador para sacar la media
    datos_aux=0 #variable auxiliar para hacer la media
    if request.method == "POST":
        if email_user == " ": #Comprobamos que esta loggeado el usuario para dejarle hacer la media
            return '<p>Primero debes meter tus credenciales</p>' 
        else: #si esta logeado entramos aqui
            globals()["num"]=globals()["num"]+1 #contamos uno mas, para ver las veces que ha pedido la media
            bclient = BBT( token='token_H24rjoPXwQm0cSjD') #nos autenticamos con la BBDD de internet
            res1 = Resource(bclient,'dev','res1') #creamos un recurso
            records = bclient.read('dev', 'res1', limit = 100) #leemos 100 datos de la base de datos
            for records_aux in records:
                datos_aux+=float(records_aux["data"].replace(',','.')) #recorremos la lista y reemplazamos la coma por el punto. Pasamos de string a float. Se accede solo al dato
                i=i+1 #aumentamos el contador para leer los datos que haya, como mucho 100
            media = datos_aux/i #hacemos la media
            return '<p>media: ' + str(media) + ' Has pedido la media un total de '+str(num) +' veces<p>' #retornamos la media.

#Metodo POST para leer datos de thingspeak y hacer la media
@app.route("/thingspeak", methods=['POST'])
def success_media_internet2():
    i=0 #contador para sacar la media
    datos_aux=0 #variable auxiliar para hacer la media
    if request.method == "POST":
        if email_user == " ": #Comprobamos que esta loggeado el usuario para dejarle hacer la media
            return '<p>Primero debes meter tus credenciales</p>'
        else: #si esta logeado entramos aqui
            globals()["num"]=globals()["num"]+1 #contador de veces que se cuenta la media
            msg=requests.get("https://thingspeak.com/channels/1910541/fields/1.json?api_key=GSIZSDQZHV4U7328&results=10") #leemos los 10 ultimos datos de la BBDD
            json_data = json.loads(msg.text) #convertimos el mensaje a dict con JSON
            while(i<10):
                datos_aux += float(json_data["feeds"][i]["field1"].replace(',', '.')) 
                i=i+1
            media = datos_aux/i #guardamos la media
            return "<p>media: " + str(media) + ' Has pedido la media un total de ' + str(num) + ' veces<p>' #retornamos la media y 

#Metodo POST para ver graficas  de thingspeak
@app.route("/graficas", methods=['POST'])
def graficas():
    if request.method == "POST":
        if email_user == " ": #Comprobamos que esta loggeado el usuario para dejarle acceder a las graficas
            return '<p>Primero debes meter tus credenciales</p>'
        else:
            return redirect("https://thingspeak.com/channels/1910541/charts/1?bgcolor=%23ffffff&color=%23d62020&dynamic=true&results=60&timescale=10&type=line&yaxismax=1&yaxismin=0") #redirigimos a la base de datos

    
#Metodo POST para ver los valores que superan el umbral historico
@app.route("/umbral_historico_post", methods=['POST'])
def umbral_historico_post():
    my_list = []
    fechas = []
    i=0
    j=0
    if request.method == "POST":
        myclient1 = pymongo.MongoClient("mongodb://localhost:27017/") #conexión con la base de datos
        mydb1 = myclient1["mydatabase"] #identificamos la base de datos
        mycol1 = mydb1["EURO-DOLLAR"] #objeto que refiere a la coleccion en la que guardamos
        umbral_historico=float(request.form['umbral_historico'].replace(',','.'))
        for datos in  mycol1.find({}, {"_id":0 ,"VALOR": 1, "FECHA": 1 }): #obtención de todos los valores guardados
            aux=datos["VALOR"].replace(',','.')
            aux_fecha=datos["FECHA"]
            fechas.append(aux_fecha)
            my_list.append(float(aux))
            i+=1
        while(j<len(my_list)):
            if my_list[j]<umbral_historico:
                my_list.pop(j)
                fechas.pop(j)
                j-=1
            j+=1
        return '<h1>Umbral: '+str(umbral_historico)+'</h1>'+'<p>'+str(fechas[len(fechas)-1])+' : ' + str(my_list[len(my_list)-1])+ '</p> '+'<p>' +str(fechas[len(fechas)-1])+' : '  + str(my_list[len(my_list)-2])+ '</p> ' + '<p>' + str(fechas[len(fechas)-3])+' : '  + str(my_list[len(my_list)-3])+ '</p>'  + '<p>' + str(fechas[len(fechas)-1]) +' : ' +str(my_list[len(my_list)-4])+'</p>'  +'<p>'+ str(fechas[len(fechas)-1])+' : '  + str(my_list[len(my_list)-5]) + '</p>'
#GET de la página principal
@app.route("/", methods=['GET'])
def hello():
    r = requests.get('https://es.investing.com/currencies/eur-usd') #GET de la pagina que tiene el dato
    soup = BeautifulSoup(r.text, 'lxml') #COnversión al objeto de tipo soup
    name=soup.find('span', class_='text-2xl').get_text(strip=True) #busqueda del dato que nos interesa
    myclient = pymongo.MongoClient("mongodb://localhost:27017/") #Conexión con la BBDD local
    mydb = myclient["mydatabase"] #crear base de datos
    mycol = mydb["EURO-DOLLAR"] #crear coleccion BBDD
    mydict = { "FECHA" : datetime.now() , "VALOR" : name } #creamos objeto tipo diccionario
    y = mycol.insert_one(mydict) #insertamos el objeto diccionario en la colección EURO-DOLLAR BBDD 
    return render_template("homepage2.html", name=name, email_user="Bienvenido "+email_user) #devuelve el html de la pagina principal


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False) #corremos el servidor
