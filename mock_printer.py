import socket

HOST = "0.0.0.0"
PORT = 9100

print("=== Mock Zebra Printer ===")
print(f"Listening on TCP {PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen(1)

    while True:
        conn, addr = server.accept()

        with conn:
            print()
            print(f"Connection from {addr[0]}:{addr[1]}")

            data = conn.recv(4096)

            if data:
                print()
                print("=== PRINT JOB RECEIVED ===")
                print(data.decode("utf-8"))
                print("=== END PRINT JOB ===")
