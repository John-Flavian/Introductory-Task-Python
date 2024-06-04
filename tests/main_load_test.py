""" Cloned main module for load testing. """

from client_load_test import send_message


async def run_client() -> None:
    """
    Asynchronously sends a message to the server.

    This function uses the `send_message` coroutine to send a
        message to the server.
        The message sent is "16;0;21;11;0;19;4;0;".

    Parameters:
    None

    Returns:
    None
    """
    await send_message("16;0;21;11;0;19;4;0;")


async def main() -> None:
    """
    Asynchronously starts the client.

    This function calls the `run_client` function to start
        the client and send a message to the server.

    Parameters:
    None

    Returns:
    None
    """
    await run_client()
