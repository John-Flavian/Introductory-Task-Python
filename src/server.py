"""Module providing a function to handle asynchronous client connections."""
import asyncio
import json
import ssl
import os
from datetime import datetime
import threading
import time

# Get the directory of the current script
src_dir = os.path.dirname(os.path.abspath(__file__))
# Go one level above
parent_dir = os.path.dirname(src_dir)
# Construct the full path to the config file
config_dir_path = os.path.join(parent_dir, 'config/config.json')


# Load configuration function
def load_config(config_path: str) -> dict[str, str]:
    """ Loads the configuration from a JSON file. """
    try:
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data or {}
    except FileNotFoundError as e:
        exception = FileNotFoundError(
            f"Error: The file '{config_path}' does not exist."
            )
        raise exception from e
    except PermissionError as e:
        raise PermissionError(
            f"Error: Permission denied for file '{config_path}'."
        ) from e
    except IsADirectoryError as e:
        raise IsADirectoryError(
            f"Error: The path '{config_path}' is a directory, not a file."
        ) from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Error: The file '{config_path}' contains invalid JSON.",
            doc=config_path,
            pos=0
        ) from e
    return {}


# Define variables
config = load_config(config_dir_path)
USE_SSL = config.get("use_ssl", False)
CERTFILE = os.path.join(parent_dir, config.get("certificate_file", ''))
KEYFILE = os.path.join(parent_dir, config.get("key_file", ''))
BUFFER_SIZE = 1024
HOST = config.get("server_host", "127.0.0.1")
PORT = config.get("server_port", 8001)

linuxpath = os.path.join(parent_dir, config.get("txt_file", ''))
REREAD_ON_QUERY = config.get("reread_on_query", False)


def load_txt_file(file_path: str) -> list[str]:
    """Load the contents of the text file located at the file path."""
    try:
        contents = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                contents.append(line.strip())
        return contents
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Error: The file '{file_path}' was not found."
        ) from e
    except PermissionError as e:
        raise PermissionError(
            f"Error: Permission denied for file '{file_path}'."
        ) from e
    except IsADirectoryError as e:
        raise IsADirectoryError(
            f"Error: The path '{file_path}' is a directory, not a file."
        ) from e
    except IOError as e:
        raise IOError(
            f"Error: An I/O error occurred: {e}"
            ) from e
    return []


# Load the contents of the text file
INITIAL_FILE_CONTENTS = load_txt_file(linuxpath)


def search(contents: list[str], query: str) -> str:
    """ Search for the specified query in the given text contents """
    if query in contents:
        return 'STRING EXISTS'
    return 'STRING NOT FOUND'


async def handle_client(
                        reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter) -> None:
    """ Handle an asynchronous client connection. """
    start_time = time.time()
    client_ip = writer.get_extra_info('peername')[0]
    try:
        while True:
            # Read the message from the client
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break
            message = data.decode('utf-8').strip()
            contents = []

            # Check if the contents should be reloaded
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
        raise asyncio.IncompleteReadError(e.partial, e.expected) from e
    except ConnectionResetError as e:
        raise ConnectionResetError(
            f"Error: Connection reset by the server: {e}"
        ) from e
    finally:
        print("Closing connection")
        writer.close()
        await writer.wait_closed()


def create_ssl_context() -> ssl.SSLContext:
    """ Create and return an SSL context for secure client connections. """
    cert_missing = not os.path.exists(CERTFILE) or not CERTFILE
    key_missing = not os.path.exists(KEYFILE) or not KEYFILE
    if cert_missing or key_missing:
        raise FileNotFoundError("SSL certificate or key file not found")
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    return context


async def main() -> None:
    """ Start the server and serve client connections. """
    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT,
        ssl=create_ssl_context() if USE_SSL else None
    )

    address = server.sockets[0].getsockname()
    print(f'Serving on {address}')
    await server.serve_forever()


if __name__ == "__main__":
    # Function to start the server
    # Run multiple threads in production
    try:
        # Run two threads per CPU core
        cpu_count = os.cpu_count()
        if cpu_count is None:
            # Fallback in case os.cpu_count() returns None
            MAX_WORKERS = 8
        else:
            MAX_WORKERS = cpu_count * 2

        threads = []

        print(f"Number of CPU cores / threads: {MAX_WORKERS}")

        # Create and start threads
        for _ in range(MAX_WORKERS):
            thread = threading.Thread(target=asyncio.run(main()))
            threads.append(thread)
            thread.start()

        # Join threads
        for thread in threads:
            thread.join()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped manually.")
    finally:
        print("Server stopped.")
