"""Commands for the jvc_projector library."""

from enum import Enum

# Headers
OPR = b"!\x89\x01"  # operation
REF = b"?\x89\x01"  # reference
RES = b"@\x89\x01"  # response
PACK = b"\x06\x89\x01"  # projector ack


class Commands(Enum):
    # power commands
    power_on = OPR + b"PW1\n"
    power_off = OPR + b"PW0\n"

    # lens memory commands
    memory1 = OPR + b"INML0\n"
    memory2 = OPR + b"INML1\n"
    memory3 = OPR + b"INML2\n"
    memory4 = OPR + b"INML3\n"
    memory5 = OPR + b"INML4\n"

    # input commands
    hdmi1 = OPR + b"IP6\n"
    hdmi2 = OPR + b"IP7\n"

    # picture mode commands
    pm_cinema = OPR + b"PMPM01\n"
    pm_hdr = OPR + b"PMPM04\n"
    pm_natural = OPR + b"PMPM03\n"
    pm_film = OPR + b"PMPM00\n"
    pm_THX = OPR + b"PMPM06\n"
    pm_user1 = OPR + b"PMPM0C\n"
    pm_user2 = OPR + b"PMPM0D\n"
    pm_user3 = OPR + b"PMPM0E\n"
    pm_user4 = OPR + b"PMPM0F\n"
    pm_user5 = OPR + b"PMPM10\n"
    pm_user6 = OPR + b"PMPM11\n"
    pm_hlg = OPR + b"PMPM14\n"

    # low latency enable/disable
    pm_low_latency_enable = OPR + b"PMLL1\n"
    pm_low_latency_disable = OPR + b"PMLL0\n"

    # mask commands
    mask_off = OPR + b"ISMA2\n"
    mask_custom1 = OPR + b"ISMA0\n"
    mask_custom2 = OPR + b"ISMA1\n"
    mask_custom3 = OPR + b"ISMA3\n"

    # lamp commands
    lamp_high = OPR + b"PMLP1\n"
    lamp_low = OPR + b"PMLP0\n"

    # menu controls
    menu = OPR + b"RC732E\n"
    menu_down = OPR + b"RC7302\n"
    menu_left = OPR + b"RC7336\n"
    menu_right = OPR + b"RC7334\n"
    menu_up = OPR + b"RC7301\n"
    menu_ok = OPR + b"RC732F\n"
    menu_back = OPR + b"RC7303\n"

    # Lens Aperture commands
    aperture_off = OPR + b"PMDI0\n"
    aperture_auto1 = OPR + b"PMDI1\n"
    aperture_auto2 = OPR + b"PMDI2\n"

    # Anamorphic commands
    anamorphic_off = OPR + b"INVS0\n"
    anamorphic_a = OPR + b"INVS1\n"
    anamorphic_b = OPR + b"INVS2\n"
    anamorphic_c = OPR + b"INVS3\n"

    # MAC Address query
    get_mac = REF + b"LSMA\n"

    # model query
    model = REF + b"MD\n"

    # power status query commands
    power_status = REF + b"PW\n"
    current_input = REF + b"IP\n"
    signal_active = REF + b"SC\n"


class Responses(Enum):
    standby = RES + b"PW0\n"
    cooling = RES + b"PW2\n"
    emergency = RES + b"PW4\n"

    # on some projectors like the DLA-X5900, the status
    # is returned as the "reserved" on below when the
    # projector lamp is warming up and "lamp_on" when
    # the lamp is on
    lamp_on = RES + b"PW1\n"
    reserved = RES + b"PW3\n"

    hdmi1 = RES + b"IP6\n"
    hdmi2 = RES + b"IP7\n"

    no_signal = RES + b"SC0\n"
    active_signal = RES + b"SC1\n"
