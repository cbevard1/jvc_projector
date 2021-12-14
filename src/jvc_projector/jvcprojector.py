"""Minimal library for controlling JVC Projectors with python.

This module implements the JVC IP control API. It should work for
most of their projectors.

Use `async` prefix for asynchronous versions of the commands, eg, async_power_on()

Example:
    Usage with the python console:

    >>> from jvcprojector import JVCProjectorClient
    >>> p = JVCProjectorClient('192.168.1.14')
    >>> p.is_on()
    False
    >>> p.command("pm_memory1")
"""

import asyncio
from .jvccommands import Commands, PowerStates
from datetime import datetime

class JVCProjectorClient:
    """This class handles sending and receiving information from the projector.

    Use `async` prefix for asynchronous versions of the commands, eg, async_power_on()

    Args:
        host (str): The ip address or hostname of the projector.
        port (int, optional): The port to connect to.
            Can be found in the network settings of the projector.
            Defaults to 20554.
        delay_seconds (float, optional): The amount of time to wait before being able to send another command.
            Defaults to 0.6.
        connect_timeout_seconds (int, optional): The amount of time to wait when trying to establish a connection.
            Defaults to 10.

    Attributes:
        host (str): The ip address or hostname of the projector.
        port (int): The port specified when initialising the class.

    Examples:
        >>> from jvcprojector import JVCProjectorClient
        >>> p = JVCProjectorClient('192.168.1.14')
        >>> p.is_on()
        False
        >>> p.command("pm_memory1")
    """

    def __init__(
            self,
            host: str,
            port: int = 20554,
            delay_seconds: float = 0.6,
            connect_timeout_seconds: int = 10,
    ) -> None:

        self.host: str = host
        self.port: int = port
        self._connect_timeout_seconds: int = connect_timeout_seconds
        self._delay_seconds: float = delay_seconds
        self._last_command_time = datetime.now()

    async def _async_send_command(self, operation: bytes) -> bytes:
        """Private method to send a raw command to the projector and receive a response.

        Args:
            operation (bytes): The raw command bytes. See jvccommands.py.

        Returns:
            bytes: The response from the projector.
                If the first byte of the command signifies an operation (b'!'),
                the response will be empty, b''
        """
        JVC_GREETING = b'PJ_OK'
        JVC_REQ = b'PJREQ'
        JVC_ACK = b'PJACK'

        await self._throttle()

        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), timeout=self._connect_timeout_seconds)
        except ConnectionRefusedError:
            raise JVCCannotConnectError("Could not connect to the projector. Check the Hostname/IP and ensure that 'Control4' is turned off in the network settings.")

        # 3 step handshake:
        # Projector sends PJ_OK, client sends PJREQ, projector replies with PJACK
        # first, after connecting, see if we receive PJ_OK. If not, raise exception
        if await reader.read(len(JVC_GREETING)) != JVC_GREETING:
            raise JVCHandshakeError("Projector did not reply with correct PJ_OK greeting.")

        # Now send PJREQ.
        writer.write(JVC_REQ)

        # Did the projector acknowledge?
        if await reader.read(len(JVC_ACK)) != JVC_ACK:
            raise JVCHandshakeError("Projector did not send PJACK.")

        # 3 step connection is verified, send the command
        writer.write(operation)

        ack = b"\x06\x89\x01" + operation[3:5] + b"\x0A"
        ACK = await reader.read(len(ack))

        result = b''
        wait_for_response = True if operation[0:1] == b'?' else False
        if ACK == ack:
            if wait_for_response:
                message = await reader.read(1024)
                result = message
        else:
            raise JVCCommunicationError("Unexpected ACK from projector")

        writer.close()

        self._last_command_time = datetime.now()

        return result

    def _send_command(self, operation):
        """Call async_send command synchronously"""
        return asyncio.run(self._async_send_command(operation))


    async def _throttle(self):
        """Throttles the comminication."""

        if self._delay_seconds == 0:
            return

        delta = (datetime.now() - self._last_command_time).total_seconds()
        if self._delay_seconds > delta:
            return await asyncio.sleep(self._delay_seconds - delta)
        return

    async def async_power_on(self) -> None:
        """Powers the projector on."""
        await self._async_send_command(Commands.power_on.value)

    def power_on(self) -> None:
        """Powers the projector on."""
        asyncio.run(self.async_power_on())

    async def async_power_off(self) -> None:
        """Powers the projector off."""
        await self._async_send_command(Commands.power_off.value)

    def power_off(self) -> None:
        """Powers the projector off."""
        asyncio.run(self.async_power_off())

    async def async_command(self, command_string: str) -> bool:
        """Send a known command to the projector.

        See the commands in jvccommands.Commands.

        Args:
            command_string (str): The name of the command in jvccommands.Commands

        Returns:
            bool: True if the command exists in jvccommands.Commands.
                False otherwise.
        """
        if not hasattr(Commands, command_string):
            return False
        else:
            await self._async_send_command(Commands[command_string].value)
            return True

    def command(self, command_string: str) -> bool:
        """Send a known command to the projector.

        See the commands in jvccommands.Commands.

        Args:
            command_string (str): The name of the command in jvccommands.Commands

        Returns:
            bool: True if the command exists in jvccommands.Commands.
                False otherwise.
        """
        return asyncio.run(self.async_command(command_string))

    async def async_get_mac(self) -> str:
        """Get the MAC address of the projector."""
        mac = await self._async_send_command(Commands.get_mac.value)
        if mac:
            return mac[5:-1].decode("ascii") # skip the header and end
        else:
            raise JVCCommunicationError("Unexpected response for get_mac()")

    def get_mac(self) -> str:
        """Get the MAC address of the projector."""
        return asyncio.run(self.async_get_mac())

    async def async_get_model(self) -> str:
        """Get the model string of the projector."""
        model = await self._async_send_command(Commands.model.value)
        if model:
            return model[5:-1].decode("ascii") # skip the header and end
        else:
            raise JVCCommunicationError("Unexpected response for get_model()")

    def get_model(self) -> str:
        """Get the model string of the projector."""
        return asyncio.run(self.async_get_model())

    async def async_power_state(self) -> str:
        """Fetch the power state."""
        message = await self._async_send_command(Commands.power_status.value)
        return PowerStates(message).name

    def power_state(self) -> str:
        """Fetch the power state."""
        return asyncio.run(self.async_power_state())

    async def async_is_on(self) -> bool:
        """Check if the projector is powered on."""
        on = ["lamp_on", "reserved"]
        return await self.async_power_state() in on

    def is_on(self) -> bool:
        """Check if the projector is powered on."""
        return asyncio.run(self.async_is_on())


class JVCCannotConnectError(Exception):
    """Exception when we can't connect to the projector"""
    pass

class JVCHandshakeError(Exception):
    """Exception when there was a problem with the 3 step handshake"""
    pass

class JVCCommunicationError(Exception):
    """Exception when there was a communication issue"""
    pass

