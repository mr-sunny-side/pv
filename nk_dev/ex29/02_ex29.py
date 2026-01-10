#!/usr/bin/env python3 

import socket
import threading

# クライアントからの接続数をカウント(global)
connect_num = 0
lock = threading.Lock()    #　カウントする際に一度に１スレッドに制限する鍵

# ソケットの作成関数
def create_server_socket(host='127.0.0.1', port=8080):
    """
        1. ソケットの作成
        2. 再起動時にTCP通信がポートを専有しないように設定
        3. ソケットにIPアドレスとポート番号を紐付け
        4. 接続待ち状態にして接続キューを指定
        
    """

    # ソケット作成
    # AF_INET == IPv4
    # SOCK_STREAM == TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 再起動時にportがTCPによって予約状態になるのをやめる
    # socket.SOL_SOCKET == ソケット層を指定
    # socket.SO_REUSEADDR == アドレスの再利用を許可
    # 1 == 有効
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # ソケットをIPアドレスとポートを紐付ける
    # 引数は一つのタプル
    server_socket.bind((host, port))
    
    server_socket.listen(5)
    
    return server_socket
    
def handle_client(client_socket, client_address, client_id):
    """
        1. global変数の呼び出し（数えるため）
        2. 排他制御を用いて起動中の接続を数える
        3. id(何回目の接続か)とアドレス・ポート、現在の接続数を出力
        
        4.バッファにサーバーからのデータを保存、データサイズ・デコードデータを出力
        5.送信するデータを作成(文字列,id,thread_name,現在の接続数)
        
            thread_name = threading.current_thread().name
            - スレッド情報を取得？
        
        6.データを送信
        7.finallyにスレッドの終了・接続数のデクリメントを記述
                接続の終了を出力
    """

    global  connect_num
    
    cur_con = 0
    # 排他制御を用いて、現在の接続数を数える
    with lock:
        connect_num += 1
        cur_con = connect_num    # この回は何個目の接続なのか記録
        
    print(f'Connection ID: [{client_id}]')
    print(f' - address:port: {client_address[0]}:{client_address[1]}')  # アドレスとポートは配列で保存されている
    print(f' - current_connection: {cur_con}')
    
    try:
        # サーバーからの送信をバッファに保存
        data = client_socket.recv(1024)
        if data:
            print('Data from client: ')
            print(f' - data size: {len(data)}')
            print(f' - {data.decode("utf-8", errors="replace")}')
            
        thread_name = threading.current_thread().name
        response = 'HelloClient!'
        response += f'\nClient ID: {client_id}'
        response += f'\nThread Info: {thread_name}'
        response += f'\nConnection num: {cur_con}'
        response += '\n'
        
        # データをサーバーに送信
        client_socket.sendall(response.encode('utf-8'))
        
    except Exception as e:
        print(f'ERROR handle_client: {e}')
    finally:
        client_socket.close()
        with lock:
            connect_num -= 1
            cur_con = connect_num
        print(f'Client ID [{client_id}] is closed')
        print(f' - Conection num: {cur_con}')
        print()
        
    
    
def run_server(host='127.0.01', port=8080):
    
    server_socket = create_server_socket(host, port)
    print(f'Server listening {host}:{port}')
    print('Press Ctrl + C to Stop')
    print()
    
    connection_counter = 0         # 接続した回数を数える
    
    try:
        while True:
            
            # サーバーソケットを待機状態にする
            client_socket, client_address = server_socket.accept()
            
            connection_counter += 1           
            client_id = connection_counter      # 接続順からidを付与
            
            # 各接続ごとにスレッドを作成
            # target == スレッドで実行する関数
            # args == その引数の指定
            # daemon == デーモンとして開始するか否か
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address, client_id),
                daemon=True
            )

            # スレッドを開始
            client_thread.start()
        
    # Ctrl + Cを検知
    except KeyboardInterrupt as e:
        print('Shutting down server...')
    # 必ずソケットを閉じる
    finally:
        server_socket.close()
        print('Server stopped')
        
if __name__ == '__main__':
    run_server()
