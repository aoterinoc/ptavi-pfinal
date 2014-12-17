#!/usr/bin/python
# -*- coding: utf-8 -*-

import SocketServer
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import os
import os.path
import time

class ServidorHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
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
        
        if name in self.tags:
            for atributo in self.atributos[name]:
                elem = name + "_" + atributo
                self.diccionario[elem] = attrs.get(atributo, "")

    def get_tags(self):
        return self.diccionario

    #MIRO LO QUE RECIBO Y MANDO CODIGO DE RESPUESTA
    def handle(self):
        while 1:
            # Lee linea a lina lo que llega del cliente

            line = self.rfile.read()

            #Comprobamos si hay linea en blanco
            if not line:
                break
            print "Recibo del cliente"
            print line
            
if __name__ == "__main__":
    # Argumentos y errores
    if len(sys.argv) !=2  or os.path.exists(sys.argv[1]) is False:
        print "Usage : uaclient.py config method option"
        sys.exit()

    CONFIG_XML = sys.argv[1]
     
    #parte del programa smallsmilhander para parsear el XML
    parser = make_parser()
    cHandler = ServidorHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    diccionario = cHandler.get_tags()

    SERVER_IP = diccionario['uaserver_ip']
    SERVER_PORT = diccionario['uaserver_puerto']
  # Creamos servidor de eco y escuchamos
    serv = SocketServer.UDPServer((SERVER_IP, int(SERVER_PORT)), ServidorHandler)
    print "Listening..."
    serv.serve_forever()
