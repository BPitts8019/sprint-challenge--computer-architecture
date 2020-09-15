"""CPU functionality."""

import sys

### Registers ###
R0 = 0x00
R1 = 0x01
R2 = 0x02
R3 = 0x03
R4 = 0x04
R5 = 0x05
R6 = 0x06
R7 = 0x07
PROGRAM_END = 0x04
SP = 0x07


### OP-Codes ###
# ALU
ADD = 0b10100000
SUB = 0b10100001
MUL = 0b10100010
DIV = 0b10100011
MOD = 0b10100100
INC = 0b01100101
DEC = 0b01100110
CMP = 0b10100111
AND = 0b10101000
NOT = 0b01101001
OR = 0b10101010
XOR = 0b10101011
SHL = 0b10101100
SHR = 0b10101101

# PC Mutators
CALL = 0b01010000
RET = 0b00010001
INT = 0b01010010
IRET = 0b00010011
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110
JGT = 0b01010111
JLT = 0b01011000
JLE = 0b01011001
JGE = 0b01011010

# Other
NOP = 0b00000000
HLT = 0b00000001
LDI = 0b10000010
LD = 0b10000011
ST = 0b10000100
PUSH = 0b01000101
POP = 0b01000110
PRN = 0b01000111
PRA = 0b01001000

### Bit Tools ###
ONE_BYTE = 0xff
ONE_BIT = 0x01
OP_SETS_INST = 0x04
NUM_OPERANDS = 0x06
CMP_CLEAR = 0b11111000
EQ = 0x01
GT = 0x02
LT = 0x04

### Stack ###
STACK_HEAD = 0xf4

