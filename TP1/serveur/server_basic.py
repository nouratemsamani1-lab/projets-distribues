import socket
import datetime
import threading

class SimpleServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
    
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f" Serveur démarré sur {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f" Nouveau client: {address}")
                
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                client_socket.send(f"Bienvenue! Il est {current_time}\n".encode())
                client_socket.close()
                
            except Exception as e:
                if self.running:
                    print(f"Erreur: {e}")
    
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    server = SimpleServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nArrêt du serveur")
        server.stop()
