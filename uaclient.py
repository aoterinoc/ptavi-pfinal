#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os


class ClienteHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.tags = ["account", "uaserver", "rtpaudio", "regproxy", "log",
                     "audio"]
        self.atributos = {
            "account": ["username"],
            "uaserver": ["ip", "puerto"],
            "rtpaudio": ["puerto"],
            "regproxy": ["ip", "puerto"],
            "log": ["path"],
            "audio": ["path"]
        }

    def startElement(self, name, attrs):
        """
        Método que se emplea al abrirse una etiqueta
        """

        if name in self.tags:
            for atributo in self.atributos[name]:
                elem = name + "_" + atributo
                self.diccionario[elem] = attrs.get(atributo, "")

    def get_tags(self):
        return self.diccionario

    #METODO LOG
    def log(self, accion, linea, fich_log):
        fich = open(fich_log, "a")
        #utilizo "a" para no sobreescribir el contenido
        tiempo = time.gmtime(time.time())  # segundos en tupla
        hora = time.strftime('%Y%m%d%H%M%S', tiempo)
        line = linea.split('\r\n')  # Quito saltos de linea
        texto = ' '.join(line)  # Transformo en espacios

        fich.write(hora + "\t" + accion + "\t" + texto + "\r\n")

if __name__ == "__main__":
    # Argumentos y errores
    if len(sys.argv) != 4 or os.path.exists(sys.argv[1]) is False:
        print "Usage : uaclient.py config method option"
        sys.exit()

    CONFIG_XML = sys.argv[1]
    metodo = sys.argv[2]
    METODO = metodo.upper()

    #OPCION[3] cambiara segun el metodo empleado

    #parte del programa smallsmilhander para parsear el XML
    parser = make_parser()
    cHandler = ClienteHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    diccionario = cHandler.get_tags()
    #log = cHandler.log((self, accion, linea, fich_log)

    #extraigo informacion XML
    usuario = diccionario['account_username']
    try:
        puerto = int(diccionario['uaserver_puerto'])
        puerto_rtp = int(diccionario['rtpaudio_puerto'])
        puerto_proxy = int(diccionario['regproxy_puerto'])
    except ValueError:
        print "Error: El puerto debe ser un entero"
        sys.exit()
    ip = diccionario['uaserver_ip']
    if ip <= "0.0.0.0" or ip >= "255.255.255.255":
        sys.exit("Error: El rango de tu IP no es válido")

    fich_log = diccionario['log_path']
    #si no se indica la IP la tomareos como 127.0.0.1 en servidor y proxy
    if ip == "":
        ip = "127.0.0.1"

    ip_proxy = diccionario['regproxy_ip']
    if ip_proxy <= "0.0.0.0" or ip_proxy >= "255.255.255.255":
        sys.exit("Error: El rango de tu IP no es válido")
    if ip_proxy == "":
        ip_proxy = "127.0.0.1"

    if METODO == "REGISTER":
    # REGISTER sip:luke@polismassa.com:puerto SIP/2.0\r\n
        try:
            OPCION_EXPIRES = int(sys.argv[3])
        except ValueError:
            print "Usage : uaclient.py config method option"
            sys.exit()

        LINE = METODO.upper() + " sip:" + usuario + ":" + str(puerto)
        LINE += " SIP/2.0\r\n"
        LINE = LINE + "Expires: " + str(OPCION_EXPIRES) + "\r\n\r\n"

    elif METODO == "INVITE":
        #INVITE sip:receptor SIP/2.0\r\n
        OPCION_RECEPTOR = sys.argv[3]  # la opcion es a quien se lo mandamos
        #excepcion si no es una cadena!!!
        LINE = METODO.upper() + " sip:" + OPCION_RECEPTOR + " SIP/2.0\r\n"
        LINE += "Content-Type: application/sdp" + "\r\n\r\n"
        LINE += "v=0" + "\r\n"
        LINE += "o=" + usuario + " " + ip + "\r\n"
        LINE += "s=misesion" + "\r\n"
        LINE += "t=0" + "\r\n"
        LINE += "m=audio " + str(puerto_rtp) + " RTP" + "\r\n\r\n"

    elif METODO == "BYE":
        OPCION_RECEPTOR = sys.argv[3]
        LINE = METODO.upper() + " sip:" + OPCION_RECEPTOR + " SIP/2.0\r\n"

    else:  # SI NO ES NINGUNO DE ESTOS METODOS
        sys.exit("Usage: python uaclient.py config method opcion")

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    #me tengo que atar al proxy porque es con el que intercambio datos
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ip_proxy, puerto_proxy))

    print "Envio: " + LINE
    my_socket.send(LINE)
    accion = "Sent to " + ip_proxy + ":" + str(puerto_proxy) + ":"

    cHandler.log(accion, LINE, fich_log)

    #Excepcion en caso de establecer conexion con un puerto no abierto
    try:
        data = my_socket.recv(1024)
        print 'Recibo del proxy -- '
        print data

        #Si el proxy/registrar me contesta..
        accion = "Received from " + ip_proxy + ":" + str(puerto_proxy) + ":"
        cHandler.log(accion, data, fich_log)

        if data == 'SIP/2.0 400 Bad Request\r\n\r\n':
            sys.exit()

        linea = data.split()

        if linea[1] == "100" and linea[4] == "180" and linea[7] == "200":
            print "He recibido las respuestas 100,180,200 mando ACK"
            sip = " SIP/2.0\r\n\r\n"
            asentimiento = "ACK" + " sip:" + OPCION_RECEPTOR + sip
            print "Enviando: " + asentimiento
            my_socket.send(asentimiento)
            accion = "Sent to " + ip_proxy + ":" + str(puerto_proxy) + ":"
            cHandler.log(accion, asentimiento, fich_log)

            print "HE MANDADO ACK, MANDO RTP"
            receptor_IP = linea[13]
            receptor_Puerto = linea[17]
            FICHERO_AUDIO = diccionario['audio_path']
            accion = "Sent to " + receptor_IP + ":" + receptor_Puerto + ":"
            data = FICHERO_AUDIO
            cHandler.log(accion, data, fich_log)
            comando_rtp = "./mp32rtp -i " + str(receptor_IP) + " -p"
            comando_rtp += str(receptor_Puerto) + " < "

            aEjecutar = comando_rtp + FICHERO_AUDIO
            os.system(aEjecutar)
            print "Se acaba la transmision de RTP"

            aEjecutar_cvlc = "cvlc rtp://" + str(receptor_IP) + ":"
            aEjecutar_cvlc += str(receptor_Puerto) + " 2> /dev/null"
            print "Vamos a ejecutar", aEjecutar_cvlc
            os.system(aEjecutar_cvlc + "&")

    except (socket.error):
        accion = "No server listening at " + str(ip_proxy) + " port "
        accion += str(puerto_proxy)
        print accion
        cHandler.log(accion, '', fich_log)
        sys.exit()

    print "Terminando socket..."

    # Cerramos todo
    my_socket.close()
    print "Fin."
