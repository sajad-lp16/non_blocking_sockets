"""Author: Sajad Tohidi Majd"""

"""
This script allows multiple clients to get connected to the server and echos
clients messages, and as the Interrupt Signal is triggered it will gracefully
shutdown the client connections after 2 seconds

NOTE: cant be used on production because it has some issues and written just for
learning reasons :)
"""

import asyncio
import signal
from asyncio import AbstractEventLoop
import socket


clients = []


class GraceFullExit(SystemExit):
    pass


def shutdown():    
    raise GraceFullExit()



async def cancel_tasks():
    closing_tasks = [asyncio.wait_for(task, 2) for task in clients]

    for closing_task in closing_tasks:
        try:
            await closing_task
        except asyncio.exceptions.TimeoutError:
            pass
    print("all tasks are now closed!\n")


async def echo_task(connection: socket.socket, loop: AbstractEventLoop):
    try:
        while data := await loop.sock_recv(connection, 1024):
            print(f"{connection.getpeername()} says {data.decode()}")
            if b"boom" in data:
                raise Exception("explosion!")
            await loop.sock_sendall(connection, data)
        print(f"{connection.getpeername()} is now offline!")
    except Exception as exc:
        print(exc)
    except asyncio.exceptions.CancelledError:
        await loop.sock_sendall(connection, b"aw body we are about to shutdown the server\r\n")
    finally:
        connection.close()


async def listen_for_connection(server: socket.socket, loop: AbstractEventLoop):
    while True:
        connection, address = await loop.sock_accept(server)
        print(f"{address} is now connected!")
        connection.setblocking(False)
        clients.append(asyncio.create_task(echo_task(connection, loop)))


async def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)
    server.bind(("127.0.0.1", 8000))

    server.listen()

    await listen_for_connection(server, asyncio.get_running_loop())

loop = asyncio.new_event_loop()
loop.add_signal_handler(signal.SIGINT, shutdown)


try:
    loop.run_until_complete(main())
except GraceFullExit:
    loop.run_until_complete(cancel_tasks())

finally:
    loop.close()

