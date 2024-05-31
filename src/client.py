"""Module providing a function to send a message to the server."""
import asyncio
import ssl
import json
import socket
import os

# Get the directory of the current script
src_dir = os.path.dirname(os.path.abspath(__file__))

# Go one level above
parent_dir = os.path.dirname(src_dir)

# Construct the full path to the config file
config_path = os.path.join(parent_dir, 'config/config.json')


# Load configuration
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)


HOST = config.get("host", "localhost")
PORT = config.get("port", 8080)
PROMPT = config.get("prompt", False)
QUERY = config.get("query", "hi")

USE_SSL = config.get("use_ssl", False)
CERTFILE = os.path.join(parent_dir, config.get("certificate_file"))
KEYFILE = os.path.join(parent_dir, config.get("key_file"))


async def send_message(message):
    """ Function to send a message to the server. """
    try:
        if USE_SSL:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            # Additional options to disable SSL verification (dev mode)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
        else:
            context = None
        reader, writer = await asyncio.open_connection(
            # '135.181.96.160',
            # 44445,
            HOST,
            PORT,
            ssl=context
            )
        print("Connected to the server.")
        writer.write(message.encode())
        await writer.drain()
        data = await reader.read(100)
        print(f"Received: {data.decode()}")
        writer.close()
        await writer.wait_closed()
    except ssl.SSLError as ssl_err:
        print(f"SSL error occurred: {ssl_err}")
    except socket.gaierror as socket_err:
        print(f"Socket error occurred: {socket_err}")
    except ConnectionRefusedError:
        print("Connection refused by the server.")
    except ConnectionResetError:
        print("Connection reset by the server.")
    except asyncio.TimeoutError:
        print("Connection timed out.")
    finally:
        if 'writer' in locals():
            writer.close()
            await writer.wait_closed()


async def main():
    """ Function to start the client. """
    if config.get("prompt", False):
        search_text = input("Please enter the search text: ")
    else:
        search_text = config.get("query", "hi")

    await send_message(search_text)

# This allows the script to be run directly
if __name__ == "__main__":
    asyncio.run(main())
