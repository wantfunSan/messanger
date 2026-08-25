from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

from cryptography.fernet import Fernet

import sqlite3
import sys

import tkinter

conn = sqlite3.connect('server.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS accounts(
			phone TEXT PRIMARY KEY, 
			username TEXT,
			password TEXT,
			chats TEXT)
		   ''')

def broadcast(cl, need_chat, msg, prefix, key, cipher_suite):
	try:
		for cl_nm in clients:
			if cl_nm == prefix + ' rec':
				data2send = cipher_suite.encrypt(bytes(f'{need_chat}', 'utf8'))
				clients[cl_nm].send(data2send)

				res = clients[cl_nm].recv(BUFSIZ).decode("utf8")
				key = res.encode()
					

				res = bytes(res, 'utf8')

				cipher_suite = Fernet(key)
				res = cipher_suite.decrypt(res).decode('utf-8')
					
				if res == 'ok':
					data2send = cipher_suite.encrypt(bytes(f'{msg}', "utf8"))
					clients[cl_nm].send(data2send)

					data2send = cipher_suite.encrypt(bytes('sended', 'utf8'))
					cl.send(data2send)
						
					break
				else:
					data2send = cipher_suite.encrypt(bytes('not need chat', "utf8"))
					cl.send(data2send)
						
					break

		data2send = cipher_suite.encrypt(bytes('non active', "utf8"))
		cl.send(data2send)
	
	except Exception as error:
		data2send = cipher_suite.encrypt(bytes('non active', "utf8"))
		cl.send(data2send)
		print(f'Ошибка: {error}')
		
def accept_incoming_connections():
	while True:
		client, client_address = SERVER.accept()

		print("%s:%s соединено" % client_address)
		
		Thread(target=handle_client, args=(client, )).start()

def handle_client(client):
	try:
		data = client.recv(BUFSIZ).decode('utf8')

		key = data.encode()
		

		data = bytes(data, 'utf8')

		cipher_suite = Fernet(key)

		data = cipher_suite.decrypt(data).decode('utf-8')
		

		if 'quit' in data:
			client.close()
			SERVER.close()
			sys.exit()

		splitted_data = data.split(' ')
		
		for i in range(len(splitted_data)):
			splitted_data[i] = splitted_data[i][splitted_data[i].find('=')+1:]

		c.execute('SELECT username, password, chats FROM accounts WHERE phone = ?', (splitted_data[1], ))
		db_saved = c.fetchone()

		if db_saved is None and splitted_data[0] == 'reg':
			c.execute('INSERT INTO accounts VALUES(?,?,?,?)', (splitted_data[1],splitted_data[2],splitted_data[3], None))
			conn.commit()
			clients[splitted_data[2]] = client

			data2send = cipher_suite.encrypt(bytes("open", "utf8"))
			client.send(data2send)
	
		elif db_saved is None and (splitted_data[0] == 'log' or splitted_data[0] == 'chat'):
			data2send = cipher_suite.encrypt(bytes("closed no", "utf8"))
			client.send(data2send)
	
		elif db_saved is not None and (splitted_data[0] == 'log' or splitted_data[0] == 'chat'): 
		
			if splitted_data[2] != db_saved[1]:
				data2send = cipher_suite.encrypt(bytes("closed pass", "utf8"))
				client.send(data2send)
		
			elif splitted_data[2] == db_saved[1]:
			
				if splitted_data[0] == 'log':
					clients[db_saved[0]] = client

					data2send = cipher_suite.encrypt(bytes(f"open {db_saved[0]}", "utf8"))
					client.send(data2send)
			
				elif splitted_data[0] == 'chat':
					clients[db_saved[0]] = client
					
					data2send = cipher_suite.encrypt(bytes(f"open {db_saved[2]}", "utf8"))
					client.send(data2send)

			else:
				data2send = cipher_suite.encrypt(bytes("closed hz", "utf8"))
				client.send(data2send)
	
		elif db_saved is not None and splitted_data[0] == 'reg':
			data2send = cipher_suite.encrypt(bytes("closed yes", "utf8"))
			client.send(data2send)

		elif splitted_data[0] == 'update':
			clients[db_saved[0]+' rec'] = client

		elif splitted_data[0] == 'update2':
			clients[splitted_data[1] +' rec2'] = client

		elif splitted_data[0] == 'add_chat':
			c.execute('SELECT username FROM accounts WHERE phone = ?', (splitted_data[1], ))
			user_data = c.fetchone()

			if user_data is None or user_data == list():
				data2send = cipher_suite.encrypt(bytes('not found', 'utf8'))
				client.send(data2send)
			else:
				data2send = cipher_suite.encrypt(bytes(f'find {user_data[0]}', 'utf8'))
				client.send(data2send)

				c.execute('SELECT chats FROM accounts WHERE phone = ?', (splitted_data[2], ))
				my_chats = c.fetchone()
				
				if my_chats[0] == None:
					c.execute('UPDATE accounts SET chats = ? WHERE phone = ?', (user_data[0], splitted_data[2]))
				else:
					c.execute('UPDATE accounts SET chats = ? WHERE phone = ?', (my_chats[0] +' ' + user_data[0], splitted_data[2]))
				conn.commit()
				
				for cl_nm in clients:
					if cl_nm == f'{splitted_data[2]} rec2':
						data2send = cipher_suite.encrypt(bytes(f'make {user_data[0]}', 'utf8'))
						clients[cl_nm].send(data2send)

		elif '@' in data:
			msg = data

			msg = msg.split(' @')

			try:
				broadcast(client, msg[2], msg[0], msg[1], key, cipher_suite)
			except Exception as err:
				data2send = cipher_suite.encrypt(bytes('non active', "utf8"))
				client.send(data2send)
				print(f'176 строка: {err}')
	
	except ConnectionResetError:
		pass
clients = dict()

HOST = '1.1.1.1' 
PORT = 12345
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

def stop():
	SERVER.close()
	for cl_nm in clients:
		clients[cl_nm].close()
	sys.exit()

if __name__ == "__main__":
	SERVER.listen(5)
	print("ожидание соединения")
	ACCEPT_THREAD = Thread(target=accept_incoming_connections)
	ACCEPT_THREAD.start()
	ACCEPT_THREAD.join()
	SERVER.close()