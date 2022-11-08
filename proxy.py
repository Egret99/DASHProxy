import xml.etree.ElementTree as ET
from socket import *
import sys
import time

# Utility functions

def calculate_current_throughput(t1, t2, size, alpha, throughput):
    newThroughput = size*1.0/(t2-t1)
    throughput = alpha*newThroughput + (1-alpha)*throughput
    return throughput

def getBitrates(manifest_file):
    bitrates = []
    root = ET.fromstring(manifest_file)
    for representation in root.find("Period").find("AdaptationSet").findall("Representation"):
        bitrates.append(int(representation.get("bandwidth")))

    return bitrates

def transformUri(uri, throughput, bitrates):
    biggest_bitrate = bitrates[0]
    for bitrate in bitrates:
        if bitrate > biggest_bitrate and bitrate*1.5 <= throughput:
            biggest_bitrate = bitrate
    
    paths = uri.split("/")
    paths[0] = paths[0].split("_")[0] + "_" + biggest_bitrate + "bps"
    return "/var/www/html" + "/".join(paths)


# Connection functions

def receive_request(connectionSocket):
    request = connectionSocket.recv(2048).decode()
    uri = request.split("\n")[0].split(" ")[1]
    time = time.time()

    return (request, uri, time)

def connect_to_server(serverIp, proxyIp):
    sendingSocket = socket(AF_INET,SOCK_STREAM)
    try:
        sendingSocket.bind((proxyIp, 0))
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

def handle_communication(connectionSocket, proxyIp, serverIp, alpha):
    throughput = 0
    bitrates = []
    while True:
        try:
            request, uri, t1 = receive_request(connectionSocket)
            sendingSocket = connect_to_server(proxyIp, serverIp)
            if uri[-3:] == "mpd":
                uri_new = "/var/www/html" + uri.split(".")[0] + "_nolist.mpd"
                response_headers, file_chunks, size, t2 = request_file(sendingSocket, uri_new, request)
                return_file_to_client(connectionSocket, response_headers, file_chunks)

                # Get the correct manifest file and bitrates & also set initial throughput
                manifest_file = "".join([file_chunk.decode() for file_chunk in request_file(sendingSocket, "/var/www/html" + uri, request)[1]])
                bitrates = getBitrates(manifest_file)
                throughput = min(bitrates)
            else:
                uri_new = transformUri(uri, throughput, bitrates) # do some transformation based on bitrate
                response_headers, file_chunks, size, t2 = request_file(sendingSocket, uri_new, request)
                return_file_to_client(connectionSocket, response_headers, file_chunks)
                throughput = calculate_current_throughput(t1, t2, size, alpha, throughput)
        except error as e:
            # When error --> one is disconnected
            break


if __name__ == "__main__":
    log, alpha, listeningPort, proxyIp, serverIp = sys.argv[1:]
    listeningPort = int(listeningPort) ## port number specified as a command line argument
    alpha = float(alpha)
    
    listeningSocket = socket(AF_INET,SOCK_STREAM)# listening socket
    
    try:
        listeningSocket.bind(('', listeningPort))
    except error as e:
        print(e)
        
    listeningSocket.listen(1000)
    print("The proxy is ready to receive on port", listeningPort)

    while True:
        connectionSocket, addr = listeningSocket.accept()
        handle_communication(connectionSocket)