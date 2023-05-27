# Brainfuck Assembler
A simple assembly language compiling to brainfuck. Just for fun.  

## Instructions
Every instruction takes the form
```
MNEMONIC{C} Operand1, Operand2
```
Where
- `MNEMONIC`: the name of the instruction
- `{C}`: An optional 'conditional' flag, which indicates that the instruction must only be executed if the last condition operation evaluated to true
- `Operand1`: First operand of the instruction, must always be a register name
- `Operand2`: Second operand of the instruction. Not all instructions have two operands.


The second operand can be:
- A register name. Eg `R1`
- A constant value (prefixed by the `#` symbol, eg `#3`)
- The memory address stored in a register (register name surrounded by `[]`, eg `[R3]`)

### Instruction reference
#### Generic operations
| Instruction | Description |
| -------- | ----------- |
| `MOV Reg, Operand` | Copies `Operand` to `Reg`  |
| `ADD Reg, Operand` | Adds `Operand` to the value contained in `Reg`, storing the result in `Reg`  |
| `OUT Reg` | Prints the content of `Reg` |

#### Conditions
| Instruction | Description |
| -------- | ----------- |
| `GT Reg, Operand` | Checks if `Reg` is greater than `Operand`, storing 1 in `CRR` if the condition is verified. |

#### Branching
| Instruction | Description |
| -------- | ----------- |
| `B Operand` | Jumps to the instruction referenced by `Operand`. This can either be a constant or a register |


## User Registers
User registers are available for use by the users.

| Register | Description |
| -------- | ----------- |
| `CRR`       | Condition result register. 1 If the latest contional operation evaluated to true, 0 otherwise. |
| `PC` | Program Counter, contains the address of the current istruction being executed |
| `R1` | General purpose register 1 |
| `R2` | General purpose register 2 |
| `R3` | General purpose register 3 |
| `R4` | General purpose register 4 |
| `R5` | General purpose register 5 |


## Example
### Assembly
```
    MOV R1, #5   ; Set R1 to 5
loop:
    ADD R2, #1   ; Add 1 to R2
    GT R1, R2    ; R1 > R2?
    BC loop      ; If yes, branch to loop
    OUT R1       ; Print R1
    OUT R2       ; Print R2
```
### Output
```
++++++
[-[-[-[-[-[-
>
>>>>>>>>[-]<<<<<<<<
>+<[>-]>[>]<
[-
    >>>>>>>>[-]+++++<<<<<<<<
]
+<[>-]>[>]<<->[-<+>]<
<]>
>>>>>>>>[-]+<<<<<<<<
>+<[>-]>[>]<
[-
    >>>>>>>>>+<<<<<<<<<
]
+<[>-]>[>]<<->[-<+>]<
<]>
>>>>>>>>[-]++<<<<<<<<
>+<[>-]>[>]<
[-
    >>>>>>[-]<<<<<<>>>>>>>>
[-<<<+<+>>>>]<<<<[->>>>+<<<<]>>>>>[-<<<<<<+>+>>>>>]<<<<<[->>>>>+<<<<<]>>>>><<<<[-<<<<+>+>>>]<<<[->>>+<<<]>>>
[-<<[<<->]>[>]<->>]<<[+]<<
[->>>>>+<<<<<]
<
]
+<[>-]>[>]<<->[-<+>]<
<]>
>>>>>>>>[-]+++<<<<<<<<
>+<[>-]>[>]<
[-
    >>>>>>[-<<<<<<+>+>>>>>]<<<<<[->>>>>+<<<<<]>>>>><<<<<<[-<<+++>>]
]
+<[>-]>[>]<<->[-<+>]<
<]>
>>>>>>>>[-]++++<<<<<<<<
>+<[>-]>[>]<
[-
    >>>>>>>>.<<<<<<<<
]
+<[>-]>[>]<<->[-<+>]<
<]>
>>>>>>>>[-]+++++<<<<<<<<
>+<[>-]>[>]<
[-
    >>>>>>>>>.<<<<<<<<<
]
+<[>-]>[>]<<->[-<+>]<
<]>

```