### Exit Codes ###
DONE = 0
UNKNOWN_INSTRUCTION = 1
IO_ERROR = 2
STACK_OVERFLOW = 3


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.reg[SP] = STACK_HEAD
        self.pc = 0x00
        self.fl = 0x00

        self.perform_op = {}
        self.perform_op[LDI] = self._ldi
        self.perform_op[PRN] = self._prn
        self.perform_op[HLT] = self._hlt
        self.perform_op[PUSH] = self._push
        self.perform_op[POP] = self._pop
        self.perform_op[JMP] = self._jmp
        self.perform_op[JEQ] = self._jeq
        self.perform_op[JNE] = self._jne
        ### ALU Operations ###
        self.perform_op[ADD] = self._add
        self.perform_op[MUL] = self._mul
        self.perform_op[CMP] = self._cmp
        self.perform_op[AND] = self._and
        self.perform_op[OR] = self._or
        self.perform_op[XOR] = self._xor
        self.perform_op[NOT] = self._not
        self.perform_op[SHL] = self._shl
        self.perform_op[SHR] = self._shr
        self.is_running = False

    def _ldi(self, *operands):
        """LDI registerA

        Set the value of a register to an integer."""

        self.reg[operands[0]] = operands[1]

    def _prn(self, *operands):
        """PRN registerA

        Print numeric value stored in the given register."""
        print(self.reg[operands[0]])

    def _hlt(self, *operands):
        """HLT

        Halt the CPU (and exit the emulator)."""

        self.is_running = False

    def _add(self, *operands):
        """ADD registerA registerB

        Add the value in two registers and store the result in registerA."""
        self.alu("ADD", *operands)

    def _mul(self, *operands):
        """MUL registerA registerB

        Multiply the values in two registers together and store the result in registerA."""
        self.alu("MUL", *operands)

    def _cmp(self, *operands):
        """CMP registerA registerB

        Compare the values in two registers.
            • If they are equal, set the Equal E flag to 1, otherwise set it to 0.
            • If registerA is less than registerB, set the Less-than L flag to 1, otherwise set it to 0.
            • If registerA is greater than registerB, set the Greater-than G flag to 1, otherwise set it to 0."""
        self.alu("CMP", *operands)

    def _and(self, *operands):
        """AND registerA registerB

        Bitwise-AND the values in registerA and registerB, then store the result in registerA."""
        self.alu("AND", *operands)

    def _or(self, *operands):
        """OR registerA registerB

        Perform a bitwise-OR between the values in registerA and registerB, storing the result in registerA."""
        self.alu("OR", *operands)

    def _xor(self, *operands):
        """XOR registerA registerB

        Perform a bitwise-XOR between the values in registerA and registerB, storing the result in registerA."""
        self.alu("XOR", *operands)

    def _not(self, *operands):
        """NOT register`

        Perform a bitwise-NOT on the value in a register, storing the result in the register."""
        self.alu("NOT", *operands)

    def _shl(self, *operands):
        """SHL registerA registerB

        Shift the value in registerA left by the number of bits specified in registerB, filling the low bits with 0."""
        self.alu("SHL", *operands)

    def _shr(self, *operands):
        """SHR registerA registerB

        Shift the value in registerA right by the number of bits specified in registerB, filling the high bits with 0."""
        self.alu("SHR", *operands)

    def _pop(self, *operands):
        """POP registerA

        Pop the value at the top of the stack into the given register."""
        self.reg[operands[0]] = self.ram_read(self.reg[SP])
        if self.reg[SP] < STACK_HEAD:
            self.reg[SP] += 1

    def _push(self, *operands):
        """PUSH registerA

        Push the value in the given register on the stack."""
        if (self.reg[SP]-1) >= self.reg[PROGRAM_END]:
            self.reg[SP] -= 1
            self.ram_write(self.reg[SP], self.reg[operands[0]])
        else:
            print(f"Stack Overflow!!")
            self.trace()
            self._shutdown(STACK_OVERFLOW)

    def _jmp(self, *operands):
        """JMP register

        Jump to the address stored in the given register."""
        self.pc = self.reg[operands[0]]

    def _jeq(self, *operands):
        """JEQ register

        If equal flag is set (true), jump to the address stored in the given register."""
        if self.fl & EQ:
            self.pc = self.reg[operands[0]]
        else:
            self.pc += 2

    def _jne(self, *operands):
        """JNE register

        If E flag is clear (false, 0), jump to the address stored in the given register."""
        if not (self.fl & EQ):
            self.pc = self.reg[operands[0]]
        else:
            self.pc += 2

    def load(self, program_path):
        """Load a program into memory."""
        address = 0

        try:
            with open(program_path) as program:
                for line in program:
                    split_line = line.split("#")
                    instruction = split_line[0].strip()
                    if instruction != "":
                        self.ram[address] = int(instruction, 2)
                        address += 1
        except:
            print(f"Cannot open file at \"{program_path}\"")
            self._shutdown(IO_ERROR)

        # store end of program into PROGRAM_END register
        self.reg[PROGRAM_END] = address

    def _to_next_instruction(self, ir):
        # Meanings of the bits in the first byte of each instruction: AABCDDDD
        #   AA Number of operands for this opcode, 0-2
        #   B 1 if this is an ALU operation
        #   C 1 if this instruction sets the PC
        #   DDDD Instruction identifier
        isPcAlreadySet = ir >> OP_SETS_INST
        isPcAlreadySet = isPcAlreadySet & ONE_BIT
        if not isPcAlreadySet:
            self.pc += (ir >> NUM_OPERANDS) + 1

    def _shutdown(self, exit_code=DONE):
        print("Shutting Down...")
        sys.exit(exit_code)

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        # elif op == "SUB": etc
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "CMP":
            # clear the CMP flag bits
            self.fl &= CMP_CLEAR
            if self.reg[reg_a] < self.reg[reg_b]:
                self.fl |= LT
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.fl |= GT
            else:
                self.fl |= EQ
        elif op == "AND":
            self.reg[reg_a] &= self.reg[reg_b]
        elif op == "OR":
            self.reg[reg_a] |= self.reg[reg_b]
        elif op == "XOR":
            self.reg[reg_a] ^= self.reg[reg_b]
        elif op == "NOT":
            self.reg[reg_a] = ~self.reg[reg_a]
        elif op == "SHL":
            self.reg[reg_a] = self.reg[reg_a] << self.reg[reg_b]
        elif op == "SHR":
            self.reg[reg_a] = self.reg[reg_a] >> self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

        # Clamp results to one byte
        self.reg[reg_a] &= ONE_BYTE

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """
        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def ram_read(self, mar):
        return self.ram[mar]

    def ram_write(self, mar, mdr):
        self.ram[mar] = mdr

    def run(self):
        """Run the CPU."""
        print("Running...")
        self.is_running = True
        while self.is_running:
            instruction_reg = self.ram_read(self.pc)
            op_a = self.ram_read(self.pc + 1)
            op_b = self.ram_read(self.pc + 2)
            if instruction_reg in self.perform_op:
                self.trace()
                self.perform_op[instruction_reg](op_a, op_b)
                self._to_next_instruction(instruction_reg)
            else:
                print(f"Unknown Instruction {instruction_reg}")
                self._shutdown(UNKNOWN_INSTRUCTION)

        self._shutdown()
