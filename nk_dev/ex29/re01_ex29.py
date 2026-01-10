#!/usr/bin/env python3

import threading
import socket

"""
    クライアントが接続したらリストを追加、
    切断したらリストから削除するサーバー
    
"""

import socket
import threading

# グローバル変数
clients = {}  # {socket, nickname, address} の辞書のリスト
lock = threading.Lock()

class ClientData:
    def __init__(self, nickname, client_socket, client_address):
        self.nickname = nickname
        self.cilent_socket = client_socket
        self.address = cilent_address
        
    def send_message(self, message):
        try:
            message = message.encode('utf-8')
            self.client_socket.sendall(message)
            return True
        except UnicodeEncodeError as e:
            print(f'ERROR send_message/ClientData: Cannot send message')
            print(f'UnicodeEncodeError: {e}')
            return False
        except Exception as e:
            print(f'ERROR send_message/ClientData: Cannot send message')
            print(f'Exception: {e}')
            return False
    

def create_server_socket(host='127.0.0.1', port=8080):
    """
        1. ソケットの作成
        2. 再起動時にTCP通信がポートを専有しないように設定
        3. ソケットにIPアドレスとポート番号を紐付け
        4. 接続待ち状態にして接続キューを指定
        
    """
    
    # ソケット作成
    # AF_INET == IPv4
    # SOCK_STEAM == TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 再起動時にアドレスの再利用を許可
    # ソケットの設定を指定　SOL_SOCKET
    # アドレスの再利用　SO_REUSEADDR
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # IPアドレスとポートの紐付け(bind)
    server_socket.bind((host, port))
    
    # 接続待ち状態に。一度の接続要求は5まで
    server_socket.listen(5)
    
    return server_socket

def sendall(message):
    if not isinstance(message, str):
        print('ERROR sendall: message must be str')
        return False
    for user in client.keys():
        if not client[user].send_message(message):
            print('ERROR send_massege/sendall: return False')
            break
            return False
    return True

def handle_client(client_socket, client_address):
    """
                個別クライアントの処理

        # ニックネームを受信
        # クライアントリストに追加
        # 参加通知を全員に送信

    """
    nickname = None

    try:
        # ニックネームを受信
        nickname = client_socket.recv(1024)
        if not nickname:
            print('ERROR handle_client: Cannot receive nickname')
            return False
        
        # 排他制御下でクライアントデータを記録
        with lock:
            print(f'Login detected: {nickname}')
            print(f'Address data: {client_address[0]}:{client_address[1]}')
            client[nickname] = ClientData(nickname, client_socket, client_address)
            
            # ユーザーの接続を全ユーザーに通知
            message = f'Hello {nickname}!'
            if not sendall(message):
                print('ERROR sendall/handle_client: return False')
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # クライアントリストから削除
        # 退出通知を全員に送信
        # ソケットを閉じる
        pass

def run_server(host='127.0.0.1', port=8080):
    """
    サーバーのメインループ
    """
    
    # ソケットの作成
    server_socket = create_server_socket(host, port)
    print(f'server_listening: {host}:{port}')
    print('Press Ctrl + C to stop')
    
    try:
        while True:
            # サーバーを待機状態にする
            client_socket, client_address = server_socket.accept()
            
            # スレッド作成
            client_thread = threading.thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            
            client_thread.start()
            
        
    except KeyboardInterrupt:
        print('Shutting down server...')
    finally:
        server_socket.close()
        print('Servser stopped')

if __name__ == "__main__":
    run_server()

