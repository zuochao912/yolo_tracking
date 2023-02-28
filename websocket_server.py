# coding:utf8
# /usr/bin/env python
import socket,base64,hashlib
import time,threading

def get_headers(data):
    '''将请求头转换为字典'''
    header_dict = {}
    data = str(data,encoding="utf-8")
    '''
    'GET / HTTP/1.1\r\nHost: 127.0.0.1:8080\r\nConnection: Upgrade\r\n
    Pragma: no-cache\r\nCache-Control: no-cache\r\n
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.61\r\n
    Upgrade: websocket\r\nOrigin: null\r\nSec-WebSocket-Version: 13\r\nAccept-Encoding: gzip, deflate, br\r\n
    Accept-Language: zh-CN,zh-TW;q=0.9,zh-HK;q=0.8,zh;q=0.7,en;q=0.6,en-GB;q=0.5,en-US;q=0.4\r\n
    Sec-WebSocket-Key: laIaih9XUTnzxdB8UKcVFg==\r\nSec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n\r\n'
    '''
    # 客户端请求头的一部分字段;
    # upgrade：说明是websocket而不是http
    # Sec-websocket-key,由浏览器随机产生的校验码：浏览器随机生成的;
    # Sec-WebSocket-Protocol:同个URL下的不同服务,最终使用的服务
    header,body = data.split("\r\n\r\n",1)
    header_list = header.split("\r\n")
    for i in range(0,len(header_list)):
        if i == 0:
            if len(header_list[0].split(" ")) == 3:
                header_dict['method'],header_dict['url'],header_dict['protocol'] = header_list[0].split(" ")
        else:
            k,v=header_list[i].split(":",1)
            header_dict[k]=v.strip()
    return header_dict

def get_data(info):
    '''
        info: websocket发送的包
    '''
    payload_len = info[1] & 127
    if payload_len == 126:
        extend_payload_len = info[2:4]
        mask = info[4:8]
        decoded = info[8:]
    elif payload_len == 127:
        extend_payload_len = info[2:10]
        mask = info[10:14]
        decoded = info[14:]
    else:
        extend_payload_len = None
        mask = info[2:6]
        decoded = info[6:]

    bytes_list = bytearray()    #这里我们使用字节将数据全部收集，再去字符串编码，这样不会导致中文乱码
    for i in range(len(decoded)):
        chunk = decoded[i] ^ mask[i % 4]    #解码方式
        bytes_list.append(chunk)
    body = str(bytes_list, encoding='utf-8')
    return body


class server:
    def __init__(self,ip="127.0.0.1",port=8080):
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.bind((ip,port))
        sock.listen(1) #socket可以"挂起"的最大数量;
        self.sock=sock

    def check(self):
        '''
            args:
                sock:初始化的套接字
        '''

        #等待用户连接
        conn,addr = self.sock.accept()
        #获取握手消息，magic string ,sha1加密
        #发送给客户端
        #握手消息
        data = conn.recv(8096)

        headers = get_headers(data)

        # 对请求头中的sec-websocket-key进行加密
        response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
            "Upgrade:websocket\r\n" \
            "Connection: Upgrade\r\n" \
            "Sec-WebSocket-Accept: %s\r\n" \
            "WebSocket-Location: ws://%s%s\r\n\r\n"


        magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

        value = headers['Sec-WebSocket-Key'] + magic_string
        ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())

        response_str = response_tpl % (ac.decode('utf-8'), headers['Host'], headers['url'])

        # 响应【握手】信息
        conn.send(bytes(response_str, encoding='utf-8'))

        # if not blocking:
        #     conn.setblocking(0)
        # 设置blocking=false，wait会报错:无法立即完成一个非阻止性套接字操作

        # 此处默认只对付1个客户端,如果多个客户端，需要设置列表和标识符;
        self.conn=conn

    def wait(self,buffsize=8096):
        '''
            args:
                websocket阻塞等待数据
                buffsize为可接受的最大数据;此处默认我们一次可以接受全部数据
        '''    
        data = self.conn.recv(buffsize) #阻塞操作
        data = get_data(data) 
        return data

    def send(self,msg):
        '''
            args:
                conn:为socket连接;
                msg:为消息字符串;
        '''
        msg_bytes=bytes(msg,encoding="utf-8")
        import struct

        token = b"\x81" #接收的第一字节，一般都是x81不变
        length = len(msg_bytes)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)

        msg = token + msg_bytes
        self.conn.send(msg)

    def shutdown(self):
        self.conn.shutdown(2) #0关闭recv,1关闭send,2关闭recv、send
        self.conn.close()

def check_client(websock):
    global endsignal
    print("Checking websock!")
    while not endsignal:
        data = websock.wait()
        print("receiving:",data)
        if data =="end":
            endsignal=True
            print("Received end signal!")
            break

def run(websock):
    global endsignal
    t=0
    while not endsignal:
        time.sleep(1)
        result="time:{}".format(t)
        print(result)
        t+=1
        websock.send(result)
    websock.shutdown()
    print("End the sockets")


if __name__ == "__main__":
    global endsignal
    endsignal=False
    # get server and waiting for the client connection
    websock=server()
    websock.check()
    print("Thread begins!")
    T1 = threading.Thread(target=check_client(websock), name="T1")
    T2 = threading.Thread(target=run(websock), name="T2")
    T1.start()
    T2.start()

    time.sleep(2)
    threading.active_count()
    # when the server get end signal, stop detecting;
    


