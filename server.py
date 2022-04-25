import sys
import socket
import json
import os
import time

serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])

serverAddress = (serverHost, serverPort)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind(serverAddress)

authDict = {}

loggedInUsers = []

clients = {}

threads = {}

files = {}

# Opening the credentials file and storing it in a dictionary
with open("credentials.txt", "r") as auth:
    credentials = auth.readlines()
    for line in credentials:
        username, password = line.split()
        authDict[username] = password.strip()

def requestHandler():
    while True:
        request, address = serverSocket.recvfrom(1024)

        if not request:
            break

        request = json.loads(request.decode())

        if request["command"] not in ("LOG", "PASS", "NEW"):
            print(f"{request['command']} request received from {clients[address]}")

        if request["command"] == "LOG":
            serverLOG(request["username"], address)
        elif request["command"] == "PASS":
            serverPASS(request["username"], request["password"], address)
        elif request["command"] == "NEW":
            serverNEW(request["username"], request["password"], address)
        elif request["command"] == "CRT":
            serverCRT(request["threadTitle"], request["username"], address)
        elif request["command"] == "MSG":
            serverMSG(request["threadTitle"], request["message"], request["username"], address)
        elif request["command"] == "DLT":
            serverDLT(request["threadTitle"], request["messageNumber"], request["username"], address)
        elif request["command"] == "EDT":
            serverEDT(request["threadTitle"], request["messageNumber"], request["message"], request["username"], address)
        elif request["command"] == "LST":
            serverLST(threads, address)
        elif request["command"] == "RDT":
            serverRDT(request["threadTitle"], address)
        elif request["command"] == "UPD":
            serverUPD(request["threadTitle"], request["username"], request["filename"], request["filesize"], address)
        elif request["command"] == "DWN":
            serverDWN(request["threadTitle"], request["filename"], address)
        elif request["command"] == "RMV":
            serverRMV(request["threadTitle"], request["username"], address)
        elif request["command"] == "XIT":
            serverXIT(request["username"], address)

# Function that sends response to client
def serverSendResponse(response, address):
    serverSocket.sendto((bytes(json.dumps(response).encode())), address)

# Function to log in user in server
def serverLOG(username, address):
    response = {}

    # If the username is already logged in, return error
    if username in loggedInUsers:
        print("User already logged in")
        response["status"] = 403

    # If the username exists but not logged in, return continue
    elif username in authDict and username not in loggedInUsers:
        response["status"] = 100
        print("Client authenticating")

    # if the username does not exist, return error
    elif username not in authDict and username not in loggedInUsers:
        response["status"] = 401
        
    serverSendResponse(response, address)

# Function to authenticate password in server
def serverPASS(username, password, address):
    response = {}

    # If the password match the username in the authDict, return OK
    if authDict[username] == password:
        loggedInUsers.append(username)
        if address not in clients:
            clients[address] = username
        response["status"] = 200
        print(f"{username} logged in")

    else:
        print("Incorect password given")
        response["status"] = 401

    serverSendResponse(response, address)

def serverNEW(username, password, address):
    response = {}

    with open("credentials.txt", "a") as credentials:
        credentials.write(f"{username} {password}\n")

    loggedInUsers.append(username)
    if address not in clients:
        clients[address] = username

    authDict[username] = password
    
    response["status"] = 200
    print(f"{username} logged in")

    serverSendResponse(response, address)

