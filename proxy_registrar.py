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
from uaclient import ClienteHandler


registro = {}  # Registro proxy usuarios
METODOS_ACEPTADOS = ["REGISTER", "INVITE", "BYE", "ACK"]


class ProxyHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.tags = ["server", "database", "log"]
        self.atributos = {
            "server": ["name", "ip", "puerto"],
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
    # ---------BASE DE DATOS---------

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
            linea = clave + "\t" + str(registro[clave][1]) + "\t"
            linea += str(registro[clave][2]) + "\t"
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

        while 1:
            # Lee linea a lina lo que llega del cliente

            line = self.rfile.read()

            #Comprobamos si hay linea en blanco
            if not line:
                break
            print "Recibo del cliente"
            print line
            #client_address me da la ip y puerto del que me envia .
            IP_C = self.client_address[0]
            port_client = self.client_address[1]

            linea = line.split('\r\n')
   
            #miro nombre metodo
            lin = linea[0].split()
            metodo = lin[0]
            if metodo == "REGISTER":
                sip = "SIP/2.0"
                li = linea[0]

                if 'sip:' not in li or sip not in li or "@" not in li:
                    error = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(error)
                    accion = 'Error: '
                    error = error + str(IP_C) + ':' + str(port_client) + ':'
                    cliente.log(accion, error, fich_log)
                    break
                    #Si el cliente me manda mal el mensaje no le mando nada mas

                linea = line.split('\r\n')

                #saco valor expires,puerto y dirección server
                expires = linea[1].split(':')
                expires = int(expires[1])
                linea = linea[0].split()
                direcc = linea[1]
                direcc = direcc.split(':')
                puerto = direcc[2]
                direcc = direcc[1]

                accion = "Received from " + str(IP_C) + ":" + str(port_client)
                accion += ":"
                cliente.log(accion, line, fich_log)
                # Mando 200 OK por Registrar
                ok = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(ok)
                accion = "Sent to " + str(IP_C) + ":" + str(port_client) + ":"
                cliente.log(accion, ok, fich_log)

                 #Solo metemos en el diccionario si el expires no es 0
                if expires != "0":
                    hora_s = time.time()
                    #guardo user, IP_C , puerto, date y expires
                    registro[direcc] = [direcc, IP_C, str(puerto), hora_s,
                                        expires]

                if expires == "0":
                #Si un usuario se da de baja y esta en el registro, le borramos
                    if direcc in registro:
                        del registro[direcc]
                        print "Usuario dado de baja"
                        ok = "SIP/2.0 200 OK\r\n\r\n"
                        self.wfile.write(ok)
                        accion = "Sent to " + str(IP_C) + ":"
                        accion += str(port_client) + ":"
                        cliente.log(accion, ok, fich_log)
                #Borro usuarios caducados y escribimos en el fichero
                self.borrar_caducados(registro)
                self.register2file()

            if metodo not in METODOS_ACEPTADOS:
                error = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(error)
                error = error.split('\r\n\r\n')[0]
                accion = 'Error: '
                error += error + str(IP_C) + ":" + str(port_client) + ":"
                liente.log(accion, error, fich_log)

            if metodo == "INVITE":
                li = linea[0]
                sdp = linea[1]

                if 'sip:' not in li \
                        or 'Content-Type: application/sdp' not in sdp:
                    error = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(error)
                    accion = 'Error: '
                    error = error + str(IP_C) + ':' + str(port_client) + ':'
                    cliente.log(accion, error, fich_log)
                    break

                #nombre del cliente que manda el register
                nom_client = linea[4].split('=')[1].split(' ')[0]
                #Para saber a quien envio el invite
                usuario_inv = linea[0].split()[1].split(':')[1]

                accion = "Received from " + str(IP_C) + ":"
                accion += str(port_client) + ":"
                cliente.log(accion, line, fich_log)

                # SDP bien formado y valores correctos
                # comprobación de valores ya hecha cuando lee del sdp
                # miramos si es un entero el puerto o una ip valida
                if linea[3] != 'v=0':
                    error = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(error)
                    accion = 'Error: '
                    error = error + str(IP_C) + ':' + str(port_client) + ':'
                    cliente.log(accion, error, fich_log)
                    break
                des_medio = linea[7].split(' ')[2]

                if linea[4][0] != 'o' or linea[5][0] != 's' \
                    or linea[6][0] != 't' or linea[7][0] != 'm' \
                        or des_medio != 'RTP' or not '@' in nom_client:
                    error = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(error)
                    accion = 'Error: '
                    error = error + str(IP_C) + ':' + str(port_client) + ':'
                    cliente.log(accion, error, fich_log)
                    break

                #Debes mandar un registrar antes de invite
                if nom_client not in registro:
                    error = "SIP/2.0 404 Not Found\r\n\r\n"
                    self.wfile.write(error)
                    accion = 'Error: '
                    error += error + str(IP_C) + ":" + str(port_client) + ":"
                    cliente.log(accion, error, fich_log)
                else:
                    if usuario_inv in registro:
                        #Cojo IP y puerto server del diccionario
                        IP = registro[usuario_inv][1]
                        PUERTO = registro[usuario_inv][2]
                        #Cojo el mensaje a reenviar

                        self.my_socket.connect((IP, int(PUERTO)))

                        print "Reenvio Invite --" + line
                        self.my_socket.send(line)
                        accion = "Sent to " + str(IP) + ":" + str(PUERTO) + ":"
                        cliente.log(accion, line, fich_log)
                        try:
                            resp = self.my_socket.recv(1024)
                            print "Recibo del servidor"
                            print resp
                            accion = "Received from " + str(IP) + ":"
                            accion += str(PUERTO) + ":"
                            cliente.log(accion, resp, fich_log)

                        except (socket.error):
                            error = "No server listening at " + str(IP)
                            error += " port " + str(PUERTO)
                            print error
                            accion = "Error: " + error
                            accion += str(IP_C) + ":" + str(port_client) + ":"
                            cliente.log(accion, '', fich_log)
                            #El servidor no esta escuchando mando msj error
                            error = "SIP/2.0 404 User Not Found\r\n\r\n"
                            self.wfile.write(error)
                            accion = "Error: "
                            cliente.log(accion, error, fich_log)
                            break

                        print "Reenvio al cliente --"
                        print resp
                        self.wfile.write(resp)
                        accion = "Sent to " + str(IP_C) + ":"
                        accion += str(port_client) + ":"
                        cliente.log(accion, resp, fich_log)
                    else:
                        error = "SIP/2.0 404 User Not Found\r\n\r\n"
                        self.wfile.write(error)
                        accion = "Error: "
                        cliente.log(accion, error, fich_log)
            if metodo == "ACK":
                destinatario = line.split('\r\n')[0].split(' ')[1]
                destinatario = destinatario.split(':')[1]
                accion = "Received from " + str(IP_C) + ":"
                accion += str(port_client) + ":"
                cliente.log(accion, line, fich_log)
                if destinatario in registro:
                    #IP y PUERTO destinatario para reenviar ACK
                    IP = registro[destinatario][1]
                    PUERTO = registro[destinatario][2]

                    self.my_socket.connect((IP, int(PUERTO)))

                    print "Reenvio al Servidor: " + line
                    self.my_socket.send(line)
                    accion = "Sent to " + str(IP) + ":"
                    accion += str(PUERTO) + ":"
                    cliente.log(accion, line, fich_log)

                else:
                    error = "SIP/2.0 404 User Not Found\r\n\r\n"
                    self.wfile.write(error)
                    accion = "Error: "
                    cliente.log(accion, error, fich_log)

            if metodo == "BYE":
                sip = "SIP/2.0"
                li = linea[0]

                if 'sip:' not in li or sip not in li or "@" not in li:
                    error = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(error)
                    accion = 'Error: '
                    error = error + str(IP_C) + ':' + str(port_client) + ':'
                    cliente.log(accion, error, fich_log)
                    break

                accion = "Received from " + str(IP_C) + ":"
                accion += str(port_client) + ":"
                cliente.log(accion, line, fich_log)

                destinatario = line.split('\r\n')[0].split(' ')[1]
                destinatario = destinatario.split(':')[1]

                if destinatario in registro:
                    #IP y PUERTO destinatario para reenviar BYE
                    IP = registro[destinatario][1]
                    PUERTO = registro[destinatario][2]

                    self.my_socket.connect((IP, int(PUERTO)))
                    print "Reenvio al Servidor: " + line
                    self.my_socket.send(line)
                    accion = "Sent to " + str(IP) + ":"
                    accion += str(PUERTO) + ":"
                    cliente.log(accion, line, fich_log)
                    try:
                        resp = self.my_socket.recv(1024)
                        print "Recibo del servidor"
                        print resp
                        accion = "Received from " + str(IP) + ":"
                        accion += str(PUERTO) + ":"
                        cliente.log(accion, resp, fich_log)
                    except (socket.error):
                        error = "No server listening at " + str(IP)
                        error += " port " + str(PUERTO)
                        print error
                        accion = "Error: " + error
                        accion += str(IP_C) + ":" + str(port_client) + ":"
                        cliente.log(accion, '', fich_log)

                    print "reenvio al cliente"
                    print resp
                    self.wfile.write(resp)
                    accion = "Sent to " + str(IP_C) + ":"
                    accion += str(port_client) + ":"
                    cliente.log(accion, resp, fich_log)
                else:
                    error = "SIP/2.0 404 User Not Found\r\n\r\n"
                    self.wfile.write(error)
                    accion = "Error: "
                    cliente.log(accion, error, fich_log)
                    # USUARIO NO ESTA EN EL REGISTRO

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
    cliente = ClienteHandler()  # Instancio ClienteHandler()
    IP = diccionario['server_ip']
    if IP <= "0.0.0.0" or IP >= "255.255.255.255":
        sys.exit("Error: El rango de tu IP no es válido")
    fich_log = diccionario['log_path']
    # En caso de no indicar la IP se utiliza la 127.0.0.1
    if IP == "":
        IP = "127.0.0.1"

    try:
        PUERTO = int(diccionario['server_puerto'])
    except ValueError:
        print "Error: El puerto debe ser un entero"
    NAME = diccionario['server_name']
    try:
        # Instanciamos EchoHandler
        serv = SocketServer.UDPServer((IP, PUERTO), EchoHandler)
        print "Server " + NAME + " listening at port " + str(PUERTO) + "..."
        accion = 'Starting...'
        cliente.log(accion, '', fich_log)
        serv.serve_forever()
    except(KeyboardInterrupt):
        mensaje = "Programa interrumpido por el usuario"
        print mensaje
        accion = "Finishing\r\n"
        cliente.log(accion, "", fich_log)
