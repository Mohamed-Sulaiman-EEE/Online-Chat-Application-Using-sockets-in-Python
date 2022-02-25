#............imports...........................
import threading
import socket
import datetime
import time
import sys
import webbrowser
#..............Variables........................
FORMAT = "utf-8"
PORT = 5050
HEADER = 64
room_name = ""
room_passcode = 0
Host = ""
User = ""
LOG = False
User_connected = False
Host_connected = False
SERVER_IP = ""
ACTIVE_USERS = 0
clients_list = list()
server_thread_list = list()
clients_book = dict()
#..............clientside................................
def join_room():
	global PORT , FORMAT   , User , HEADER , User_connected , SERVER_IP
	ADDR = (SERVER_IP, PORT)
	def connect():
		global PORT , SERVER_IP  
		try :
			ADDR = (SERVER_IP, PORT)
			client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			client.connect(ADDR)
			return client
		except :
			print(">>>> Falied to connect ! Retry again... ")
			time.sleep(8)
			sys.exit()

	def handle_server(connection):
		global PORT , FORMAT  , User , HEADER , User_connected
		User_connected = True
		while(User_connected):
			try :
				msg_len = connection.recv(HEADER).decode(FORMAT)
				if(msg_len):
					msg_len = int(msg_len)
					msg = connection.recv(msg_len).decode(FORMAT)
					print(msg)
					
			except:
				print(">>>> Connection has ended :( ")
				User_connected = False
				break
				sys.exit()
		return


	def send(client, msg):
		global PORT , FORMAT , HEADER 
		message = msg.encode(FORMAT)
		msg_len = len(message)
		send_len = str(msg_len).encode(FORMAT)
		send_len += b' ' * (HEADER - len(send_len))
		client.send(send_len)
		client.send(message)
		return

	def start():
		global PORT , FORMAT  , User , HEADER , User_connected
		print(">>>> JOINING ROOM.....")
		connection = connect()
		thread = threading.Thread(target = handle_server , args = (connection , ))
		thread.start()
		send(connection , User) #sending user name
		joining_msg = ">>>> {0} has joined the server !!!".format(User)
		send(connection , joining_msg)
		User_connected  = True
		while (User_connected):
				msg = input()
				try :
					if msg == "%DISCONNECT" :
						User_connected = False
						dm = ">>>> {0} is leaving the server now ...".format(User)
						send(connection , dm)
						time.sleep(3)
						send(connection, "%DISCONNECT")
						time.sleep(3)
						print('>>>> Disconnected from the room ...')
						exit()
						break
					elif (msg == "%ACTIVE-USERS"):
						send(connection,msg)
					else:
						msg = User +" : " + msg 
						send(connection, msg)
						time.sleep(1)
				except :
					exit()
	start()
	return

#...........................Server___side................................

def create_room():
	global PORT , FORMAT  , Host , HEADER , clients_list ,LOG , SERVER_IP
	ADDR = (SERVER_IP, PORT)
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try :
		server.bind(ADDR)
	except :
		print(">>>>Seems like an error occured ! Restart App")	
		sys.exit()

	def log_data(text):
		global LOG
		if(LOG):
			with open("log_data.txt" , "at") as f :
				time = datetime.datetime.now().strftime('%I:%M %p')
				f.write(time +"/ "+ text + "\n")
				f.close()

# Broadcast the message to all the active clients......
	def broadcast(msg , sender = None):
		global clients_list
		log_data(msg)
		for person in clients_list :
			if(person != sender ):
				send(person , msg)
			else :
				continue
		return
#Common function so send a message.......
	def send(client, msg):
		global PORT , FORMAT  , User , HEADER , User_connected
		message = msg.encode(FORMAT)
		msg_len = len(message)
		send_len = str(msg_len).encode(FORMAT)
		send_len += b' ' * (HEADER - len(send_len))
		client.send(send_len)
		client.send(message)
		return

