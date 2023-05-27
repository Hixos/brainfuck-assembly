#!/usr/bin/env python3

from __future__ import annotations

import click
from enum import Enum
from registers import *

print_len = 15
print_reg = True

@click.command()
@click.argument("file", type=click.File("r"), default="out.bf")
def bfc(file: click.File):
    """BrainFuck compiler"""

    bf = file.read()
    program = compile(bf)
    
    machine =  BrainFuckMachine(program, 2048)
    res = machine.run()
    print("")
    machine.print_memory()
    if res == Result.END:
        exit(0)
    else:
        exit(1)

def compile(bf: str) -> list[Instruction]:
    program: list[Instruction] = [Instruction(ISet.NOP, 0)]
    loop_stack = []

    for (i, b) in enumerate(bf):
        match b:
            case "+":
                if program[-1].i == ISet.ADD:
                    program[-1].data += 1
                else:
                    program.append(Instruction(ISet.ADD, i, 1))
            case "-":
                if program[-1].i == ISet.ADD:
                    program[-1].data += -1
                else:
                    program.append(Instruction(ISet.ADD, i, -1))
            case ">":
                if program[-1].i == ISet.MV:
                    program[-1].data += 1
                else:
                    program.append(Instruction(ISet.MV, i, 1))
            case "<":
                if program[-1].i == ISet.MV:
                    program[-1].data += -1
                else:
                    program.append(Instruction(ISet.MV, i, -1))
            case ".":
                program.append(Instruction(ISet.OUT, i, 0))
            case "!":
                program.append(Instruction(ISet.DBG, i, 0))
            case "[":
                # Temporary we will now where to jump to when we encounter the end of the loop
                program.append(Instruction(ISet.JZ, i, 0))
                loop_stack.append(len(program) - 1)
            case "]":
                addr = loop_stack.pop()
                program.append(Instruction(ISet.JMP, i, addr))
                program[addr].data = len(program)
            case _:
                pass

    return program


class ISet(Enum):
    NOP = 0     # NOP
    ADD = 1     # ADD, value    adds 'value' to the current memory cell
    MV = 2      # MV, offset    moves the memory pointer by 'offset'
    JMP = 5     # JMP, ptr      sets the program counter to 'ptr'
    JZ = 6      # JZ, ptr       sets the pc to 'ptr' only if the current cell is 0
    OUT = 7     # OUT           prints the value of the current cell
    DBG = 8     # DBG           debug instruction, prints the current state of the memory


class Instruction:
    i: ISet
    data: int
    bfp: int # Pointer to the original brainfuck instruction

    def __init__(self, instruction: ISet, bfp: int, data: int = 0):
        self.i = instruction
        self.data = data
        self.bfp = bfp

    def __repr__(self):
        return f"{self.i.name} {self.data}  #{self.bfp}"

    def __str__(self):
        return self.__repr__()


class Result(Enum):
    OK = 0
    END = 1
    SEGFAULT = 2
    BUSFAULT = 3


class BrainFuckMachine:
    def __init__(self, program, data_size=256, memory_size=256):
        self.program = program
        self.data_size = data_size
        self.memory_size = memory_size

        self.memory = [0] * memory_size
        self.pc = 0  # Program counter
        self.last_pc = 0
        self.mp = 0  # Memory pointer

    def reset(self):
        self.memory = [0] * self.memory_size
        self.pc = 0
        self.last_pc = 0
        self.mp = 0

    def run(self) -> Result:
        res = Result.OK
        while res == Result.OK:
            res = self.step()
        
        match res:
            case Result.BUSFAULT:
                ins: Instruction = self.program[self.last_pc]
                print(f"Error: Bus Fault after instruction {ins.bfp}")
            case Result.SEGFAULT:
                ins: Instruction = self.program[self.pc]
                print(f"Error: Segmentation Fault at instruction {ins.bfp}")
        return res

    def step(self) -> Result:
        if self.pc < 0 or self.pc > len(self.program):
            return Result.BUSFAULT

        i: Instruction = self.program[self.pc]
        match i.i:
            case ISet.NOP:
                self.pcinc()
            case ISet.ADD:
                if self.mp < 0 or self.mp >= self.memory_size:
                    return Result.SEGFAULT

                self.memory[self.mp] += i.data
                self.memory[self.mp] = self.memory[self.mp] % self.data_size
                self.pcinc()
            case ISet.MV:
                self.mp += i.data
                self.pcinc()
            case ISet.JMP:
                self.pcset(i.data)
            case ISet.JZ:
                if self.memory[self.mp] == 0:
                    self.pcset(i.data)
                else:
                    self.pcinc()
            case ISet.OUT:
                print(f"{self.memory[self.mp]} ", end="")
                self.pcinc()
            case ISet.DBG:
                self.print_memory()
                self.pcinc()

        if self.pc == len(self.program):
            return Result.END
        else:
            return Result.OK

    def print_memory(self, length=print_len):
        print("")
        if length == None:
            length = self.memory_size
        w = max(len(str(self.memory_size - 1)), len(str(self.data_size - 1))) + 1

        for i in range(length):
            if print_reg:
                if i < len(Registers):
                    n = f"{Registers[i]}"
                else:
                    n = f"{i-len(Registers)}"
            else:
                n = f"{i}"
            if i == self.mp:
                n = f"{n}*"
                print(f"{n:<{w}}", end="")
            else:
                print(f"{n:<{w}}", end="")

        print("")
        for i in range(length):
            val = self.memory[i]
            print(f"{val:<{w}}", end="")
        print("")

    def pcset(self, value):
        self.last_pc = self.pc
        self.pc = value

    def pcinc(self, offset = 1):
        self.pcset(self.pc + offset)


if __name__ == "__main__":
    bfc()
