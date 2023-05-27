#!/usr/bin/env python3

from __future__ import annotations

import click
from enum import Enum, auto
from dataclasses import dataclass
import re
from typing import Tuple, Dict
from copy import deepcopy

from assembler import Label, Instruction, Operand, OperandType, assemble

re_label = re.compile(r"\s*(?P<val>[\w_\d]+):")
re_addr = re.compile(r"\s*\[(?P<val>[\w_\d]+)\]")
re_word = re.compile(r"\s*(?P<val>[\w_\d]+)")
re_comma = re.compile(r"(?P<val>,)")
re_hex_const = re.compile(r"\s*#(?P<val>0x[A-F\d]+)")
re_dec_const = re.compile(r"\s*#(?P<val>[\d]+)(?!\w)")
re_comment = re.compile(r"\s*(?P<val>;.*)")


class TokenType(Enum):
    NEWLINE = auto()
    LABEL = auto()
    COMMA = auto()
    WORD = auto()
    CONSTANT = auto()
    ADDRESS = auto()
    COMMENT = auto()


token_regex = [
    (TokenType.LABEL, re_label),
    (TokenType.ADDRESS, re_addr),
    (TokenType.WORD, re_word),
    (TokenType.CONSTANT, re_hex_const),
    (TokenType.CONSTANT, re_dec_const),
    (TokenType.COMMA, re_comma),
    (TokenType.COMMENT, re_comment),
]

@dataclass
class Token:
    value: str
    type: TokenType
    line: int
    cols: Tuple[int, int]

    def __repr__(self):
        return f"{{{self.type.name}: {self.value} ({self.line}-{self.cols[0]}:{self.cols[1]})}}"

    def __str__(self):
        return self.__repr__()


@click.command()
@click.argument("file", type=click.File("r"), default="test.bfs")
@click.option("-o", "--output", type=click.File("w"), default="out.bf")
def bfas(file: click.File, output):
    """BrainFuck assembler"""

    bfas = file.readlines()
    # bfas = preprocessor(bfas)

    tokens = lexer(bfas)
    if tokens is None:
        exit(1)


    print(tokens)

    instructions, labels = parser(tokens)

    print(labels)
    print(instructions)

    bf = assemble(instructions, labels)
    output.write(bf)

def lexer(bfas: list(str)) -> (list[Token] | None):
    tokens: list[Token] = []

    line = 0
    for l in bfas:
        line += 1
        i = 0
        while i !=  len(l):
            found = False
            tk: TokenType
            rx: re.Pattern
            for (tk, rx) in token_regex:
                m: re.Match
                if (m := rx.match(l, i)) is not None:
                    tokens.append(Token(m.group("val"), tk, line, (m.start("val")+1, m.end("val")+1)))
                    i = m.end()
                    found = True
                    break
            if not found:
                rem = l[i:].strip()
                if len(rem) > 0:
                    print(f"Unrecognized token: {rem}")
                    return None
                break
        tokens.append(Token("", TokenType.NEWLINE, line, (len(l), len(l)+1)))
    return tokens

def parser(tokens: list[Token]) -> Tuple(list[Instruction], Dict[str, Label]):
    class ParserState(Enum):
        STATEMENT = auto()
        OPERAND_1 = auto()
        OPERAND_CONT = auto()
        OPERAND_2 = auto()
    
    state = ParserState.STATEMENT

    instructions = []
    labels = {}

    ic = 0
    curr_inst = Instruction("", [])

    def token_error(t: Token):
        print()
    
    def complete_instruction():
        nonlocal ic
        ic += 1
        instructions.append(deepcopy(curr_inst))

    for t in tokens:
        if t.type == TokenType.COMMENT:
            continue

        match state:
            case ParserState.STATEMENT:
                match t.type:
                    case TokenType.LABEL:
                        if t.value is labels:
                            print(f"Duplicate label: {t}")
                            exit(1)
                        labels[t.value] = Label(t.value, ic)
                    case TokenType.WORD:
                        curr_inst.name = t.value
                        state = ParserState.OPERAND_1
                    case TokenType.NEWLINE:
                        pass
                    case _:
                        print(f"Unexpected token: {t}")
                        exit(1)
            case ParserState.OPERAND_1:
                match t.type:
                    case TokenType.WORD:
                        curr_inst.operands = [Operand(t.value, OperandType.REFERENCE)]
                        state = ParserState.OPERAND_CONT
                    case TokenType.NEWLINE:
                        complete_instruction()
                        state = ParserState.STATEMENT
                    case _:
                        print(f"Unexpected token: {t}")
                        exit(1)
            case ParserState.OPERAND_CONT:
                match t.type:
                    case TokenType.COMMA:
                        state = ParserState.OPERAND_2
                    case TokenType.NEWLINE:
                        complete_instruction()
                        state = ParserState.STATEMENT
                    case _:
                        print(f"Unexpected token: {t}")
                        exit(1)
            case ParserState.OPERAND_2:
                match t.type:
                    case TokenType.WORD:
                        curr_inst.operands.append(Operand(t.value, OperandType.REFERENCE))
                        state = ParserState.OPERAND_CONT
                    case TokenType.ADDRESS:
                        curr_inst.operands.append(Operand(t.value, OperandType.ADDRESS))
                        state = ParserState.OPERAND_CONT
                    case TokenType.CONSTANT:
                        curr_inst.operands.append(Operand(t.value, OperandType.CONSTANT))
                        state = ParserState.OPERAND_CONT
                    case _:
                        print(f"Unexpected token: {t}")
                        exit(1)
    return (instructions, labels)


if __name__ == "__main__":
    bfas()
