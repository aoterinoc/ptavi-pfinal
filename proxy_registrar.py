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
import uaclient 

registro={}
METODOS_ACEPTADOS = ["REGISTER" , "INVITE", "BYE", "ACK"]

class ProxyHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.tags = ["server", "database", "log"]
        self.atributos = {
            "server": ["name","ip", "puerto"],
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

  
class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    #---------BASE DE DATOS---------
    
    def register2file(self):
        """
        Listado con los usuarios registrados en cada momento.
        """

        fich = open("registered.txt", "w")
        escribe = "User" + "\t" + "IP" + "\t" + "Port" + "\t"
        escribe += "Date" + "\t" + "Expires" + "\r\n"
        fich.write(escribe)
        for clave in registro:
            tiempo = time.gmtime(float(registro[clave][3]))
            hora = time.strftime('%Y%m%d%H%M%S', tiempo)
            linea = clave + "\t" + str(registro[clave][1]) + "\t" + str(registro[clave][2]) + "\t"
            linea += hora + "\t" + str(registro[clave][4]) + "\r\n"
            fich.write(linea)
        fich.close()
    
    def borrar_caducados(self, registro):
        """
        Gestiona la caducidad de los usuarios registrados
        """
        list_caducados = []
        for clave in registro:
            hora_entrada = registro[clave][3]
            expires = registro[clave][4]
            tiemp_a = time.time()
            if int(hora_entrada) + int(expires) <= tiemp_a:
                list_caducados.append(clave)
        for clave in list_caducados:
            del registro[clave]
    
    def handle(self):
       self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       #NECESARIO?? COMO ESPERO SI NO??
       while 1:
            # Lee linea a lina lo que llega del cliente

            line = self.rfile.read()

            #Comprobamos si hay linea en blanco
            if not line:
                break
            print "Recibo del cliente"
            print line
            """
            ip_client = self.client_address[0]
            port_client = self.client_address[1]
            accion = "Received from " + str(ip_client) + ":" + str(port_client) + ":"
            uaclient.self.log(accion, line)
            """
            """
            ¿COMO COMPRUEBO SI EL MENSAJE ESTA BIEN FORMADO?
            if line != "":
                sip = "SIP/2.0\r\n\r\n"
                #miro aqui el codigo 400 xq el split me corta los \r\n
                if 'sip:' not in line or sip not in line or "@" not in line:
                    self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")
                    break
            """
            linea = line.split('\r\n')
            print linea
            
            #miro nombre metodo
            lin = linea[0].split() 
            metodo = lin[0]
            print metodo
            
           
            #COMPROBAR PETICION BIEN FORMADA!!!#
            if metodo == "REGISTER":
                linea = line.split('\r\n')
                print linea
                #saco valor expires
                expires = linea
                expires = linea[1].split(':')
                expires = int(expires[1])
                print expires
                linea = linea[0].split() 
                direcc = linea[1]
                direcc = direcc.split(':')
                puerto = direcc[2]
                
                direcc = direcc[1]
                print direcc
                #quiero la IP y puerto del cliente
                cli_addr = self.client_address
                self.wfile.write(" SIP/2.0 200 OK\r\n\r\n")                
            #Solo metemos en el diccionario si el expires no es 0
                if expires != "0":
                    hora_s = time.time()
                    #guardo user, ip , puerto, date y expires
                    #client_address me da la ip y puerto del que me envia .
                    registro[direcc] = [direcc,str(cli_addr[0]), str(puerto), hora_s, expires]
                    #falta IP!!
                if expires == "0":
                #Si un usuario se da de baja y esta en el registro, le borramos
                    if direcc in registro:
                        del registro[direcc]
                        print "Usuario dado de baja"                   
                        self.wfile.write(" SIP2.0 200 OK\r\n\r\n")
                #Borro usuarios caducados y escribimos en el fichero
                
                self.borrar_caducados(registro)
                self.register2file()
                print registro
            
            if metodo not in METODOS_ACEPTADOS:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            
            if metodo == "INVITE":
                #nombre del cliente que manda el register
                nom_client = linea[4].split('=')
                nom_client = nom_client[1].split(' ')
                nom_client = nom_client[0]
                print nom_client
                #Para saber a quien envio el invite
                usuario_inv = linea[0].split()
                usuario_inv = usuario_inv[1].split(':')[1]
                print usuario_inv
                
                
                if nom_client in registro:
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
                    sdp += "m=audio" + "PONER PUERTO RTP" +"\r\n\r\n"
                    cod_respuesta = trying + ringing + ok + sdp
                    self.wfile.write(cod_respuesta)

                    
                    
                    #self.my_socket.connect((ip_server, puerto_server)
                    #self.my_socket.send(reenviar)
               
                    try:
                        data = self.my_socket.recv(1024)
                    except (socket.error):
                        print "No server listening at "  + " port " 
                        sys.exit()
                if usuario_inv not in registro:
                    self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")
                    #si no esta en el registro
                    print "cliente que manda Invite sin antes registrarse"  
                if nom_client not in registro:
                    error = "Debes mandar un Register antes de hacer Invite"
                    self.wfile.write(error)
              
                

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
    
    IP = diccionario['server_ip']
    #En caso de no indicar la IP se utiliza la 127.0.0.1
    if IP == "":
        IP = "127.0.0.1"
    


    PUERTO = diccionario['server_puerto']
    NAME = diccionario['server_name']
    #Instanciamos EchoHandler
    serv = SocketServer.UDPServer((IP, int(PUERTO)), EchoHandler)
   
    print "Server " + NAME + " listening at port " + PUERTO
    serv.serve_forever()   



