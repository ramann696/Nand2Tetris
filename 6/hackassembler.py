# Hack Assembler in Python
# Structure: Parser, Code, SymbolTable, Main

import sys
import re

# Predefined symbols
PREDEFINED_SYMBOLS = {
    'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
    'SCREEN': 16384, 'KBD': 24576,
    **{f'R{i}': i for i in range(16)}
}

# =================== SymbolTable ===================
class SymbolTable:
    def __init__(self):
        self.table = PREDEFINED_SYMBOLS.copy()

    def add_entry(self, symbol, address):
        self.table[symbol] = address

    def contains(self, symbol):
        return symbol in self.table

    def get_address(self, symbol):
        return self.table[symbol]

# =================== Code ===================
class Code:
    dest_table = {
        None:   '000',
        'M':    '001',
        'D':    '010',
        'MD':   '011',
        'A':    '100',
        'AM':   '101',
        'AD':   '110',
        'AMD':  '111'
    }

    comp_table = {
        '0':   '0101010', '1':   '0111111', '-1':  '0111010',
        'D':   '0001100', 'A':   '0110000', '!D':  '0001101',
        '!A':  '0110001', '-D':  '0001111', '-A':  '0110011',
        'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110',
        'A-1': '0110010', 'D+A': '0000010', 'D-A': '0010011',
        'A-D': '0000111', 'D&A': '0000000', 'D|A': '0010101',
        'M':   '1110000', '!M':  '1110001', '-M':  '1110011',
        'M+1': '1110111', 'M-1': '1110010', 'D+M': '1000010',
        'D-M': '1010011', 'M-D': '1000111', 'D&M': '1000000',
        'D|M': '1010101'
    }

    jump_table = {
        None:  '000',
        'JGT': '001', 'JEQ': '010', 'JGE': '011',
        'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111'
    }

    def dest(self, mnemonic):
        return self.dest_table[mnemonic]

    def comp(self, mnemonic):
        return self.comp_table[mnemonic]

    def jump(self, mnemonic):
        return self.jump_table[mnemonic]

# =================== Parser ===================
class Parser:
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        self.commands = [line.split('//')[0].strip() for line in lines if line.strip() and not line.startswith('//')]
        self.current_index = -1
        self.current_command = None

    def has_more_commands(self):
        return self.current_index + 1 < len(self.commands)

    def advance(self):
        self.current_index += 1
        self.current_command = self.commands[self.current_index]

    def command_type(self):
        if self.current_command.startswith('@'):
            return 'A_COMMAND'
        elif self.current_command.startswith('('):
            return 'L_COMMAND'
        else:
            return 'C_COMMAND'

    def symbol(self):
        if self.command_type() == 'A_COMMAND':
            return self.current_command[1:]
        elif self.command_type() == 'L_COMMAND':
            return self.current_command[1:-1]

    def dest(self):
        return self.current_command.split('=')[0] if '=' in self.current_command else None

    def comp(self):
        parts = self.current_command.split('=')[-1].split(';')[0]
        return parts

    def jump(self):
        return self.current_command.split(';')[1] if ';' in self.current_command else None

# =================== Main ===================
def assemble(input_file):
    parser = Parser(input_file)
    code = Code()
    symbol_table = SymbolTable()

    # First Pass: build symbol table with labels
    rom_address = 0
    while parser.has_more_commands():
        parser.advance()
        ctype = parser.command_type()
        if ctype == 'L_COMMAND':
            symbol = parser.symbol()
            symbol_table.add_entry(symbol, rom_address)
        else:
            rom_address += 1

    # Second Pass: generate binary
    parser = Parser(input_file)
    ram_address = 16
    output_file = input_file.replace('.asm', '.hack')
    with open(output_file, 'w') as outf:
        while parser.has_more_commands():
            parser.advance()
            ctype = parser.command_type()
            if ctype == 'A_COMMAND':
                symbol = parser.symbol()
                address = 0
                if symbol.isdigit():
                    address = int(symbol)
                else:
                    if not symbol_table.contains(symbol):
                        symbol_table.add_entry(symbol, ram_address)
                        ram_address += 1
                    address = symbol_table.get_address(symbol)
                outf.write(f'{address:016b}\n')
            elif ctype == 'C_COMMAND':
                dest = code.dest(parser.dest())
                comp = code.comp(parser.comp())
                jump = code.jump(parser.jump())
                outf.write(f'111{comp}{dest}{jump}\n')
    print(f'Assembly complete. Output written to {output_file}')

# =================== Entry Point ===================
if __name__ == '__main__':
    if len(sys.argv) != 2 or not sys.argv[1].endswith('.asm'):
        print("Usage: python assembler.py Prog.asm")
    else:
        assemble(sys.argv[1])
