IRegisters = ["BJR", "FJR", "IC", "TR1", "TR2", "TR3", "TR4", "TR5"]
URegisters = ["CRR", "PC", "R1", "R2", "R3", "R4", "R5"]

Registers = IRegisters + URegisters


def check_reg(reg: str):
    if not reg in Registers:
        raise ValueError(f"Undefined register {reg}")


def check_ureg(reg: str):
    if not reg in URegisters:
        raise ValueError(f"Undefined register {reg}")


def address_of(reg: str):
    check_reg(reg)
    return Registers.index(reg)
