"""Module providing a function to handle asynchronous client connections."""
import asyncio
import json
import ssl
import os
from datetime import datetime
import threading
# import signal

# Watchdog imports
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler


# Get the directory of the current script
src_dir = os.path.dirname(os.path.abspath(__file__))
# Go one level above
parent_dir = os.path.dirname(src_dir)
# Construct the full path to the config file
config_dir_path = os.path.join(parent_dir, 'config/config.json')


# Load configuration function
def load_config(config_path):
    """ Load the configuration. """
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


# Define variables
config = load_config(config_dir_path)
USE_SSL = config.get("use_ssl", False)
CERTFILE = os.path.join(parent_dir, config.get("certificate_file"))
KEYFILE = os.path.join(parent_dir, config.get("key_file"))
DEV_MODE = config.get("development", False)
BUFFER_SIZE = 1024

linuxpath = os.path.join(parent_dir, config.get("txt_file"))
REREAD_ON_QUERY = config.get("reread_on_query", False)


def load_txt_file(file_path):
    """ Load the contents of the text file. """
    try:
        contents = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                contents.append(line.strip())
            return contents
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except IOError as e:
        print(f"IOError occurred: {e}")
    return None


# Load the contents of the text file
INITIAL_FILE_CONTENTS = load_txt_file(linuxpath)


def search(contents, query):
    """ Search for the query in the specified text file and return. """
    try:
        for line in contents:
            if query == line.strip():
                return 'STRING EXISTS'
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {linuxpath}") from e
    except IOError as e:
        raise IOError(f"IOError occurred: {e}") from e
    return 'STRING NOT FOUND'


async def handle_client(reader, writer):
    """Function handling an asynchronous client connection."""
    start_time = time.time()
    client_ip = writer.get_extra_info('peername')[0]
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break
            message = data.decode('utf-8').strip()
            contents = []

            if REREAD_ON_QUERY:
                contents = load_txt_file(linuxpath)
            else:
                contents = INITIAL_FILE_CONTENTS

            search_results = search(contents, message)

            # Send a response back to the client
            response = f"{search_results}" + "\n"
            writer.write(response.encode())
            await writer.drain()

            # Log the details of the query
            execution_time = (time.time() - start_time) * 1000
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_message = (
                f"DEBUG: Time: {timestamp}, IP: {client_ip}, "
                f"Query: {message}, Execution Time: {execution_time:.2f} ms"
            )
            print(log_message)
    except asyncio.IncompleteReadError as e:
        raise asyncio.IncompleteReadError(
            f"Error: Incomplete read error: {e}",
            e.partial
        ) from e
    except ConnectionResetError as e:
        raise ConnectionResetError(
            f"Error: Connection reset by the server: {e}"
        ) from e
    finally:
        print("Closing connection")
        writer.close()
        await writer.wait_closed()


def create_ssl_context():
    """ Function to create the SSL context. """
    cert_missing = not os.path.exists(CERTFILE) or not CERTFILE
    key_missing = not os.path.exists(KEYFILE) or not KEYFILE
    if cert_missing or key_missing:
        raise FileNotFoundError("SSL certificate or key file not found")
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    return context


async def main():
    """ Function to start the server. """
    server = await asyncio.start_server(
        handle_client,
        'localhost',
        8080,
        ssl=create_ssl_context() if USE_SSL else None
    )

    address = server.sockets[0].getsockname()
    print(f'Serving on {address}')
    await server.serve_forever()


if __name__ == "__main__":
    # Function to start the server
    if DEV_MODE:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        path = sys.argv[1] if len(sys.argv) > 1 else '.'
        logging.info('start watching directory %s', path)
        event_handler = LoggingEventHandler()
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        try:
            thread1 = threading.Thread(target=asyncio.run(main()))
            thread2 = threading.Thread(target=asyncio.run(main()))
            thread1.start()
            thread2.start()
            thread1.join()
            thread2.join()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Server stopped manually.")
        finally:
            observer.stop()
            observer.join()
    else:
        try:
            thread1 = threading.Thread(target=asyncio.run(main()))
            thread2 = threading.Thread(target=asyncio.run(main()))
            thread1.start()
            thread2.start()
            thread1.join()
            thread2.join()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Server stopped manually.")
        finally:
            print("Server stopped.")
