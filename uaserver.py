#!/usr/bin/python
# -*- coding: utf-8 -*-

import SocketServer
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import os
import os.path
import time

Metodos_Aceptados = [ "INVITE", "ACK", "BYE"]
Dicc_Rtp ={}
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

class EchoHandler(SocketServer.DatagramRequestHandler):
    #MIRO LO QUE RECIBO Y MANDO CODIGO DE RESPUESTA
    def handle(self):
        while 1:
            # Lee linea a lina lo que llega del cliente

            line = self.rfile.read()
            #Comprobamos si hay linea en blanco
            if not line:
                break
            print "Recibo del proxy -- "
            print line
            
            linea = line.split('\r\n')
            print linea
            
            #miro nombre metodo
            lin = linea[0].split() 
            metodo = lin[0]
            print metodo
            
            if metodo not in Metodos_Aceptados:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")

            if metodo == "INVITE":

                nombre = diccionario['account_username']
                ip = diccionario['uaserver_ip']
                rtp_puerto = diccionario['rtpaudio_puerto']
        
                trying = "SIP/2.0 100 Trying\r\n\r\n"
                ringing = "SIP/2.0 180 Ringing\r\n\r\n"
                ok = "SIP/2.0 200 OK\r\n\r\n"
                #SDP que se manda con el 200 OK
                sdp = "ContentType: application/sdp" + "\r\n\r\n"
                sdp += "v=0" + "\r\n"                
                sdp += "o=" + nombre + " " + ip + "\r\n"
                sdp += "s=misesion" + "\r\n"
                sdp += "t=0" + "\r\n"
                sdp += "m=audio " + rtp_puerto + " RTP" + "\r\n\r\n"
                cod_respuesta = trying + ringing + ok + sdp
                print "Mando al proxy --"
                
                self.wfile.write(cod_respuesta)
                print cod_respuesta
                #GUARDO IP Y PUERTO CLIENTE PARA MANDAR RTP
                receptor_IP = line.split('\r\n')[4].split(' ')[1]
                Dicc_Rtp['receptor_IP'] = receptor_IP
                receptor_Puerto = line.split('\r\n')[7].split(" ")[1]
                Dicc_Rtp['receptor_Puerto'] = receptor_Puerto
                            
            if metodo == "ACK":
                #El puerto y la IP lo cojo de Dicc_Rtp
                
                print "Me llega ACK envio RTP"
                comando_rtp = "./mp32rtp -i " + Dicc_Rtp['receptor_IP'] + " -p"
                comando_rtp += Dicc_Rtp['receptor_Puerto'] + " < "
                FICHERO_AUDIO = diccionario['audio_path']
                aEjecutar = comando_rtp + FICHERO_AUDIO
                os.system(aEjecutar)    
                print "Se acaba la transmision de RTP"
            
            if metodo == "BYE":
                print "Mando al proxy SIP/2.0 200 OK"
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                
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
    if SERVER_IP == "":
        SERVER_IP = "127.0.0.1"
        print "IP POR DEFECTO"
    SERVER_PORT = diccionario['uaserver_puerto']
    print SERVER_IP
    print SERVER_PORT
  # Creamos servidor de eco y escuchamos
    
    serv = SocketServer.UDPServer((SERVER_IP, int(SERVER_PORT)), EchoHandler)
    print "Listening..."
    serv.serve_forever()
    
