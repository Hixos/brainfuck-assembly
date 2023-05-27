from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict
from registers import *

class OperandType(Enum):
    REFERENCE = auto()  # Could be register or label
    ADDRESS = auto()
    CONSTANT = auto()


@dataclass
class Operand:
    val: str
    type: OperandType

    def __repr__(self):
        return f"{{{self.type}: {self.val}}}"

    def __str__(self):
        match self.type:
            case OperandType.REFERENCE:
                return self.val
            case OperandType.ADDRESS:
                return f"[{self.val}]"
            case OperandType.CONSTANT:
                return f"[#self.val]"
            case _:
                raise ValueError("Unrecognized operand type")


@dataclass
class Instruction:
    name: str
    operands: list[Operand]

    def __repr__(self):
        s = f"{{{self.name} "
        for p in self.operands:
            s += f"{p.__repr__()} "
        return s[0:-1] + "}"

    def __str__(self):
        s = f"{self.name} "
        for p in self.operands:
            s += f"{p.__str__()} "
        return s[0:-1]


@dataclass
class Label:
    name: str
    ip: int

    def __repr__(self):
        return f"{{{self.ip}: {self.name}}}"

    def __str__(self):
        return f"{self.ip}: {self.name}"


class BFGen:
    def ptr(src: str, dst: str) -> str:
        src = address_of(src)
        dst = address_of(dst)

        if dst > src:
            return ">" * (dst - src)
        else:
            return "<" * (src - dst)

    def inc(val: int) -> str:
        return "+" * val

    def clr() -> str:
        return "[-]"
    
    def set(val: int) -> str:
        return "[-]" + "+"*val

    def mv(src: str, dst: str) -> str:
        # Assumes bp to be on src
        return f"[-{BFGen.ptr(src, dst)}+{BFGen.ptr(dst, src)}]"
    
    def cp(src: str, dst:str, tmp: str):
        # Assumes bp to be on src
        return f"[-{BFGen.ptr(src, dst)}+{BFGen.ptr(dst, tmp)}+{BFGen.ptr(tmp, src)}]{BFGen.ptr(src, tmp)}{BFGen.mv(tmp, src)}{BFGen.ptr(tmp, src)}"
    
    def set_pc(pc: int) -> str:
        # Note: assumes block pointer on FJR
        return BFGen.ptr("FJR", "PC") + BFGen.clr() + BFGen.inc(pc) + BFGen.ptr("PC", "FJR") + "\n"

    def fjump_wrap(inst: str) -> str:
        # Note: assumes block pointer on FJR at beginning and after inst
        # fmt: off
        return (
                ">+<"                   # IC = 1
                "[>-]"                  # if FJR == 0 -> IC = 0
                ">[>]<\n"               # ptr IC
                f"[-\n    {inst}\n]\n"  # if IC != 0 (aka FJR == 0), set IC = 0 and execute inst 
                "+<[>-]>[>]<<->[-<+>]<\n" # Decrement FJR if FJR > 0
        ) 
        # fmt: on

    def bjump_post() -> str:
        return "<]>\n"  #  mv BJR, loop, mv FJR
    
    def wrap(inst: str, pc: int) -> str:
        return BFGen.set_pc(pc) + BFGen.fjump_wrap(inst) + BFGen.bjump_post()
    
    def bjump_pre(ni: int) -> str:
        return BFGen.inc(ni) + "\n" + "[-"*ni + "\n>\n"
    
    def gt_setup(rega, regb):
        # Assumes bp to be on rega
        # out bp TR5
        cpa5 = BFGen.cp(rega, "TR5", "TR4") # Copy a to TR5
        cpb3 = BFGen.cp(regb, "TR3", "TR4") # Copy b to TR3
        cpa1 = BFGen.cp("TR5", "TR1", "TR2") # Copy a to TR1
        return f"{cpa5}{BFGen.ptr(rega, regb)}{cpb3}{BFGen.ptr(regb, 'TR5')}{cpa1}"
    
    def clear_cond(curr_ptr):
        return BFGen.ptr(curr_ptr, "CRR") + "[-]" +  BFGen.ptr("CRR", curr_ptr)

    def gt() -> str:
        # assumes bp to be on TR5
        # assumes TR1 = a, TR3 = b, TR5 = a
        # then TR1 = a > b
        # out bp TR1

        return "[-<<[<<->]>[>]<->>]<<[+]<<"

    def inot(a, dst):
        # assumes bp to be on a
        ad = BFGen.ptr(a, dst)
        da = BFGen.ptr(dst, a)
        return f"{ad}+{da}[[-]{ad}-{da}]"
    
    def cond(inst: str):
        return f"{BFGen.ptr('IC', 'CRR')}{BFGen.cp('CRR', 'IC', 'TR1')}{BFGen.ptr('CRR', 'IC')}[-{inst}]"


