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
import SocketServer

registro={}
METODOS_ACEPTADOS = ["INVITE", "BYE", "ACK"]

class ProxyHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.tags = ["server", "database", "log"]
        self.atributos = {
            "server": ["name","ip"],
            "database": ["path"],
            "log": ["path"],
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
    
    #REGISTRO de USUARIOS
    """
    def register2file(self):
        
        Escribe en un fichero los usuarios registrados o dados de baja
        con sus valores.
        

        fich = open("registered.txt", "w")
        fich.write("User" + "\t" + "IP" + "\t" + "Expires" + "\r\n")
        for clave in registro:
            tiempo = time.gmtime(registro[clave][2])
            hora = time.strftime('%Y-%m-%d %H:%M:%S', tiempo)
            fich.write(clave+"\t"+registro[clave][0]+"\t"+hora+"\r\n")
        fich.close()
       """
       #BORRO USUARIOS CADUCADOS

        
            
#Implementación codigos de respuesta

class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    

    def handle(self):
       
        
        while 1:
            # Lee linea a lina lo que llega del cliente

            line = self.rfile.read()

            #Comprobamos si hay linea en blanco
            if not line:
                break
            print "Recibo del cliente"
            print line
            if line != "":
                sip = "SIP/2.0\r\n\r\n"
                #miro aqui el codigo 400 xq el split me corta los \r\n
                if 'sip:' not in line or sip not in line or "@" not in line:
                    self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")
                    break
                    #Si el cliente me manda mal el mensaje no le mando nada mas
                #troceamos la linea que nos llega
                line = line.split()
                if line[0] == "REGISTER":
                    self.wfile.write(" SIP/2.0 200 OK\r\n\r\n")
                line[1] = line[1].split(":")
                
                #Solo metemos en el diccionario si el expires no es 0
                #Me quedo con el valor de expires
                #if valor de expires != "0":
                    #hora_s = time.time()
                    #registro[line[1][1]] = [str(self.client_address[0]), line[4], hora_s]
              #  else:
                #Si un usuario se da de baja y esta en el registro, le borramos
              #  if line[1][1] in registro:
              #      del registro[line[1][1]]
              #      self.wfile.write(" SIP2.0 200 OK\r\n\r\n")
                #Borro usuarios caducados y escribimos en el fichero
              #  self.borrar_caducados(registro)
              #  self.register2file()
            print registro
            if line[0] == "INVITE":
                trying = "SIP/2.0 100 Trying\r\n\r\n"
                ringing = "SIP/2.0 180 Ringing\r\n\r\n"
                ok = "SIP/2.0 200 OK\r\n\r\n"
                #SDP que se manda con el 200 OK
                sdp = "ContentType: application/sdp" + "\r\n\r\n"
                sdp += "v=0" + "\r\n"
                nombre = diccionario['server_name']
                ip = diccionario['server_ip']
                sdp += "o=" + nombre + " " + ip + "\r\n"
                sdp += "s= misesion" + "\r\n"
                sdp += "t=0" + "\r\n"
                cod_respuesta = trying + ringing + ok + sdp
                self.wfile.write(cod_respuesta)
            
            if line[0] not in METODOS_ACEPTADOS:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            #404 USER NOT FOUND USUARIO NO REGISTRADO
            if line[0] == "BYE":
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")









if __name__ == "__main__":
    # Dirección IP, puerto y mensaje para servidor
    if len(sys.argv) != 2:
        print "Usage: python proxy_registrar.py config"
        sys.exit()
    FICH_XML = sys.argv[1]
    
    parser = make_parser()
    cHandler = ProxyHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(FICH_XML))
    diccionario = cHandler.get_tags()
    
    #puerto = int(diccionario['server_port'])
    nombre = diccionario['server_name']
    IP_SERV = diccionario['server_ip']
    #PORT = int(diccionario['server_puerto'])
    serv = SocketServer.UDPServer((IP_SERV, 2020), ProxyHandler)
    print "Server " + nombre + " listening at port " + "PUERTO"  + "..."
   
    serv.serve_forever()




