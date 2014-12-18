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

    #extraigo informacion XML
    usuario = diccionario['account_username']
    puerto = int(diccionario['uaserver_puerto'])
    ip = diccionario['uaserver_ip']
    puerto_rtp = int(diccionario['rtpaudio_puerto'])
    ip_proxy = diccionario['regproxy_ip']
    puerto_proxy = diccionario['regproxy_puerto']
    client_address = (ip, puerto)
    #-----------------------LOG----------------------------
    
    fich_log = diccionario['log_path']
    def log(accion, linea):    
        fich = open(fich_log, "a")
        #utilizo "a" para no sobreescribir el contenido
        tiempo = time.gmtime(time.time()) #segundos en tupla
        hora = time.strftime('%Y%m%d%H%M%S', tiempo)
        line = linea.split('\r\n')
        texto = ' '.join(line)
        
        fich.write(hora + "\t" + accion + "\t" + texto + "\r\n")
     #-------------------------------------------------------   
    
    
    if METODO == "REGISTER":
    # REGISTER sip:luke@polismassa.com:puerto SIP/2.0\r\n
        try:
            OPCION_EXPIRES = int(sys.argv[3])
        except ValueError:
            print "Usage : uaclient.py config method option"
            sys.exit()

        LINE = METODO.upper() + " sip:" + usuario + ":" + str(puerto) + " SIP/2.0\r\n"
        LINE = LINE + "Expires: " + str(OPCION_EXPIRES) + "\r\n\r\n"
        
    elif METODO == "INVITE":
        #INVITE sip:receptor SIP/2.0\r\n
        OPCION_RECEPTOR = sys.argv[3] #la opcion es a quien se lo mandamos
        #excepcion si no es una cadena!!!
        LINE = METODO.upper() + " sip:" + OPCION_RECEPTOR + " SIP/2.0\r\n"
        LINE += "ContentType: application/sdp" + "\r\n\r\n"
        LINE += "v=0" + "\r\n"
        LINE += "o=" + usuario + " " + ip + "\r\n"
        LINE += "s= misesion" + "\r\n"
        LINE += "t=0" + "\r\n"
        LINE += "m= audio " + str(puerto_rtp) + " RTP" + "\r\n"  
        
    elif METODO == "BYE":
        OPCION_RECEPTOR = sys.argv[3]
        LINE = METODO.upper() + "sip:" + OPCION_RECEPTOR + " SIP/2.0\r\n"
        
    else:  #SI NO ES NINGUNO DE ESTOS METODOS
        sys.exit("Usage: python uaclient.py config method opcion")
    
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    #me tengo que atar al proxy porque es con el que intercambio datos
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ip_proxy, int(puerto_proxy)))
    
 
    
    print "Envio: " + LINE
    my_socket.send(LINE)
    accion = "Sent to " + ip_proxy +":" + puerto_proxy + ":"
    log (accion, LINE)
    
    #Excepcion en caso de establecer conexion con un puerto no abierto
    try:
        data = my_socket.recv(1024)
        print 'Recibido -- '
        print data

        #Si el proxy/registrar me contesta..
        if data == 'SIP/2.0 400 Bad Request\r\n\r\n':
            sys.exit()
        trying = "SIP/2.0 100 Trying\r\n\r\n"
        ringing = "SIP/2.0 180 Ringing\r\n\r\n"
        ok = "SIP/2.0 200 OK\r\n\r\n"
        respuesta = trying + ringing + ok
        accion = "Received from " + ip_proxy + ":" + puerto_proxy + ":"
        log (accion, respuesta)
        
        if data == respuesta:
            print "He recibido las respuestas 100,180,200 mando ACK"
            sip = " SIP/2.0\r\n\r\n"
            asentimiento = "ACK" + " sip:" + RECEPTOR + "@" + SERVER + sip
            print "Enviando: " + asentimiento
            my_socket.send(asentimiento)
         
   #ENVIO RTP?

    except (socket.error):
        print "No server listening at " + str(ip_proxy) + " port " + str(puerto_proxy)
        sys.exit()

    print "Terminando socket..."

    # Cerramos todo
    my_socket.close()
    
    print "Fin."
