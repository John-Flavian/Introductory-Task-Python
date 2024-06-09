""" Cloned main module for load testing. """
from client_load_test import send_message


async def run_client() -> None:
    """ Asynchronously sends a message to the server. """
    await send_message("16;0;21;11;0;19;4;0;")


async def main() -> None:
    """ Asynchronously starts the client. """
    await run_client()
