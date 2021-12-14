import asyncio
from jvccommands import Commands, PowerStates, ACKs

class JVCProjectorClient():
    """JVC Projector Control"""

    def __init__(
            self,
            host: str,
            port: int = 20554,
            delay_seconds: float = 0.6,
            connect_timeout: int = 60,
    ) -> None:

        "Initialize the connection with the projector"
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.delay = delay_seconds

    async def _send_command(self, operation):
        JVC_GREETING = b'PJ_OK'
        JVC_REQ = b'PJREQ'
        JVC_ACK = b'PJACK'
        result = False

        reader, writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), timeout=self.connect_timeout)

        # jvc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # jvc_sock.settimeout(self.connect_timeout)
        # jvc_sock.connect((self.host, self.port)) # connect to projector

        # 3 step handshake:
        # Projector sends PJ_OK, client sends PJREQ, projector replies with PJACK
        # first, after connecting, see if we receive PJ_OK. If not, raise exception
        if await reader.read(len(JVC_GREETING)) != JVC_GREETING:
            raise JVCHandshakeError("Projector did not reply with correct PJ_OK greeting")

        # try sending PJREQ, if there's an error, raise exception
        # try:
        #     writer.write(JVC_REQ)
        # except socket.error as e:
        #     raise Exception("Socket exception when sending PJREQ")
        writer.write(JVC_REQ)

        # see if we receive PJACK, if not, raise exception
        if await reader.read(len(JVC_ACK)) != JVC_ACK:
            raise JVCHandshakeError("Projector did not send PJACK")

        # 3 step connection is verified, send the command
        writer.write(operation)

        ack = b"\x06\x89\x01" + operation[3:5] + b"\x0A"
        ACK = await reader.read(len(ack))

        result = None
        wait_for_response = True if operation[0:1] == b'?' else False
        if ACK == ack:
            if wait_for_response:
                message = await reader.read(1024)
                result = message
        else:
            raise JVCCommunicationError("Unexpected ACK from projector")

        writer.close()

        await asyncio.sleep(self.delay)

        return result

    async def power_on(self):
        return await self._send_command(Commands.power_on.value)

    async def power_off(self):
        return await self._send_command(Commands.power_off.value)

    async def command(self, command_string):
        if not hasattr(Commands, command_string):
            return False
        else:
            await self._send_command(Commands[command_string].value)
            return True

    async def get_mac(self):
        mac = await self._send_command(Commands.get_mac.value)
        if mac is not None:
            return mac[5:-1].decode("ascii")
        else:
            raise JVCCommunicationError("Unexpected response for get_mac()")

    async def get_model(self):
        model = await self._send_command(Commands.model.value)
        if model is not None:
            return model[5:-1].decode("ascii")
        else:
            raise JVCCommunicationError("Unexpected response for get_model()")

    async def power_state(self):
        message = await self._send_command(Commands.power_status.value)
        return PowerStates(message).name

    async def is_on(self):
        on = ["lamp_on", "reserved"]
        return await self.power_state() in on


class JVCCannotConnectError(Exception):
    """Exception when we can't connect to the projector"""
    pass

class JVCHandshakeError(Exception):
    """Exception when there was a problem with the 3 step handshake"""
    pass

class JVCCommunicationError(Exception):
    """Exception when there was a problem with the 3 step handshake"""
    pass

if __name__=="__main__":

    async def main():
        p = JVCProjectorClient("192.168.1.14")
        a = await p.is_on()
        print(a)
        b = await p.get_mac()
        print(b)
        c = await p.get_model()
        print(c)

    asyncio.run(main())