class BFI:
    def add(i: Instruction, labels: Dict[str, Label], pc: int) -> str:
        if len(i.operands) != 2:
            print("Not enough operands in ADD")
            exit(1)

        regadd = i.operands[0].val

        check_ureg(regadd)

        match i.operands[1].type:
            case OperandType.REFERENCE:
                regsrc = i.operands[1].val
                check_ureg(regsrc)
                t2s = BFGen.ptr("TR1", regsrc)
                s2d = BFGen.ptr(regsrc, regadd)
                d2t = BFGen.ptr(regadd, "TR1")
                # fmt: off
                return BFGen.ptr("IC", regsrc) + BFGen.mv(regsrc, "TR1") + BFGen.ptr(regsrc, "TR1") + (
                    f"[-{t2s}+{s2d}+{d2t}]"
                ) + BFGen.ptr("TR1", "IC")
                # fmt: on
            case OperandType.CONSTANT:
                val = i.operands[1].val
                return BFGen.ptr("IC", regadd) + "+"*int(val) + BFGen.ptr(regadd, "IC")
            case _:
                print("Unexpected operand type in ADD")
                exit(1)
    
    def mov(i: Instruction, labels: Dict[str, Label], pc: int) -> str:
        if len(i.operands) != 2:
            print("Not enough operands in MOV")
            exit(1)
        dstv = i.operands[0].val

        check_ureg(dstv)

        srct = i.operands[1].type
        srcv = i.operands[1].val
        if srct != OperandType.CONSTANT:
            print("Unexpected operand type in MOV")
            exit(1)

        return BFGen.ptr("IC", dstv) + BFGen.clr() + "+"*int(srcv) + BFGen.ptr(dstv, "IC")
        

    def out(i: Instruction, labels: Dict[str, Label], pc: int) -> str:
        if len(i.operands) != 1:
            print("Not enough operands in OUT")
            exit(1)
        dstv = i.operands[0].val

        check_ureg(dstv)
        
        return BFGen.ptr("IC", dstv) + "." + BFGen.ptr(dstv, "IC")

    def branch(i: Instruction, labels: Dict[str, Label], pc: int) -> str:
        if len(i.operands) != 1:
            print("Not enough operands in B")
            exit(1)
        dstv = i.operands[0].val
        
        if dstv in URegisters:
            cmd = ""
            cmd += BFGen.ptr("IC", "PC")
            cmd += BFGen.gt_setup("PC", dstv)
            cmd += BFGen.gt() + "\n"
            cmd += BFGen.cp('TR1', 'TR3', 'TR4')
            cmd += BFGen.ptr('TR1', 'TR3')
            cmd += BFGen.inot('TR3', 'TR2')
            cmd += BFGen.ptr('TR3', 'TR1') + "\n"

            #### Jump back
            # PC - DST + 1
            sub = f"{BFGen.ptr('TR1', 'PC')}{BFGen.cp('PC', 'TR3', 'TR5')}{BFGen.ptr('PC', dstv)}{BFGen.cp(dstv, 'TR4', 'TR5')}{BFGen.ptr(dstv, 'TR4')}[-<->]<"
            cmd += f"[{sub}\n+{BFGen.mv('TR3', 'BJR')}{BFGen.ptr('TR3', 'TR1')}-]\n"

            #### Jump fwd
            # DST - PC
            sub = f"{BFGen.ptr('TR2', 'PC')}{BFGen.cp('PC', 'TR4', 'TR5')}{BFGen .ptr('PC', dstv)}{BFGen.cp(dstv, 'TR3', 'TR5')}{BFGen.ptr(dstv, 'TR4')}[-<->]<"
            cmd += f">[{sub}{BFGen.mv('TR3', 'FJR')}{BFGen.ptr('TR3', 'TR2')}-]{BFGen.ptr('TR2', 'IC')}"

            return cmd
        else:
            if dstv not in labels:
                print("Undefined label")
                exit(1)

            lbl: Label = labels[dstv]
            
            if lbl.ip > pc:
                # Jump forward
                return BFGen.ptr("IC", "FJR") + BFGen.inc(lbl.ip - pc) + BFGen.ptr("FJR", "IC")
            else:
                # Jump back
                val = pc - lbl.ip + 1
                return BFGen.ptr("IC", "BJR") + BFGen.inc(val) + BFGen.ptr("BJR", "IC")             


    def gt(i: Instruction, labels: Dict[str, Label], pc: int) -> str:
        a = i.operands[0].val
        b = i.operands[1].val
        return f"{BFGen.clear_cond('IC')}{BFGen.ptr('IC', a)}\n{BFGen.gt_setup(a, b)}\n{BFGen.gt()}\n{BFGen.mv('TR1', 'CRR')}\n{BFGen.ptr('TR1', 'IC')}"

IPtr = {
    "ADD": BFI.add,
    "MOV": BFI.mov,
    "OUT": BFI.out,
    "GT": BFI.gt,
    "B": BFI.branch,
}

def assemble(instructions: list[Instruction], labels: Dict[str, Label]) -> str:
    bf = ""
    for (pc, i) in enumerate(instructions):
        if i.name.endswith("C") and i.name[:-1] in IPtr:
            istr = IPtr[i.name[:-1]](i, labels, pc)
            bf += BFGen.wrap(BFGen.cond(istr), pc)
        elif i.name in IPtr:
            istr = IPtr[i.name](i, labels, pc)
            bf += BFGen.wrap(istr, pc)
        else:
            print(f"Unrecognized instruction: {i.name}")
            exit(1)

    return BFGen.bjump_pre(len(instructions)) + bf