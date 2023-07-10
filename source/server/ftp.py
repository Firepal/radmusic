import socket
import os
from threading import Thread

SERVER_PORT = 2104
DATA_PORT = 1745
BUFFER_SIZE = 1024

# What if we served a fake directory representing our target,
# and, on request, encoded the file as needed?


class LogSoc(socket.socket):
    def __init__(self,socket_obj,name):
        self.__socket_obj = socket_obj
        self.__name = name
    
    def send(self, __data, __flags = 0):
        print(f"{self.__name}: {__data}")
        self.__socket_obj.send(__data,__flags)
    

    def __getattr__(self, attr):
        # Pass through any other function calls to the underlying socket object
        
        try:
            return getattr(self.__socket_obj, attr)
        except AttributeError:
            #If attribute was not found in self.df, then try in self
            return object.__getattr__(self, attr)

def handle_client(init_socket: socket.socket,client_address):
    init_socket.send(b"220 FTP server ready\r\n")
    authenticated = False
    cwd = os.getcwd()


    pasv_socket = None

    while True:
        data = init_socket.recv(BUFFER_SIZE).decode().strip()
        if not data:
            break

        command = data.split()[0].upper()
        match command:
            case "USER":
                init_socket.send(b"331 User name okay, need password.\r\n")
            
            case "PASS":
                authenticated = True
                init_socket.send(b"230 User logged in, proceed.\r\n")
            
            case _ if not authenticated:
                init_socket.send(b"530 Not logged in.\r\n")
            
            case "PWD":
                init_socket.send(f"257 \"{cwd}\"\r\n".encode())
            
            case "CWD":
                directory = data.split(" ", 1)[1]
                path = os.path.join(cwd, directory)
                if os.path.isdir(path):
                    cwd = path
                    init_socket.send(f"250 CWD successful. \"{cwd}\"\r\n".encode())
                else:
                    init_socket.send(b"550 Failed to change directory.\r\n")
            
            case "LIST":
                if not pasv_socket:
                    init_socket.send(b"425 Use PASV first.\r\n")
                    continue
                data_socket, data_addr = pasv_socket.accept()

                files = os.listdir(cwd)
                
                def binls(file):
                    if os.path.isfile(file):
                        return r"-rwxr-xr-x 1 owner group           213 Aug 23 16:31 "
                    else:
                        return r"drwxr-xr-x 1 owner group           213 Aug 23 16:31 "
                
                file_list = "\r\n".join([binls(file)+file for file in files])
                # file_list = "\r\n".join([r"-rwxr-xr-x 1 owner group           213 Aug 23 16:31 "+file for file in files])
                

                data_socket.send((file_list).encode())

                init_socket.send(b"226 Transfer complete.\r\n")
                data_socket.close()
                print(file_list)
            
            case "RETR":
                print("retrieving")
                filename = data.split()[1]
                file_path = os.path.join(cwd, filename)
                data_socket, data_addr = pasv_socket.accept()
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as file:
                        init_socket.send(b"150 File status okay; about to open data connection.\r\n")
                        while True:
                            file_data = file.read(BUFFER_SIZE)
                            if not file_data:
                                break
                            data_socket.send(file_data)
                        init_socket.send(b"226 Closing data connection.\r\n")
            
            case "TYPE":
                init_socket.send(b"200 Type set to I.\r\n")
            
            case "PASV":
                print("passive")
                pasv_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                pasv_socket.bind(("localhost",DATA_PORT))
                pasv_socket.listen(1)
                
                ip_address, port = pasv_socket.getsockname()
                init_socket.send(f"227 Entering Passive Mode ({ip_address.split('.')[0]},"
                                   f"{ip_address.split('.')[1]},"
                                   f"{ip_address.split('.')[2]},"
                                   f"{ip_address.split('.')[3]},"
                                   f"{port // 256},{port % 256})\r\n".encode())
            case "PORT":
                if not data_socket:
                    init_socket.send(b"425 Use PASV first.\r\n")
                    continue

                addr = data.split()[1].split(',')
                ip_address = ".".join(addr[:4])
                port = int(addr[4]) * 256 + int(addr[5])
                data_socket.connect((ip_address, port))
                init_socket.send(b"200 PORT command successful.\r\n")
            
            case "QUIT":
                init_socket.send(b"221 Goodbye.\r\n")
                break
            
            case _:
                init_socket.send(b"502 Command not implemented.\r\n")

    
    print(f"Closing socket {init_socket.family}")
    init_socket.close()


def start_ftp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", SERVER_PORT))
    server_socket.listen(5)
    print("FTP server started.")

    clients = []

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address[0]}:{client_address[1]}")
        
        t = Thread(None,handle_client,args=(client_socket,client_address))
        t.start()

if __name__ == "__main__":
    start_ftp_server()