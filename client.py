import sys
import socket
import json
import os
import time

commands = ["CRT", "LST", "MSG", "DLT", "RDT", "EDT", "UPD", "DWN", "RMV", "XIT"]

serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# create a socket and connect to the server
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def requestHandler(username):
    while True:

        userInput = input("Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT: ")

        if not userInput:
            print("Invalid command")
        
        elif userInput.split()[0] not in commands:
            print("Invalid command")
        
        elif userInput.split()[0] == "CRT":
            CRT(userInput, username)

        elif userInput.split()[0] == "MSG":
            MSG(userInput, username)

        elif userInput.split()[0] == "DLT":
            DLT(userInput, username)

        elif userInput.split()[0] == "EDT":
            EDT(userInput, username)

        elif userInput.split()[0] == "LST":
            LST(userInput)

        elif userInput.split()[0] == "RDT":
            RDT(userInput)

        elif userInput.split()[0] == "UPD":
            UPD(userInput, username)

        elif userInput.split()[0] == "DWN":
            DWN(userInput)

        elif userInput.split()[0] == "RMV":
            RMV(userInput, username)

        elif userInput.split()[0] == "XIT":
            clientXIT(username)
            break

def clientConnect():

    username = input("Please enter your username: ")

    response = clientLOG(username)

    # If the username is valid, prompt for password
    if response["status"] == 100:
        # get password
        password = input("Please enter your password: ")

        response = clientPASS(username, password)

        if response["status"] == 200:
            print("Logged in successfully")
            print("Welcome back, " + username)

            # show all available commands
            requestHandler(username)

        else:
            # else if password is incorrect, call auth_connect again
            print("Incorrect password")
            clientConnect()

    # else if username is invalid, prompt for username creation
    elif response["status"] == 401:
        # get password
        password = input("Please enter your password: ")

        response = clientNEW(username, password)

        print("Welcome " + username)
        # show all available commands
        requestHandler(username)

    elif response["status"] == 403:
        print(f"{username} has already logged in")
        clientConnect()

    return username

# Function that sends request to server
def clientSendRequest(request):
    clientSocket.sendto((bytes(json.dumps(request).encode())), serverAddress)

    response = clientSocket.recvfrom(1024)[0]
    response = json.loads(response.decode())

    return response

# helper functions for request
def CRT(userInput, username):
    if len(userInput.split()) != 2:
        print("Usage: CRT threadtitle")
    else:
        threadTitle = userInput.split()[1]
        clientCRT(threadTitle, username)

def MSG(userInput, username):
    if len(userInput.split()) < 3:
        print("Usage: MSG threadtitle message")
    else:
        threadTitle = userInput.split()[1]
        message = userInput.split()[2:]
        clientMSG(threadTitle, message, username)

def DLT(userInput, username):
    if len(userInput.split()) != 3:
        print("Usage: DLT threadtitle messagenumber")
    else:
        threadTitle = userInput.split()[1]
        messageNumber = userInput.split()[2]
        clientDLT(threadTitle, messageNumber, username)

def EDT(userInput, username):
    if len(userInput.split()) < 4:
        print("Usage: EDT threadtitle messagenumber message")
    else:
        threadTitle = userInput.split()[1]
        messageNumber = userInput.split()[2]
        message = userInput.split()[3:]
        clientEDT(threadTitle, messageNumber, message, username)

def LST(userInput):
    if len(userInput.split()) != 1:
        print("Usage: LST")
    else:
        clientLST()

def RDT(userInput):
    if len(userInput.split()) != 2:
        print("Usage: RDT threadtitle")
    else:
        threadTitle = userInput.split()[1]
        clientRDT(threadTitle)

def UPD(userInput, username):
    if len(userInput.split()) != 3:
        print("Usage: UPD threadtitle filename")
    else:
        threadTitle = userInput.split()[1]
        filename = userInput.split()[2]
        clientUPD(threadTitle, username, filename)

def DWN(userInput):
    if len(userInput.split()) != 3:
        print("Usage: DWN threadtitle filename")
    else:
        threadTitle = userInput.split()[1]
        filename = userInput.split()[2]
        clientDWN(threadTitle, filename)

def RMV(userInput, username):
    if len(userInput.split()) != 2:
        print("Usage: RMV threadtitle")
    else:
        threadTitle = userInput.split()[1]
        clientRMV(threadTitle, username)

# Function to send username for authentication
def clientLOG(username):
    request = {
        "command": "LOG",
        "username": username,
    }

    response = clientSendRequest(request)

    return response

# Function to authenticate user
def clientPASS(username, password):
    request = {
        "command": "PASS",
        "username": username,
        "password": password
    }

    response = clientSendRequest(request)

    return response

# Function to create new user
def clientNEW(username, password):
    request = {
        "command": "NEW",
        "username": username,
        "password": password
    }

    response = clientSendRequest(request)

    NEWError(response)

# Function that handles CRT Command
def clientCRT(threadTitle, username):
    request = {
        "command": "CRT",
        "threadTitle": threadTitle,
        "username": username
    }

    response = clientSendRequest(request)

    CRTError(response)