#[New thread for every new client connected ]
	def handle_client(conn , addr ):
		global  FORMAT  , Host , HEADER , clients_list , room_name , ACTIVE_USERS , clients_book
		print(">>>> New connection ...")#admin only display
		msg_len = conn.recv(HEADER).decode(FORMAT)
		if(msg_len):
			msg_len = int(msg_len)
			msg = conn.recv(msg_len).decode(FORMAT)
		clients_book[msg] = conn			
		welcome_msg = ">>>> Welcome to \"{0}\" server hosted by \"{1}\" !!!".format(room_name , Host) 
		send(conn,welcome_msg)
		time.sleep(5)
		connected = True
		while(connected):
			try :
				msg_len = conn.recv(HEADER).decode(FORMAT)
				if(msg_len):
					msg_len = int(msg_len)
					msg = conn.recv(msg_len).decode(FORMAT)
					# User special commands...........
					if(msg == "%DISCONNECT"):
						ACTIVE_USERS -= 1
						connected = False
						clients_list.remove(conn)
						for client in clients_book.keys():
							if(clients_book[client] == conn):
								clients_book.pop(client)
						conn.close()
						break
					elif(msg == "%ACTIVE-USERS"):
						response = ">>>>[ Active users : {0} ]".format(ACTIVE_USERS)
						send(conn , response)
					else:
						print(msg)
						broadcast(msg, sender = conn )
			except :
				print(">>>> Client Connection has lost  :( ")
				break		
				conn.close()	
		return

#[Running on  thread : 2 ] 
	def handle_admin():
		run = True
		while(run):
			global clients_list , Host , Host_connected , server_thread_list , ACTIVE_USERS , LOG , clients_book
			msg = input()
		
			if(msg == "$STOP-SERVER"):
				msg = ">>>> Server is going to be stopped in 60 secs ! "
				broadcast(msg)
				print(msg)
				time.sleep(60)
				for client in clients_list:
					send(client , "Adios Amigo !")
					client.close()
				Host_connected = False
				decor()
				print(">>>> All clients has been disconnected ...")
				print(">>>> Server will terminate in 30 secs ...")
				time.sleep(60)
				try :
					for thr in server_thread_list:
						thr.stop()
				except:
					pass

				finally :
					run = False
					print(">>>> Program has been stopped :) \n>>>> Now you can close the app. ")
					sys.exit()
					break

			elif (msg == "$ACTIVE-USERS"):
				print(">>>>[ Active users : {0} ]".format(ACTIVE_USERS))
				
			elif (msg == "$LOG-ON"):
				LOG = True
				print(">>>> [ Started Logging... ]")
				
			elif(msg == "$LOG-OFF"):
				LOG = False
				print(">>>> [ Stopped Logging... ]")
					
			elif(msg == "$CLIENTS-BOOK"):
					print(">>>> List of active Clients... ")
					for c in clients_book.keys():
						print("[ "+ c + " ]")
						
			elif(msg == "$KICKOUT"):
						print(">>>> List of active Clients... ")
						for c in clients_book.keys():
							print("[ "+ c + " ]")
						print(">>>> Whom do you wanna kickout ?")
						name= input()
						try :
							for c in clients_book.keys():
								if (c == name):
									send(clients_book[name] , ">>>> You have been kicked out from the server :(   ")
									clients_book[name].close()

							clients_list.remove(clients_book[name])
							clients_book.pop(name)
							ACTIVE_USERS -= 1
							print(">>>> Kickout successfull :)")
							news = ">>>> {0} has been kicked out from the server by host !".format(name)
							broadcast(news)	
						except :
							print(">>>> Nobody is there in this room :(")
			else:
				msg = "Admin/ " + Host +" : " + msg
				broadcast(msg)

		return
				
#[Running on Main thread : 1]
	def start():
		print(">>>> Server has been created successfully .....Waiting for others to join....")
		global clients_list , Host_connected , server_thread_list , ACTIVE_USERS
		server.listen()
		thread = threading.Thread(target = handle_admin )
		thread.start()
		Host_connected = True
		while(Host_connected):
			conn , addr = server.accept()
			clients_list.append(conn)
			thread = threading.Thread(target = handle_client , args =  (conn , addr))
			thread.start()
			server_thread_list.append(thread)
			ACTIVE_USERS += 1
		return

	decor()
	start()
	decor()
	return

	
#................................................
def encrypt(text , key):
    #some kind of encryption that uses passcode as key
    #I dont prefer to expose the code coz , my app uses it
    return text

def encrypt_ip():
    global room_passcode , SERVER_IP
    SERVER_IP = socket.gethostbyname(socket.gethostname())
    key = 0
    #Something is done with passcode to make key..... 
    encrypted_ip = encrypt(SERVER_IP , key)
    return encrypted_ip