def serverCRT(threadTitle, username, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        # create thread
        createThread(threadTitle, username)
        response["status"] = 200
        print(f"Thread {threadTitle} created")
    else:
        response["status"] = 404

    serverSendResponse(response, address)

def serverMSG(threadTitle, message, username, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        serverSendResponse(response, address)
        return
    else:
        # Add 1 to the threads to indicate that a new message has been added
        threads[threadTitle] += 1

        with open(threadTitle, "a") as thread:
            thread.write(f"{threads[threadTitle]} {username}: {' '.join(message)}\n")

        response["status"] = 200
        print(f"{username} sent message to {threadTitle}")
    
    serverSendResponse(response, address)

def serverDLT(threadTitle, messageNumber, username, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        print("Thread does not exist")
        serverSendResponse(response, address)
        return

    with open(threadTitle, "r+") as thread:
        threadData = thread.readlines()

        messageFound = False
        trueOwner = False

        for index, line in enumerate(threadData[1:]):
            if line.split()[0] == messageNumber:
                messageFound = True
                if line.split()[1][:-1] == username:
                    trueOwner = True

            if messageFound and trueOwner:
                deleteLine(threadTitle, threadData, index + 1)
                response["status"] = 200
                print(f"{username} deleted message {messageNumber} from {threadTitle}")
                break

        if messageFound and not trueOwner:
            response["status"] = 401
        elif not messageFound:
            response["status"] = 409

    serverSendResponse(response, address)

def serverEDT(threadTitle, messageNumber, message, username, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        serverSendResponse(response, address)
        return

    with open(threadTitle, "r+") as thread:
        threadData = thread.readlines()

        messageFound = False
        trueOwner = False

        for index, line in enumerate(threadData[1:]):
            if line.split()[0] == messageNumber:
                messageFound = True
                if line.split()[1][:-1] == username:
                    trueOwner = True
            if messageFound and trueOwner:
                editLine(threadTitle, threadData, index + 1, " ".join(message))
                response["status"] = 200
                print(f"{username} edited message {messageNumber} in {threadTitle}")
                break
        
        if messageFound and not trueOwner:
            response["status"] = 401
        elif not messageFound:
            response["status"] = 409
        

    serverSendResponse(response, address)

def serverLST(threads, address):
    response = {}

    # If the threads is empty return error
    if not threads:
        response["status"] = 404
        serverSendResponse(response, address)
        return

    # If threads exists, return the list of threads
    else:
        response["status"] = 200
        print("Threads retrived successfully")
        response["threads"] = list(threads.keys())

    serverSendResponse(response, address)

def serverRDT(threadTitle, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        serverSendResponse(response, address)
        return

    with open(threadTitle, "r") as thread:
        threadData = thread.readlines()[1:]

        # If the thread is empty, return error
        if not threadData:
            response["status"] = 409
        else:
            response["status"] = 200
            print("Thread data retrived successfully")
            response["threadData"] = threadData

    serverSendResponse(response, address)

def serverUPD(threadTitle, username, filename, filesize, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        serverSendResponse(response, address)
        return

    # If the file already exists in the thread
    if threadTitle in files and filename in files[threadTitle]:
        response["status"] = 409
        serverSendResponse(response, address)
        return

    # If the file does not exist in the thread continue
    response["status"] = 100
    print(f"{username} uploading {filename} to {threadTitle}")
    serverSendResponse(response, address)

    # Receive the file
    serverUploadFile(threadTitle, username, filename, filesize, address)


def serverDWN(threadTitle, filename, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        serverSendResponse(response, address)
        return

    # If there is not a file on the thread
    if filename not in files[threadTitle]:
        response["status"] = 409
        serverSendResponse(response, address)
        return

    # If the file exists on the thread, continue
    response["status"] = 100
    print(f"{filename} is being downloaded from {threadTitle}")
    response["filesize"] = os.path.getsize(f"{threadTitle}-{filename}")
    serverSendResponse(response, address)

    # Send the file
    serverDownloadFile(threadTitle, filename, address)

def serverRMV(threadTitle, username, address):
    response = {}

    # If the thread does not exist
    if not os.path.exists(threadTitle):
        response["status"] = 404
        serverSendResponse(response, address)
        return

    with open(threadTitle, "rb") as thread:
        trueOwner = thread.readlines()[0]

        if (trueOwner.decode()).strip() != username:
            response["status"] = 401
        else:
            os.remove(threadTitle)
            # Remove the thread from the threads dictionary
            del threads[threadTitle]
            # Remove the thread from the files dictionary
            del files[threadTitle]
            response["status"] = 200
            print(f"{username} removed {threadTitle}")

    serverSendResponse(response, address)

def serverXIT(username, address):
    response = {}

    print(f"{username} exited")
    loggedInUsers.remove(username)
    print("Waiting for clients")
    response["status"] = 200

    serverSendResponse(response, address)

def createThread(threadTitle, username):
    with open(threadTitle, "w") as newThread:
        newThread.write(f"{username}\n")

    threads[threadTitle] = 0
    files[threadTitle] = []

def serverUploadFile(threadTitle, username, filename, filesize, address):
    response = {}

    with open(f"{threadTitle}-{filename}", "ab") as newFile:

        fileData = b''
        while len(fileData) < filesize:
            fileData += serverSocket.recvfrom(1024)[0]

        newFile.write(fileData)

    # Add filename to the list of files in the thread
    if os.path.getsize(f"{threadTitle}-{filename}") == filesize:
        # entry into the thread
        with open(threadTitle, "a") as thread:
            thread.write(f"{username} uploaded {filename}\n")

        files[threadTitle].append(filename)
        response["status"] = 200
    else:
        # Delete the file and restart
        os.remove(f"{threadTitle}-{filename}")
        response["status"] = 500

    serverSendResponse(response, address)

def serverDownloadFile(threadTitle, filename, address):

    with open(f"{threadTitle}-{filename}", "rb") as fileToSend:
        fileData = fileToSend.read(1024)

        while fileData:
            serverSocket.sendto(fileData, address)
            fileData = fileToSend.read(1024)


def editLine(threadTitle, threadData, index, message):

    threadData[index] = f"{threadData[index].split()[0]} {threadData[index].split()[1]} {message}\n"

    with open(threadTitle, "w") as thread:
        thread.writelines(threadData)


def deleteLine(threadTitle, threadData, index):
    threadData.pop(index)

    # Add the owner name back to the first line
    newMessages = []
    newMessages.append(threadData[0])

    for line in threadData[1:index]:
        newMessages.append(line)

    for line in threadData[index:]:
        if line.split()[0].isdigit():
            newMessages.append(f"{int(line.split()[0]) - 1}{line[1:]}")
        else:
            newMessages.append(line)

    with open(threadTitle, "w") as thread:
        thread.writelines(newMessages)

    # Update number of messages in thread
    threads[threadTitle] -= 1

def shutDown():
    for thread in threads:
        for filename in files[thread]:
            os.remove(f"{thread}-{filename}")
        os.remove(thread)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 server.py <server_port>")
        exit(0)

    while True:
        print("===== New connection created for: ", serverAddress)
        requestHandler()
        