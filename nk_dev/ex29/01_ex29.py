#!/usr/bin/env python3

import socket

def create_server_socket(host='127.0.0.1', port=8080):
# サーバーのソケットを作成・設定する
# hostはサーバー側の待受IPアドレスで、この場合ローカルのみ待ち受ける

    # 待ち受けるソケットを作成
    # socket.AF_INET == IPv4を使用
    # socket.SOCK_STREAM == TCPで通信
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # プログラムを再起動したときに、TCPがポートを保持することで、
    # ”すでに使われているエラー”が起こるのを防止
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # ソケットにアドレスとポートを紐付ける
    # 引数は一つのタプル(host, port)
    server_socket.bind((host, port))
    
    # 接続待ち状態にする
    # 同時に５つまでの接続要求を受け付ける
    server_socket.listen(5)
    
    return server_socket
    
def handle_client(client_socket, client_address):
# クライアントからの通信を処理する

    # クライアントのアドレスと割り当てられたポート番号の表示
    print(f'connection from {client_address[0]}:{client_address[1]}')
    
    try:
        # クライアントからのデータをバッファに保存
        # メモリアライメントがしやすい２の累乗、かつ十分な大きさの1024
        data = client_socket.recv(1024)
        
        if data:
            print(f'Received {len(data)} bytes:')
            print(data.decode('utf-8', errors='replace')) # strictならデコードエラーで終了
            
            
        # レスポンスの送信
        response = 'HelloClient!'
        
        # クライアントのソケットに対して送信
        # sendallはすべて送るまでループする
        # ネットワークはバイト列で通信するのでencode()
        client_socket.sendall(response.encode('utf-8'))
        
    # エラーが起きてもサーバーを止めない
    except Exception as e:
        print(f'ERROR handle_client: {e}')
    finally:
        # どんな場合でも最後にソケットを閉じて終了する
        # ファイルディスクリプタがリークする　？？？
        client_socket.close()
        
        
def run_server(host='127.0.0.1', port=8080):
# ループする関数

    # ソケットを作成
    server_socket = create_server_socket(host, port)
    print(f'server listening on {host}:{port}')
    print('Press Ctrl + C to stop')
    
    try:
        # 無限ループ
        # クライアントの接続処理が終わったら、accept()関数でまた待つ
        while True:
            # クライアントの接続をここで待つ
            client_socket, client_address = server_socket.accept()
            
            # クライアントの接続を処理
            handle_client(client_socket, client_address)
            
            # このコードの場合、逐次処理となる
            
    except KeyboardInterrupt:
        print('\nShutting down server...')
    finally:
        server_socket.close()
        print('Server stopped')
        
if __name__ == '__main__':
    run_server()
    
    
    
    