# Function to post message
def clientMSG(threadTitle, message, username):
    request = {
        "command": "MSG",
        "threadTitle": threadTitle,
        "message": message,
        "username": username
    }

    response = clientSendRequest(request)

    MSGError(response)

# Function to delete message
def clientDLT(threadTitle, messageNumber, username):
    request = {
        "command": "DLT",
        "threadTitle": threadTitle,
        "messageNumber": messageNumber,
        "username": username
    }

    response = clientSendRequest(request)

    DLTError(response)

# Function to edit message
def clientEDT(threadTitle, messageNumber, newMessage, username):
    request = {
        "command": "EDT",
        "threadTitle": threadTitle,
        "messageNumber": messageNumber,
        "message": newMessage,
        "username": username
    }

    response = clientSendRequest(request)

    EDTError(response)

# Function to List threads
def clientLST():
    request = {
        "command": "LST"
    }

    response = clientSendRequest(request)

    LSTError(response)

# Function to read thread
def clientRDT(threadTitle):
    request = {
        "command": "RDT",
        "threadTitle": threadTitle,
    }

    response = clientSendRequest(request)

    RDTError(response)

# Function to upload file
def clientUPD(threadTitle, username, filename):

    if not os.path.exists(filename):
        print("File does not exist")
        return

    filesize = os.path.getsize(filename)

    request = {
        "command": "UPD",
        "threadTitle": threadTitle,
        "username": username,
        "filename": filename,
        "filesize": filesize
    }

    response = clientSendRequest(request)

    if response["status"] == 100:
        clientUploadFile(filename)
    else:
        UPDError(response)

# Function to download file
def clientDWN(threadTitle, filename):
    request = {
        "command": "DWN",
        "threadTitle": threadTitle,
        "filename": filename
    }

    response = clientSendRequest(request)

    if response["status"] == 100:
        clientDownloadFile(filename, response)
    else:
        DWNError(response)

# Function to remove thread
def clientRMV(threadTitle, username):
    request = {
        "command": "RMV",
        "threadTitle": threadTitle,
        "username": username
    }

    response = clientSendRequest(request)

    RMVError(response)

# Function to exit
def clientXIT(username):
    request = {
        "command": "XIT",
        "username": username
    }

    response = clientSendRequest(request)

    XITError(response)

# Helper functions to check for errors in response
def NEWError(response):
    if response["status"] == 200:
        print("User created successfully")

def CRTError(response):
    if response["status"] == 200:
        print("Thread created successfully")
    else:
        print("Thread already exists")

def MSGError(response):
    if response["status"] == 200:
        print("Message posted successfully")
    else:
        print("Thread does not exist")

def DLTError(response):
    if response["status"] == 200:
        print("Message edited successfully")
    elif response["status"] == 409:
        print("Message does not exist")
    elif response["status"] == 404:
        print("Thread does not exist")
    elif response["status"] == 401:
        print("You are not the owner of the message")

def EDTError(response):
    if response["status"] == 200:
        print("Message edited successfully")
    elif response["status"] == 409:
        print("Message does not exist")
    elif response["status"] == 404:
        print("Thread does not exist")
    elif response["status"] == 401:
        print("You are not the owner of the message")

def LSTError(response):
    if response["status"] == 200:
        print("List of threads successfully retrieved:")
        for thread in response["threads"]:
            print(f"{thread}")
    else:
        print("No threads exist")

def RDTError(response):
    if response["status"] == 200:
        for message in response["threadData"]:
            print(message.rstrip())
    elif response["status"] == 404:
        print("Thread does not exist")
    elif response["status"] == 409:
        print("Thread is empty")

def UPDError(response):
    if response["status"] == 404:
        print("Thread does not exist")
    elif response["status"] == 409:
        print("File already exists on thread")

def DWNError(response):
    if response["status"] == 404:
        print("Thread/File does not exist")
    elif response["status"] == 409:
        print("File does not exist on thread")

def RMVError(response):
    if response["status"] == 200:
        print("Thread removed successfully")
    elif response["status"] == 404:
        print("Thread does not exist")
    elif response["status"] == 401:
        print("You are not the owner of the thread")

def XITError(response):
    if response["status"] == 200:
        print("Logged out successfully, Goodbye!")
        sys.exit()
    else:
        print("You are not logged in")

# Helper functions for uploading and downloading files
def clientUploadFile(filename):

    with open(filename, "rb") as uploadFile:
        fileData = uploadFile.read(1024)

        while fileData:
            clientSocket.sendto(fileData, serverAddress)
            fileData = uploadFile.read(1024)


    response = clientSocket.recvfrom(1024)[0]
    response = json.loads(response.decode())

    if response["status"] == 200:
        print("File uploaded successfully")
    else:
        print("File upload failed")

def clientDownloadFile(filename, response):

    filesize = response["filesize"]

    with open(filename, "ab") as downloadFile:
        
        fileData = b''
        while len(fileData) < filesize:
            fileData += clientSocket.recvfrom(1024)[0]

        downloadFile.write(fileData)

    if os.path.getsize(filename) == filesize:
        print("File downloaded successfully")
    else:
        print("File download failed")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 client.py <server_port>")

    username = clientConnect()

    while True:
        serverData = clientSocket.recvfrom(1024)[0]
        serverData = json.loads(serverData.decode())
        requestHandler(username)