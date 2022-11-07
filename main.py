#!/usr/sbin/python3
# -*- coding: utf-8 -*-
from random import randint
import socket
import _thread
import json
import sys
import os
import time

class Node:
    def __init__(self, ip):
        self.ip = ip
        self.id = randint(1, 1000)
        #self.id = hash(f"{ip}+rafael")
        self.porta = 12345
        self.sucessor = {}
        self.antecessor = {}


class ServidorP2P:
    def __init__(self, ip=None):
        self.node = Node(ip=ip)
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _thread.start_new_thread(self.controle, ())
        self.interface()

    def controle(self):
        print(f"=> Iniciando P2P Server (ip={self.node.ip}, porta={self.node.porta})")
        orig = ("", self.node.porta)
        self.udp.bind(orig)

        while True:
            msg, cliente = self.udp.recvfrom(1024)
            msg_decoded = msg.decode("utf-8")
            string_dict = json.loads(msg_decoded)
            if string_dict["codigo"] == 0:
                self.resposta_join_solicitar(cliente)
            elif string_dict["codigo"] == 1:
                self.leave_resposta(string_dict, cliente)
            elif string_dict["codigo"] == 2:
                self.resposta_lookup_request(string_dict)
            elif string_dict["codigo"] == 3:
                self.update_resposta(string_dict, cliente)
            elif string_dict["codigo"] == 64:
                self.join_resposta(string_dict)
            elif string_dict["codigo"] == 65:
                print("Alteração para sair confirmada")
            elif string_dict["codigo"] == 66:
                self.resposta_lookup_confirmacao(string_dict)
            elif string_dict["codigo"] == 67:
                print("Update de confirmação")

    def interface(self) -> None:
        while True:
            os.system("clear")
            print("####################################")
            print("# 1 - Criar uma nova rede P2P      #")
            print("# 2 - Entrar em uma rede P2P       #")
            print("# 3 - Sair da rede P2P             #")
            print("# 4 - Imprimir informaçõs do Nó    #")
            print("# 5 - Sair da aplicação            #")
            print("####################################")
            try:
                opc = input("Informe uma opção: ")
                if opc == "1":
                    self.node.sucessor = {"id": self.node.id, "ip": self.node.ip}
                    self.node.antecessor = {"id": self.node.id, "ip": self.node.ip}
                    print("Rede P2P Inicializada")
                    input("Pressione ENTER para continuar")

                elif opc == "2":
                    os.system("clear")
                    ip = input("Informe o IP do no: ")
                    # Enviar pacote UDP para o endereço Ip de destino
                    self.lookup_solicitar(ip)
                    # print(f"Enviando msg para {ip}")
                    input("Pressione ENTER para continuar")

                elif opc == "3":
                    os.system("clear")
                    print("Saindo da rede... ... ...")
                    self.leave_solicitar()
                    input("Pressione ENTER para continuar ")

                elif opc == "4":
                    os.system("clear")
                    print("#      Informações do Nó      #")
                    print(f"# ID: {self.node.id} ")
                    print(f"# IP: {self.node.ip} ")
                    print(f"# Sucessor: {self.node.sucessor} ")
                    print(f"# Antecessor: {self.node.antecessor} ")
                    print(f"#----------------------------#")
                    input("Pressione ENTER para continuar")

                elif opc == "5":
                    sys.exit(0)
            except ValueError:
                opc = 0

    def leave_confirmation(self):
        #To Debug
        print("Alteracao de saida confirmada")

    def join_solicitar(self, string_dict):
        msg = {
            "codigo": 0,
            "id": self.node.id,
        }
        msg_json = json.dumps(msg)
        dest = (string_dict["ip_sucessor"], self.node.porta)
        self.udp.sendto(msg_json.encode('utf-8'), dest)

    def join_resposta(self, string_dict):
        self.node.sucessor = {"id": string_dict["id_sucessor"], "ip": string_dict["ip_sucessor"]}
        self.node.antecessor = {"id": string_dict["id_antecessor"], "ip": string_dict["ip_antecessor"]}
        self.update_antecessor(self.node.id, self.node.ip)
        self.update_sucessor(self.node.id, self.node.ip)
        
    def resposta_join_solicitar(self, cliente):
        # print(self.node.antecessor)
        # print(self.node.sucessor)
        msg = {
            "codigo": 64,
            "id_sucessor": self.node.id,
            "ip_sucessor": self.node.ip,
            "id_antecessor": self.node.antecessor["id"],
            "ip_antecessor": self.node.antecessor["ip"]
        } 
        msg_json = json.dumps(msg)
        self.udp.sendto(msg_json.encode('utf-8'), cliente)
    
    def leave_solicitar(self):
        if self.node.antecessor["id"] == self.node.sucessor["id"] and self.node.antecessor["id"] == self.node.id: #Se possuir um no na rede
            self.node.sucessor = {"id": None, "ip": None}
            self.node.antecessor = {"id": None, "ip": None}
        else:
            msg = {
                "codigo": 1,
                "identificador": self.node.id,
                "id_sucessor": self.node.sucessor["id"],
                "ip_sucessor": self.node.sucessor["ip"],
                "id_antecessor": self.node.antecessor["id"],
                "ip_antecessor": self.node.antecessor["ip"]
            }
            destAntecessor = (self.node.antecessor["ip"], self.node.porta)
            destSucessor = (self.node.sucessor["ip"], self.node.porta)

            msg_json = json.dumps(msg)
            self.udp.sendto(msg_json.encode('utf-8'), destAntecessor)
            self.udp.sendto(msg_json.encode('utf-8'), destSucessor)
            self.node.sucessor = {"id": None, "ip": None}
            self.node.antecessor = {"id": None, "ip": None}

    def leave_resposta(self, string_dict, cliente):
        if string_dict["identificador"] == self.node.antecessor["id"]:
            self.node.antecessor["id"] = string_dict["id_antecessor"]
            self.node.antecessor["ip"] = string_dict["ip_antecessor"]
        else:
            self.node.sucessor["id"] = string_dict["id_sucessor"]
            self.node.sucessor["ip"] = string_dict["ip_sucessor"]
        
        msg = {
            "codigo": 65,
            "identificador": string_dict["identificador"]
        }
        msg_json = json.dumps(msg)
        self.udp.sendto(msg_json.encode('utf-8'), cliente)
        
    def lookup_solicitar(self, ip):
        msg = {
            "codigo": 2,
            "identificador": self.node.id,
            "ip_origem_busca": self.node.ip,
            "id_busca": self.node.id,
        }
        msg_json = json.dumps(msg)
        dest = (ip, self.node.porta)
        self.udp.sendto(msg_json.encode('utf-8'), dest)

        
    def envio_lookup_confirmacao(self,string_dict):
        msg = {
            "codigo": 66,
            "id_busca": string_dict["id_busca"],
            "id_origem": string_dict["identificador"],
            "ip_origem": string_dict["ip_origem_busca"],
            "id_sucessor": self.node.id,
            "ip_sucessor": self.node.ip
        } 
        msg_json = json.dumps(msg)
        dest = (string_dict['ip_origem_busca'], self.node.porta)
        self.udp.sendto(msg_json.encode('utf-8'), dest)
        # print(msg_json)

    def resposta_lookup_request(self, string_dict):
        if self.node.antecessor["id"] > self.node.id: #verificando o primeiro da fila
            if self.node.antecessor["id"] < string_dict["identificador"]:
                self.envio_lookup_confirmacao(string_dict)
        elif self.node.antecessor == self.node.sucessor: #verificando a existencia de um unico No na rede
            self.envio_lookup_confirmacao(string_dict)
        else: #enviando lookup para o proximo No
            if string_dict["identificador"] > self.node.id:
                self.responder_lookup_request(string_dict, self.node.sucessor["ip"])
            else:
                self.envio_lookup_confirmacao(string_dict)
    
    def resposta_lookup_confirmacao(self,string_dict):
        self.join_solicitar(string_dict)
    
    def responder_lookup_request(self, msg, ip):
        dest = (ip, self.node.porta)
        self.udp.sendto(msg.encode('utf-8'), dest)

    def update_resposta(self,  string_dict, cliente):
        if "id_novo_antecessor" in string_dict:
            self.node.antecessor["id"] = string_dict["id_novo_antecessor"]
            self.node.antecessor["ip"] = string_dict["ip_novo_antecessor"]

        else:
            self.node.sucessor["id"] = string_dict["id_novo_sucessor"]
            self.node.sucessor["ip"] = string_dict["ip_novo_sucessor"]

        msg = {
            "codigo": 67,
            "id_origem_mensagem": string_dict["identificador"]
        }
        msg_json = json.dumps(msg)
        self.udp.sendto(msg_json.encode('utf-8'), cliente)

    def update_sucessor(self, id, ip):
        msg = {
            "codigo": 3,
            "identificador": self.node.id,
            "id_novo_antecessor": id,
            "ip_novo_antecessor": ip
        }
        dest = (self.node.sucessor["ip"], self.node.porta)
        msg_json = json.dumps(msg)
        self.udp.sendto(msg_json.encode('utf-8'), dest)
        
    def update_antecessor(self, id, ip):
        msg = {
            "codigo": 3,
            "identificador": self.node.id,
            "id_novo_sucessor": id,
            "ip_novo_sucessor": ip
        }
        dest = (self.node.antecessor["ip"], self.node.porta)
        msg_json = json.dumps(msg)
        self.udp.sendto(msg_json.encode('utf-8'), dest)
        

if __name__ == "__main__":
    if len(sys.argv) == 2:
        servidor = ServidorP2P(ip=sys.argv[1])
    else:
        print("Modo de utilização: python3 main.py <ENDEREÇO_IP>")
        sys.exit(0)