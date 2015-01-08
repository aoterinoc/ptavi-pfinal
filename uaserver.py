#!/usr/bin/python
# -*- coding: utf-8 -*-

import SocketServer
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import ClienteHandler
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
                error = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(error)
                accion = "Error: "
                err = error.split('\r\n\r\n')[0]                     
                cliente.log(accion,err, fich_log)
            
            elif metodo == "INVITE":
                accion = "Received from " + str(IP_PROXY) +":"
                accion += str(PUERTO_PROXY) + ":" 
                cliente.log(accion, line, fich_log)
                
                nombre = diccionario['account_username']
                ip = diccionario['uaserver_ip']
                #rtp_puerto = diccionario['rtpaudio_puerto']
        
                trying = "SIP/2.0 100 Trying\r\n\r\n"
                ringing = "SIP/2.0 180 Ringing\r\n\r\n"
                ok = "SIP/2.0 200 OK\r\n\r\n"
                #SDP que se manda con el 200 OK
                sdp = "ContentType: application/sdp" + "\r\n\r\n"
                sdp += "v=0" + "\r\n"                
                sdp += "o=" + nombre + " " + ip + "\r\n"
                sdp += "s=misesion" + "\r\n"
                sdp += "t=0" + "\r\n"
                sdp += "m=audio " + str(rtp_puerto) + " RTP" + "\r\n\r\n"
                cod_respuesta = trying + ringing + ok + sdp
                print "Mando al proxy --"                
                self.wfile.write(cod_respuesta)
                print cod_respuesta
                accion = "Sent to " + str(IP_PROXY) +":"
                accion += str(PUERTO_PROXY) + ":"                 
                cliente.log(accion, cod_respuesta, fich_log)
                
                #GUARDO IP Y PUERTO CLIENTE PARA MANDAR RTP
                receptor_IP = line.split('\r\n')[4].split(' ')[1]
                Dicc_Rtp['receptor_IP'] = receptor_IP
                receptor_Puerto = line.split('\r\n')[7].split(" ")[1]
                Dicc_Rtp['receptor_Puerto'] = receptor_Puerto
                print receptor_Puerto + "puerto envio RTP!!!"           
            elif metodo == "ACK":
                #El puerto y la IP lo cojo de Dicc_Rtp
                accion = "Received from " + str(IP_PROXY) +":"
                accion += str(PUERTO_PROXY) + ":" 
                cliente.log(accion, line, fich_log)
    
                print "Me llega ACK envio RTP"
                comando_rtp = "./mp32rtp -i " + Dicc_Rtp['receptor_IP'] + " -p"
                comando_rtp += Dicc_Rtp['receptor_Puerto'] + " < "
                FICHERO_AUDIO = diccionario['audio_path']
                aEjecutar = comando_rtp + FICHERO_AUDIO
                os.system(aEjecutar)    
                print "Se acaba la transmision de RTP"
                accion = "Sent to " + Dicc_Rtp['receptor_IP'] + ":" 
                accion += Dicc_Rtp['receptor_Puerto'] + ":"
                data = FICHERO_AUDIO
                cliente.log (accion, data, fich_log)
            elif metodo == "BYE":
                accion = "Received from " + str(IP_PROXY) +":"
                accion += str(PUERTO_PROXY) + ":" 
                cliente.log(accion, line, fich_log)
            
                print "Mando al proxy SIP/2.0 200 OK"
                ok = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(ok)
                accion = "Sent to " + str(IP_PROXY) +":"
                accion += str(PUERTO_PROXY) + ":" 
                cliente.log(accion, ok, fich_log)
            else:
                error = "SIP/2.0 400 Bad Request\r\n\r\n"
                self.wfile.write(error)
                accion = "Error: "
                err = error.split('\r\n\r\n')[0]                     
                cliente.log(accion,err, fich_log)                
                break

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
    cliente = ClienteHandler()

    IP_PROXY = diccionario ['regproxy_ip']
    if IP_PROXY <= "0.0.0.0" or IP_PROXY >= "255.255.255.255":
        sys.exit("Error: El rango de tu IP no es válido")
    
    SERVER_IP = diccionario['uaserver_ip']
    fich_log = diccionario['log_path']
    if SERVER_IP <= "0.0.0.0" or SERVER_IP >= "255.255.255.255":
        sys.exit("Error: El rango de tu IP no es válido")
    
    if SERVER_IP == "":
        SERVER_IP = "127.0.0.1"
    try:
        SERVER_PORT = int(diccionario['uaserver_puerto'])
        PUERTO_PROXY = int(diccionario ['regproxy_puerto'])
        rtp_puerto = int(diccionario['rtpaudio_puerto'])
    except ValueError:
        print "Error: El puerto debe ser un entero"  
    
    print SERVER_IP
    print SERVER_PORT
  # Creamos servidor de eco y escuchamos
    try:
        serv = SocketServer.UDPServer((SERVER_IP, SERVER_PORT), EchoHandler)
        print "Listening..."
        accion = 'Starting...'
        cliente.log(accion, '', fich_log)
        serv.serve_forever()
    except(KeyboardInterrupt):
        mensaje = "Programa interrumpido por el usuario"
        print mensaje
        accion = "Finishing\r\n"
        cliente.log(accion, "", fich_log)