#.................................................................
def create_server():
	global room_name , room_passcode , Host , PORT , SERVER_IP
	room_name = input("Enter room name : ")
	try :
		room_passcode = int(input("Enter room passcode : "))
	except :	
		print("Room passcode should be a integer of 4 digits")
		print("Try again")
		decor()
		time.sleep(3)
		create_server()
	Host = input("Enter your name : ")
	print("Do you want the server to run on loacalhost or on dedicated port & IP ?   \n 1.Local Host \n 2.Dedicated port details ")
	ch = int(input("Choice : "))
	if(ch == 1):
		encrypted_ip = encrypt_ip()
	elif(ch == 2):
		try :
			PORT     = int(input("Enter room port    : "))
		except :
			print("PORT is a integer ")
			print("Try again")
			decor()
			time.sleep(5)
			create_server()

		SERVER_IP =   input("Enter IP address : ")
		key = 0
        #Something is done to passcode to make it as key
		encrypted_ip = encrypt( SERVER_IP , key)
	else:
		print("Try again")
		decor()
		time.sleep(3)
		create_server()

	decor()
	print(">>>> Server is ready , these are the joining details ...")
	print("Room address : ", encrypted_ip)
	print("PORT         : ",PORT) 
	print("Passcode     : ",room_passcode)
	print("IP           : " , SERVER_IP )
	print(">>>> Server is starting ......")
	time.sleep(5)
	with open("log_data.txt" , "at") as f :
				time_created = datetime.datetime.now().strftime('%A %m  %I:%M %p')
				text = " New room created....\n Room Name : {0} \n Room Passcode :{1} \n Created on : {2}  \n".format(room_name , room_passcode , time_created )
				f.write(text + "\n")
				f.close()
	create_room()
	return
#......................................................
def join_server():
	global room_passcode , User ,SERVER_IP , User , PORT
	def decrypt(text , key):
		#same encrytpion method is used to carry out decryption 
		return text

	room_address = input("Enter room address : ")
	try :
		PORT     = int(input("Enter room port    : "))
	except :
		print("PORT is a integer ")
		print("Try again")
		decor()
		time.sleep(5)
		join_server()
	try :
		room_passcode = int(input("Enter room passcode : "))
	except :	
		print("Room passcode should be a integer of 4 digits")
		print("Try again")
		decor()
		time.sleep(5)
		join_server()
	
	key = 0
    #Something is done to passcode to make it as key
	SERVER_IP = decrypt(room_address , key)
	User = input("Enter your name : ")
	#print("Joining IP : " , SERVER_IP)
	decor()
	join_room()
	return


def decor():
	print("*_"*22)
	print()

def Ngrok_helper():
	decor()
	ip        = input(" Enter IP Address : ")
	try :
		room_passcode = int(input(" Enter room passcode : "))
	except :	
		print(" Room passcode should be a integer of 4 digits")
		print(" Try again")
		decor()
		time.sleep(5)
		Ngrok_helper()
	port = input(" Enter PORT dsiplayed by the ngrok console : ")
	key = 0
    #Something is done to passcode to make it as key
	encrypted_ip = encrypt( ip , key)
	print(">>>> Share these details with your friends not the one that'll be displayed later ! ! ! \n")
	m = "  Room address : {0} \n  Room passcode : {1}\n  PORT : {2} \n".format(encrypted_ip ,room_passcode, port )
	print(m)
	decor()
	time.sleep(5)
	return

def main_menu():
	decor()
	print("   \"__________Chat__Room__APP__________\" \n")
	print("      || Made by Mohamed Sulaiman ||       \n")
	print("       |       Version 1.0        |       \n ")
	decor()
	print("      _____________MENU_______________ \n")
	print(" 1. Create a server \n 2. Join a server \n 3. Ngrok Helper \n 4. Help \n 5. Exit app")
	decor()
	try:
		choice = int(input("Enter Choice    : "))
		return choice
	except :
		print("Enter a integer, try again")
		decor()
		main_menu()

def main():
	choice = main_menu()
	if(choice == 1):
		try :
			create_server()
		except :
			print(">>>> Unfortunately some error has occured !!!")	
            #ITS JUST A EASY WAY ;)
			time.sleep(8)
		finally :

			exit()
		return
		
	elif(choice == 2):
		try :
			join_server()
		except :
			print(">>>> Unfortunately some error has occured !!!")
			time.sleep(8)
		finally :
			sys.exit(">>>> Close the app now ")
		return

	elif ( choice == 3):
		Ngrok_helper()
		main()

	elif (choice == 4):
		print(">>>> Read my Blog to get some idea .........")
		time.sleep(5)
		webbrowser.open_new("https://mypersonalblog-mks.blogspot.com/2022/02/online-chatting-app-using-sockets-in.html")
		main()
	
	elif (choice == 5):
		exit()

	else:
		print("Choice is out of bound ! \nTry again ...")
		time.sleep(5)
		decor()
		main()

try :
	main()
except :
	print(" ")
#............end.0f...code.........
