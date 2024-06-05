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
    """
        Load the configuration from a JSON file.

    This function reads a JSON file from the specified path
        and loads its content into a dictionary.
    If the file cannot be found, read, or parsed, appropriate
        error messages are raised and {} is returned.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        Optional[Dict[str, str]]:
            A dictionary containing the configuration data,
            or {} if an error occurs.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        PermissionError: If the file cannot be accessed due to
            insufficient permissions.
        IsADirectoryError: If the specified path is a directory, not a file.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    try:
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
DEV_MODE = config.get("development", False)
BUFFER_SIZE = 1024
HOST = config.get("server_host", "127.0.0.1")
PORT = config.get("server_port", 7000)

linuxpath = os.path.join(parent_dir, config.get("txt_file", ''))
REREAD_ON_QUERY = config.get("reread_on_query", False)


def load_txt_file(file_path: str) -> list[str]:
    """
    Load the contents of the text file located at the specified file path.

    Args:
        file_path (str): The path to the text file.

    Returns:
        list[str]: A list of strings, where each string is a line
            from the text file.

    Raises:
        FileNotFoundError: If the file at the specified path does not exist.
        PermissionError: If the user does not have permission to read the file.
        IsADirectoryError: If the specified path is a directory, not a file.
        IOError: If an I/O error occurs while reading the file.

    This function attempts to open the file at the specified path
        and read its contents.
    Each line of the file is stripped of leading and trailing whitespace
        and added to a list.
    If the file is not found, permission is denied, or the path is a directory,
        an appropriate error is raised.
    If any other I/O error occurs, an IOError is raised with a message
        indicating the cause of the error.

    If the file is successfully read, the contents of the file are returned
        as a list of strings.

    Note:
        The file is opened in 'utf-8' encoding mode.
    """
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
    """
    Search for the specified query in the given text contents and
        return a message indicating whether the query was found or not.

    Args:
        contents (list[str]): The text contents to search in.
        query (str): The query to search for.

    Returns:
        str: A message indicating whether the query was found or not.

    This function searches for the specified query in the given text contents.
    If the query is found, it returns the message 'STRING EXISTS'.
    If the query is not found, it returns the message 'STRING NOT FOUND'.

    Note:
        This function performs a simple string comparison to check
            if the query is present in the contents.
        It does not perform any advanced text processing or
            searching algorithms.
    """
    if query in contents:
        return 'STRING EXISTS'
    return 'STRING NOT FOUND'


async def handle_client(
                        reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter) -> None:
    """
    Handle an asynchronous client connection.

    Args:
        reader (asyncio.StreamReader): The reader object used to read data
            from the client.
        writer (asyncio.StreamWriter): The writer object used to write
            data to the client.

    This function handles an asynchronous client connection.
    It reads data from the client, processes the data, and sends a response
        back to the client.
    It also logs the details of the query and the execution time.

    The function reads data from the client using the `reader` object in
        chunks of size `BUFFER_SIZE`.
    If the received data is empty, it breaks out of the loop.
    The received data is decoded from utf-8 and stripped of leading and
        trailing whitespace.

    The function then searches for the query in the specified text contents.
    If `REREAD_ON_QUERY` is `True`, it loads the text file using the
        `load_txt_file` function.
    Otherwise, it uses the `INITIAL_FILE_CONTENTS` list.

    The search results are then sent back to the client as a response.
    The response is a string indicating whether the query was found or not.

    The function also logs the details of the query, including the
        client's IP address, the query itself, and the execution time.
    The execution time is calculated by subtracting the start time
        of the function from the current time.
    """
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
    """
    Create and return an SSL context for secure client connections.

    Returns:
        ssl.SSLContext: The SSL context object.

    Raises:
        FileNotFoundError: If the SSL certificate or key file is not found.

    This function creates and returns an SSL context for
        secure client connections.
    It first checks if the SSL certificate and key files exist.
    If either the certificate file or the key file is missing,
        a `FileNotFoundError` is raised.

    The function then creates a default SSL context using
        `ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)`.
    It loads the certificate chain and private key from the specified
        certificate and key files using
            `context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)`.

    Finally, the SSL context is returned.

    Note:
        The SSL certificate and key files are expected to be in PEM format.
    """
    cert_missing = not os.path.exists(CERTFILE) or not CERTFILE
    key_missing = not os.path.exists(KEYFILE) or not KEYFILE
    if cert_missing or key_missing:
        raise FileNotFoundError("SSL certificate or key file not found")
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    return context


async def main() -> None:
    """
    Start the server and serve client connections.

    This function starts the server and serves client connections.
    It creates a server using `asyncio.start_server`
        and sets the server's address to 'localhost' and port to 8080.
    If `USE_SSL` is `True`, it creates an SSL context using the
        `create_ssl_context` function and sets it as the
        SSL context for the server.

    The server is then started using `await server.serve_forever()`.
    This function blocks until the server is stopped.

    Note:
        The server is started using `asyncio.start_server`,
        which is an asynchronous function.
        The function returns immediately after starting the server.
    """
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
