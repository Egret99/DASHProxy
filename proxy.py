#!/usr/bin/env python3.10
import xml.etree.ElementTree as ET
from socket import *
import sys
import time

# Utility functions

def calculate_current_throughput(t1, t2, size, alpha, currentThroughput):
    newThroughput = size*1.0/(t2-t1)
    currentThroughput = alpha*newThroughput + (1-alpha)*currentThroughput
    return (currentThroughput, newThroughput)

def get_bitrates(manifest_file):
    bitrates = []
    root = ET.fromstring(manifest_file)
    for representation in root.find("Period").find("AdaptationSet").findall("Representation"):
        bitrates.append(int(representation.get("bandwidth")))

    return bitrates

def find_bitrate(bitrates, currentThroughput):
    biggest_bitrate = bitrates[0]
    for bitrate in bitrates:
        if bitrate > biggest_bitrate and bitrate*1.5 <= currentThroughput:
            biggest_bitrate = bitrate
    
    return biggest_bitrate

def transform_uri(uri, bitrate):
    paths = uri.split("/")
    paths[0] = paths[0].split("_")[0] + "_" + bitrate + "bps"
    return "/".join(paths)

def save_log(log):
    return

# Connection functions

def receive_request(connectionSocket):
    request = connectionSocket.recv(2048).decode()
    uri = request.split("\n")[0].split(" ")[1]
    receive_time = time.time()

    return (request, uri, receive_time)

def connect_to_server(serverIp, proxyIp, listeningPort):
    sendingSocket = socket(AF_INET,SOCK_STREAM)
    try:
        sendingSocket.bind((proxyIp, listeningPort+1))
    except error as e:
        print(e)
    sendingSocket.connect((serverIp, 8080))

    return sendingSocket

def receive_file(sendingSocket):
    response = sendingSocket.recv(2048)

    headers, body = response.split("\n\n")
    file_chunks = [body]
    current_file_length = len(body)
    total_file_length = current_file_length

    for header in headers.split("\n"):
        if header[:14] == "Content-Length":
            total_file_length = int(header[16:])

    while current_file_length < total_file_length:
        file_chunks.append(sendingSocket.recv(2048))

    return (headers, file_chunks, total_file_length, time.time())

def request_file(sendingSocket, url, request):
    requestParameters = request.split("\n")
    requestParameters[0] = requestParameters[0].split(" ")
    requestParameters[0][1] = url
    requestParameters[0] = " ".join(requestParameters[0])

    sendingSocket.send("\n".join(requestParameters).encode())

    return receive_file(sendingSocket)

def return_file_to_client(connectionSocket, response_headers, file_chunks):
    response = response_headers + "\n\n" + "".join(file_chunks)
    connectionSocket.send(response.encode())

def handle_communication(connectionSocket, proxyIp, serverIp, listeningPort, alpha, logName):
    currentThroughput = 0
    bitrate = 0
    bitrates = []

    # connect to server
    try:
        sendingSocket = connect_to_server(proxyIp, serverIp, listeningPort)
    except error as e:
        print("Cannot connect to server:", e)
        print("Closing connection with client")
        connectionSocket.close()
        return

    while True:
        try:
            request, uri, t1 = receive_request(connectionSocket)
            if uri[-3:] == "mpd":
                uri_new = "/var/www/html" + uri.split(".")[0] + "_nolist.mpd"
                response_headers, file_chunks, size, t2 = request_file(sendingSocket, uri_new, request)
                return_file_to_client(connectionSocket, response_headers, file_chunks)

                # Get the correct manifest file and bitrates & also set initial throughput
                manifest_file = "".join([file_chunk.decode() for file_chunk in request_file(sendingSocket, "/var/www/html" + uri, request)[1]])
                bitrates = get_bitrates(manifest_file)
                currentThroughput = min(bitrates)
                bitrate = currentThroughput
            else:
                if currentThroughput != min(bitrates): # tell if we already have some samples of throughputs
                    # if no samples, we use smallest bitrate
                    # else we find new bitrate
                    bitrate = find_bitrate(bitrates, currentThroughput) 

                uri_new = transform_uri(uri, bitrate) # transform uri based on bitrate
                response_headers, file_chunks, size, t2 = request_file(sendingSocket, "/var/www/html" + uri_new, request)
                return_file_to_client(connectionSocket, response_headers, file_chunks)
                currentThroughput, sampleThroughput = calculate_current_throughput(t1, t2, size, alpha, currentThroughput)
            
                save_log(logName, (t2, t2-t1, currentThroughput, sampleThroughput, bitrate, serverIp, uri_new))
        except error as e:
            # When error --> one is disconnected
            print(e)
            print("Closing connection with client and server.")
            connectionSocket.close()
            sendingSocket.close()
            break

if __name__ == "__main__":
    logName, alpha, listeningPort, proxyIp, serverIp = sys.argv[1:]
    listeningPort = int(listeningPort) ## port number specified as a command line argument
    alpha = float(alpha)
    
    listeningSocket = socket(AF_INET,SOCK_STREAM)# listening socket
    
    try:
        listeningSocket.bind(('', listeningPort))
    except error as e:
        print(e)
        
    listeningSocket.listen(1)
    print("The proxy is ready to receive on port", listeningPort)

    while True:
        connectionSocket, addr = listeningSocket.accept()
        handle_communication(connectionSocket, proxyIp, serverIp, listeningPort, alpha, logName)