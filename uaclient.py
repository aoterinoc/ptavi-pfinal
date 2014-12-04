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

class SmallSMILHandler(ContentHandler):

    def __init__(self):
        self.etiquetas = []
        self.tags = ["account", "uaserver", "rtpaudio", "regproxy", "log", "audio"]
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

        self.diccionario = {}
        if name in self.tags:
            self.diccionario['etiqueta'] = name
            for atributo in self.atributos[name]:
                self.diccionario[atributo] = attrs.get(atributo, "")
            self.etiquetas.append(self.diccionario)

    def get_tags(self):
        return self.etiquetas

if __name__ == "__main__":
    # Dirección IP, puerto y mensaje para servidor
    if len(sys.argv) != 4:
        print "Usage : uaclient.py config method option"
        sys.exit()
    CONFIG_XML = sys.argv[1]
    METODO = sys.argv[2]
    #OPCION cambiara segun el metodo empleado
     
    #parte del programa smallsmilhander para parsear el xml
    parser = make_parser()
    cHandler = SmallSMILHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    diccionario = cHandler.get_tags()

    #tengo que crear el log para ir registrando los distintos metodos

    usuario = diccionario['username']
    if METODO == "REGISTER":
    # REGISTER sip:luke@polismassa.com SIP/2.0\r\n\r\n
        OPCION_EXPIRES = sys.argv[3]
        LINE = METODO.upper() + " sip:" + usuario + " SIP/2.0\r\n"
        LINE = LINE + "Expires: " + str(T_EXPI) + "\r\n\r\n"

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #my_socket.connect((193.147.73, 5555)) #!!!!!!!!!!!!!
    
    elif METODO == "INVITE":
        #INVITE sip:receptor SIP/2.0\r\n\r\n
        OPCION_RECEPTOR = sys.argv[3] #la opcion es a quien se lo mandamos
        LINE = "INVITE sip:" + OPCION_RECEPTO + " SIP/2.0\r\n"
        LINE += "ContentType: application/sdp" + "\r\n\r\n"
        LINE += "v=0" + "\r\n"
        LINE += "o=" + name + " " + ip + "\r\n"
        LINE += "s= misesion" + "\r\n"
        LINE += "t=0" + "\r\n"
        LINE += "m= audio " + puerto_rtp + " RTP" + "\r\n"
    elif METODO == "BYE":
        OPCION_RECEPTOR = sys.argv[3]
        LINE = "BYE sip:" + OPCION_RECEPTOR + " SIP/2.0\r\n"
    print usuario
    print LINE
    print "Enviando: " + LINE
    my_socket.send(LINE + '\r\n')

    #Excepcion en caso de establecer conexion con un puerto no abierto
    try:
        data = my_socket.recv(1024)
        print 'Recibido -- '
        print data


    except (socket.error):
        print "No server listening at " + str(SERVER) + " port " + str(PORT)
        sys.exit()

    print "Terminando socket..."

    # Cerramos todo
    my_socket.close()
    print "Fin."
