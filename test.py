# OOP Programming Language with LLVM Compiler
# Features include classes, inheritance, and direct compilation to executables

import sys
import re
import os
import subprocess
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Callable
import llvmlite.binding as llvm
import llvmlite.ir as ir

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# ====== LEXER ======
class TokenType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    LPAREN = auto()
    RPAREN = auto()
    IDENTIFIER = auto()
    ASSIGN = auto()
    SEMICOLON = auto()
    PRINT = auto()
    IF = auto()
    ELSE = auto()
    LBRACE = auto()
    RBRACE = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    GREATER = auto()
    WHILE = auto()
    EOF = auto()
    STRING = auto()
    # OOP related tokens
    CLASS = auto()
    NEW = auto()
    DOT = auto()
    EXTENDS = auto()
    THIS = auto()
    SUPER = auto()
    FUNCTION = auto()
    RETURN = auto()
    COMMA = auto()

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

class Lexer:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source_code[0] if self.source_code else None
        
    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
            
        self.position += 1
        self.current_char = self.source_code[self.position] if self.position < len(self.source_code) else None
        
    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()
            
    def skip_comment(self):
        while self.current_char and self.current_char != '\n':
            self.advance()
            
    def number(self):
        line, column = self.line, self.column
        result = ""
        is_float = False
        
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if is_float:  # Second decimal point is not allowed
                    break
                is_float = True
            result += self.current_char
            self.advance()
            
        if is_float:
            return Token(TokenType.FLOAT, float(result), line, column)
        else:
            return Token(TokenType.INTEGER, int(result), line, column)
            
    def identifier(self):
        line, column = self.line, self.column
        result = ""
        
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
            
        # Keywords
        keywords = {
            'print': TokenType.PRINT,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'class': TokenType.CLASS,
            'new': TokenType.NEW,
            'extends': TokenType.EXTENDS,
            'this': TokenType.THIS,
            'super': TokenType.SUPER,
            'function': TokenType.FUNCTION,
            'return': TokenType.RETURN
        }
        
        token_type = keywords.get(result, TokenType.IDENTIFIER)
        return Token(token_type, result, line, column)
        
    def string(self):
        line, column = self.line, self.column
        self.advance()  # Skip opening quotation mark
        result = ""
        
        while self.current_char and self.current_char != '"':
            if self.current_char == '\\' and self.position + 1 < len(self.source_code):
                self.advance()  # Skip the backslash
                escape_chars = {
                    'n': '\n',
                    't': '\t',
                    'r': '\r',
                    '\\': '\\',
                    '"': '"'
                }
                result += escape_chars.get(self.current_char, self.current_char)
            else:
                result += self.current_char
            self.advance()
            
        if self.current_char is None:
            raise SyntaxError(f"Unterminated string at line {line}, column {column}")
            
        self.advance()  # Skip closing quotation mark
        return Token(TokenType.STRING, result, line, column)
    
    def get_next_token(self):
        while self.current_char:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
                
            # Skip comments
            if self.current_char == '#':
                self.skip_comment()
                continue
                
            # Numbers
            if self.current_char.isdigit():
                return self.number()
                
            # Identifiers
            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()
                
            # Strings
            if self.current_char == '"':
                return self.string()
                
            # Operators and punctuation
            line, column = self.line, self.column
            
            if self.current_char == '+':
                self.advance()
                return Token(TokenType.PLUS, '+', line, column)
                
            if self.current_char == '-':
                self.advance()
                return Token(TokenType.MINUS, '-', line, column)
                
            if self.current_char == '*':
                self.advance()
                return Token(TokenType.MULTIPLY, '*', line, column)
                
            if self.current_char == '/':
                self.advance()
                return Token(TokenType.DIVIDE, '/', line, column)
                
            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN, '(', line, column)
                
            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN, ')', line, column)
                
            if self.current_char == '{':
                self.advance()
                return Token(TokenType.LBRACE, '{', line, column)
                
            if self.current_char == '}':
                self.advance()
                return Token(TokenType.RBRACE, '}', line, column)
                
            if self.current_char == ';':
                self.advance()
                return Token(TokenType.SEMICOLON, ';', line, column)
                
            if self.current_char == ',':
                self.advance()
                return Token(TokenType.COMMA, ',', line, column)
                
            if self.current_char == '.':
                self.advance()
                return Token(TokenType.DOT, '.', line, column)
                
            if self.current_char == '=':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.EQUAL, '==', line, column)
                return Token(TokenType.ASSIGN, '=', line, column)
                
            if self.current_char == '!':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.NOT_EQUAL, '!=', line, column)
                raise SyntaxError(f"Unexpected character '!' at line {line}, column {column}")
                
            if self.current_char == '<':
                self.advance()
                return Token(TokenType.LESS, '<', line, column)
                
            if self.current_char == '>':
                self.advance()
                return Token(TokenType.GREATER, '>', line, column)
                
            # Unknown character
            raise SyntaxError(f"Unexpected character '{self.current_char}' at line {line}, column {column}")
                
        return Token(TokenType.EOF, None, self.line, self.column)
    
    def tokenize(self):
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens

# ====== PARSER ======
class ASTNode:
    pass

class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
        
    def __repr__(self):
        return f"BinOp({self.left}, {self.op}, {self.right})"

class UnaryOp(ASTNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr
        
    def __repr__(self):
        return f"UnaryOp({self.op}, {self.expr})"

class Number(ASTNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value
        
    def __repr__(self):
        return f"Number({self.value})"

class String(ASTNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value
        
    def __repr__(self):
        return f"String('{self.value}')"

class Variable(ASTNode):
    def __init__(self, token):
        self.token = token
        self.name = token.value
        
    def __repr__(self):
        return f"Variable({self.name})"

class Assign(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
        
    def __repr__(self):
        return f"Assign({self.left}, {self.op}, {self.right})"

class Print(ASTNode):
    def __init__(self, expr):
        self.expr = expr
        
    def __repr__(self):
        return f"Print({self.expr})"

class Compound(ASTNode):
    def __init__(self, statements):
        self.statements = statements
        
    def __repr__(self):
        return f"Compound({self.statements})"

class If(ASTNode):
    def __init__(self, condition, if_body, else_body=None):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        
    def __repr__(self):
        return f"If({self.condition}, {self.if_body}, {self.else_body})"

class While(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        
    def __repr__(self):
        return f"While({self.condition}, {self.body})"

# OOP AST nodes
class Class(ASTNode):
    def __init__(self, name, parent_name, body):
        self.name = name
        self.parent_name = parent_name
        self.body = body
        
    def __repr__(self):
        return f"Class({self.name}, extends={self.parent_name}, {self.body})"

class Method(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body
        
    def __repr__(self):
        return f"Method({self.name}, {self.params}, {self.body})"

class MethodCall(ASTNode):
    def __init__(self, object_expr, method_name, args):
        self.object_expr = object_expr
        self.method_name = method_name
        self.args = args
        
    def __repr__(self):
        return f"MethodCall({self.object_expr}, {self.method_name}, {self.args})"

class New(ASTNode):
    def __init__(self, class_name, args):
        self.class_name = class_name
        self.args = args
        
    def __repr__(self):
        return f"New({self.class_name}, {self.args})"

class This(ASTNode):
    def __init__(self):
        pass
        
    def __repr__(self):
        return "This"

class Super(ASTNode):
    def __init__(self):
        pass
        
    def __repr__(self):
        return "Super"

class Return(ASTNode):
    def __init__(self, expr):
        self.expr = expr
        
    def __repr__(self):
        return f"Return({self.expr})"

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0]
        
    def advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
            
    def peek(self):
        peek_pos = self.position + 1
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return None
            
    def eat(self, token_type):
        if self.current_token.type == token_type:
            current = self.current_token
            self.advance()
            return current
        else:
            line, column = self.current_token.line, self.current_token.column
            raise SyntaxError(f"Expected {token_type}, got {self.current_token.type} at line {line}, column {column}")
            
    def program(self):
        statements = []
        
        while self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.CLASS:
                statements.append(self.class_declaration())
            else:
                statements.append(self.statement())
            
        return Compound(statements)
        
    def class_declaration(self):
        self.eat(TokenType.CLASS)
        class_name = self.eat(TokenType.IDENTIFIER).value
        
        parent_name = None
        if self.current_token.type == TokenType.EXTENDS:
            self.eat(TokenType.EXTENDS)
            parent_name = self.eat(TokenType.IDENTIFIER).value
            
        self.eat(TokenType.LBRACE)
        
        body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.FUNCTION:
                body.append(self.method_declaration())
            else:
                body.append(self.statement())
                
        self.eat(TokenType.RBRACE)
        
        return Class(class_name, parent_name, Compound(body))
        
    def method_declaration(self):
        self.eat(TokenType.FUNCTION)
        method_name = self.eat(TokenType.IDENTIFIER).value
        
        self.eat(TokenType.LPAREN)
        params = []
        
        # Parse parameters
        if self.current_token.type != TokenType.RPAREN:
            params.append(self.eat(TokenType.IDENTIFIER).value)
            
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                params.append(self.eat(TokenType.IDENTIFIER).value)
                
        self.eat(TokenType.RPAREN)
        
        # Parse method body
        body = self.statement()
        
        return Method(method_name, params, body)
        
    def statement(self):
        if self.current_token.type == TokenType.PRINT:
            return self.print_statement()
        elif self.current_token.type == TokenType.IF:
            return self.if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.while_statement()
        elif self.current_token.type == TokenType.LBRACE:
            return self.compound_statement()
        elif self.current_token.type == TokenType.RETURN:
            return self.return_statement()
        elif self.current_token.type == TokenType.IDENTIFIER:
            # Check if it's an assignment or a method call
            if self.peek() and self.peek().type in (TokenType.ASSIGN, TokenType.DOT):
                return self.assignment_or_method_call()
            else:
                expr = self.expr()
                self.eat(TokenType.SEMICOLON)
                return expr
        else:
            expr = self.expr()
            self.eat(TokenType.SEMICOLON)
            return expr
            
    def return_statement(self):
        self.eat(TokenType.RETURN)
        expr = self.expr()
        self.eat(TokenType.SEMICOLON)
        return Return(expr)
            
    def print_statement(self):
        self.eat(TokenType.PRINT)
        self.eat(TokenType.LPAREN)
        expr = self.expr()
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.SEMICOLON)
        return Print(expr)
        
    def assignment_or_method_call(self):
        var_token = self.eat(TokenType.IDENTIFIER)
        
        if self.current_token.type == TokenType.DOT:
            # Method call
            object_expr = Variable(var_token)
            return self.method_call_statement(object_expr)
        else:
            # Assignment
            var = Variable(var_token)
            token = self.eat(TokenType.ASSIGN)
            expr = self.expr()
            self.eat(TokenType.SEMICOLON)
            return Assign(var, token, expr)
    
    def method_call_statement(self, object_expr):
        method_call = self.method_call(object_expr)
        self.eat(TokenType.SEMICOLON)
        return method_call
        
    def method_call(self, object_expr):
        self.eat(TokenType.DOT)
        method_name = self.eat(TokenType.IDENTIFIER).value
        
        self.eat(TokenType.LPAREN)
        args = []
        
        if self.current_token.type != TokenType.RPAREN:
            args.append(self.expr())
            
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                args.append(self.expr())
                
        self.eat(TokenType.RPAREN)
        
        return MethodCall(object_expr, method_name, args)
        
    def if_statement(self):
        self.eat(TokenType.IF)
        self.eat(TokenType.LPAREN)
        condition = self.expr()
        self.eat(TokenType.RPAREN)
        
        if_body = self.statement()
        
        else_body = None
        if self.current_token.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            else_body = self.statement()
            
        return If(condition, if_body, else_body)
        
    def while_statement(self):
        self.eat(TokenType.WHILE)
        self.eat(TokenType.LPAREN)
        condition = self.expr()
        self.eat(TokenType.RPAREN)
        body = self.statement()
        return While(condition, body)
        
    def compound_statement(self):
        self.eat(TokenType.LBRACE)
        statements = []
        
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.statement())
            
        self.eat(TokenType.RBRACE)
        return Compound(statements)
        
    def expr(self):
        return self.assignment_expr()
        
    def assignment_expr(self):
        node = self.comparison()
        
        # Handle chained method calls: obj.method1().method2()
        while self.current_token.type == TokenType.DOT:
            node = self.method_call(node)
            
        return node
        
    def comparison(self):
        node = self.arithmetic()
        
        while self.current_token.type in (TokenType.EQUAL, TokenType.NOT_EQUAL, TokenType.LESS, TokenType.GREATER):
            token = self.current_token
            self.advance()
            node = BinOp(node, token, self.arithmetic())
            
        return node
        
    def arithmetic(self):
        node = self.term()
        
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            self.advance()
            node = BinOp(node, token, self.term())
            
        return node
        
    def term(self):
        node = self.factor()
        
        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            token = self.current_token
            self.advance()
            node = BinOp(node, token, self.factor())
            
        return node
        
    def factor(self):
        token = self.current_token
        
        if token.type == TokenType.PLUS:
            self.advance()
            return UnaryOp(token, self.factor())
        elif token.type == TokenType.MINUS:
            self.advance()
            return UnaryOp(token, self.factor())
        elif token.type == TokenType.INTEGER:
            self.advance()
            return Number(token)
        elif token.type == TokenType.FLOAT:
            self.advance()
            return Number(token)
        elif token.type == TokenType.STRING:
            self.advance()
            return String(token)
        elif token.type == TokenType.LPAREN:
            self.advance()
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return Variable(token)
        elif token.type == TokenType.THIS:
            self.advance()
            return This()
        elif token.type == TokenType.SUPER:
            self.advance()
            return Super()
        elif token.type == TokenType.NEW:
            self.advance()
            class_name = self.eat(TokenType.IDENTIFIER).value
            
            self.eat(TokenType.LPAREN)
            args = []
            
            if self.current_token.type != TokenType.RPAREN:
                args.append(self.expr())
                
                while self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    args.append(self.expr())
                    
            self.eat(TokenType.RPAREN)
            
            return New(class_name, args)
        else:
            line, column = token.line, token.column
            raise SyntaxError(f"Unexpected token {token.type} at line {line}, column {column}")
            
    def parse(self):
        return self.program()

# ====== INTERPRETER ======
class Interpreter:
    def __init__(self):
        self.global_env = {}
        self.classes = {}
        
    def visit(self, node, env=None):
        if env is None:
            env = self.global_env
            
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, env)
        
    def generic_visit(self, node, env):
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined")
        
    def visit_BinOp(self, node, env):
        left = self.visit(node.left, env)
        right = self.visit(node.right, env)
        
        if node.op.type == TokenType.PLUS:
            return left + right
        elif node.op.type == TokenType.MINUS:
            return left - right
        elif node.op.type == TokenType.MULTIPLY:
            return left * right
        elif node.op.type == TokenType.DIVIDE:
            return left / right
        elif node.op.type == TokenType.EQUAL:
            return left == right
        elif node.op.type == TokenType.NOT_EQUAL:
            return left != right
        elif node.op.type == TokenType.LESS:
            return left < right
        elif node.op.type == TokenType.GREATER:
            return left > right
            
    def visit_UnaryOp(self, node, env):
        if node.op.type == TokenType.PLUS:
            return +self.visit(node.expr, env)
        elif node.op.type == TokenType.MINUS:
            return -self.visit(node.expr, env)
            
    def visit_Number(self, node, env):
        return node.value
        
    def visit_String(self, node, env):
        return node.value
        
    def visit_Variable(self, node, env):
        var_name = node.name
        if var_name not in env:
            if var_name not in self.global_env:
                raise NameError(f"Variable '{var_name}' is not defined")
            return self.global_env[var_name]
        return env[var_name]
        
    def visit_Assign(self, node, env):
        var_name = node.left.name
        value = self.visit(node.right, env)
        env[var_name] = value
        return value
        
    def visit_Print(self, node, env):
        value = self.visit(node.expr, env)
        print(value)
        return value
        
    def visit_Compound(self, node, env):
        result = None
        for statement in node.statements:
            result = self.visit(statement, env)
        return result
        
    def visit_If(self, node, env):
        condition = self.visit(node.condition, env)
        if condition:
            return self.visit(node.if_body, env)
        elif node.else_body:
            return self.visit(node.else_body, env)
            
    def visit_While(self, node, env):
        result = None
        while self.visit(node.condition, env):
            result = self.visit(node.body, env)
        return result
        
    def visit_Class(self, node, env):
        class_name = node.name
        parent_name = node.parent_name
        
        # Create class definition
        class_def = {
            'name': class_name,
            'parent': parent_name,
            'methods': {},
            'fields': {}
        }
        
        # Process class body
        class_env = {}
        if parent_name and parent_name in self.classes:
            for field, value in self.classes[parent_name]['fields'].items():
                class_env[field] = value
                
        for statement in node.body.statements:
            if isinstance(statement, Method):
                class_def['methods'][statement.name] = statement
            elif isinstance(statement, Assign):
                field_name = statement.left.name
                field_value = self.visit(statement.right, class_env)
                class_def['fields'][field_name] = field_value
                
        # Register class
        self.classes[class_name] = class_def
        return class_def
        
    def visit_Method(self, node, env):
        return node
        
    def visit_MethodCall(self, node, env):
        # Evaluate the object
        obj = self.visit(node.object_expr, env)
        
        if not isinstance(obj, dict) or 'class' not in obj:
            raise TypeError(f"Cannot call method '{node.method_name}' on non-object value")
            
        # Find method in object's class
        class_name = obj['class']
        class_def = self.classes[class_name]
        
        if node.method_name not in class_def['methods']:
            if class_def['parent'] and class_def['parent'] in self.classes:
                parent_class = self.classes[class_def['parent']]
                if node.method_name in parent_class['methods']:
                    method = parent_class['methods'][node.method_name]
                else:
                    raise AttributeError(f"Method '{node.method_name}' not found in class '{class_name}' or its parents")
            else:
                raise AttributeError(f"Method '{node.method_name}' not found in class '{class_name}'")
        else:
            method = class_def['methods'][node.method_name]
            
        # Create method environment with 'this' binding
        method_env = {'this': obj}
        
        # Evaluate and bind arguments
        if len(method.params) != len(node.args):
            raise TypeError(f"Method '{node.method_name}' expects {len(method.params)} arguments but got {len(node.args)}")
            
        for param, arg in zip(method.params, node.args):
            method_env[param] = self.visit(arg, env)
            
        # Execute method body
        return self.visit(method.body, method_env)
        
    def visit_New(self, node, env):
        class_name = node.class_name
        
        if class_name not in self.classes:
            raise NameError(f"Class '{class_name}' not defined")
            
        class_def = self.classes[class_name]
        
        # Create new object
        obj = {
            'class': class_name,
            'fields': {}
        }
        
        # Copy fields from class definition
        for field, value in class_def['fields'].items():
            obj['fields'][field] = value
            
        # Call constructor if exists
        if 'init' in class_def['methods']:
            constructor = class_def['methods']['init']
            
            # Create method environment with 'this' binding
            method_env = {'this': obj}
            
            # Evaluate and bind arguments
            if len(constructor.params) != len(node.args):
                raise TypeError(f"Constructor expects {len(constructor.params)} arguments but got {len(node.args)}")
                
            for param, arg in zip(constructor.params, node.args):
                method_env[param] = self.visit(arg, env)
                
            # Execute constructor body
            self.visit(constructor.body, method_env)
            
        return obj
        
    def visit_This(self, node, env):
        if 'this' not in env:
            raise SyntaxError("'this' can only be used within a method")
        return env['this']
        
    def visit_Super(self, node, env):
        if 'this' not in env:
            raise SyntaxError("'super' can only be used within a method")
            
        obj = env['this']
        class_name = obj['class']
        class_def = self.classes[class_name]
        
        if not class_def['parent']:
            raise TypeError(f"Class '{class_name}' has no parent class")
            
        # Create a proxy object that behaves like 'this' but with parent class
        # Continue from the Super method implementation
        super_obj = dict(obj)
        super_obj['class'] = class_def['parent'] # This line was incomplete in the original
        
        return super_obj
        
    def visit_Return(self, node, env):
        if node.expr:
            return self.visit(node.expr, env)
        return None
        
    def interpret(self, tree):
        return self.visit(tree, self.global_env)

# ====== LLVM COMPILER ======
class Compiler:
    def __init__(self):
        self.global_env = {}
        self.classes = {}
        self.current_module = None
        self.current_function = None
        self.current_builder = None
        self.printf_func = None
        self.exit_blocks = []
        self.continue_blocks = []
        self.return_values = []
        self.function_return_type = None
        
    def initialize_module(self, name):
        # Initialize module and add runtime functions
        self.current_module = ir.Module(name=name)
        
        # Declare external C functions
        printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf_func = ir.Function(self.current_module, printf_ty, name="printf")
        
        # Define integer to string conversion function
        int_to_string_ty = ir.FunctionType(
            ir.PointerType(ir.IntType(8)), [ir.IntType(32)]
        )
        self.int_to_string_func = ir.Function(
            self.current_module, int_to_string_ty, name="int_to_string"
        )
        
        # Define main function
        main_ty = ir.FunctionType(ir.IntType(32), [])
        self.main_func = ir.Function(self.current_module, main_ty, name="main")
        
        # Create entry block for main function
        entry_block = self.main_func.append_basic_block(name="entry")
        self.current_builder = ir.IRBuilder(entry_block)
        
        # Initialize runtime
        self.initialize_runtime()
        
    def initialize_runtime(self):
        # Add global string constants
        self.int_format_str = self.add_global_string("%d\n", "int_format")
        self.float_format_str = self.add_global_string("%f\n", "float_format")
        self.string_format_str = self.add_global_string("%s\n", "string_format")
        
    def add_global_string(self, string, name):
        # Add null terminator
        string_with_null = string + "\0"
        # Create global constant for string
        str_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(string_with_null)),
                              bytearray(string_with_null.encode("utf8")))
        global_str = ir.GlobalVariable(self.current_module, str_const.type, name=name)
        global_str.global_constant = True
        global_str.initializer = str_const
        return global_str
        
    def get_string_pointer(self, global_str):
        zero = ir.Constant(ir.IntType(32), 0)
        return self.current_builder.gep(global_str, [zero, zero], inbounds=True)
        
    def compile(self, tree, output_file):
        # Initialize module
        self.initialize_module(output_file)
        
        # Compile AST
        self.visit(tree)
        
        # Add return 0 at the end of main
        self.current_builder.ret(ir.Constant(ir.IntType(32), 0))
        
        # Verify module
        llvm.parse_assembly(str(self.current_module))
        
        # Optimize module
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = 2
        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        pm.run(self.current_module)
        
        # Generate object file
        target_machine = self.get_target_machine()
        with open(f"{output_file}.o", "wb") as f:
            f.write(target_machine.emit_object(self.current_module))
            
        # Link object file to create executable
        self.link_executable(output_file)
        
    def get_target_machine(self):
        # Get host CPU details
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        return target_machine
        
    def link_executable(self, output_file):
        # Use system compiler (gcc/clang) to link the object file
        if os.name == 'nt':  # Windows
            compiler = 'gcc'
        else:  # Linux/Mac
            compiler = 'cc'
            
        subprocess.run([compiler, f"{output_file}.o", "-o", output_file])
        
    def visit(self, node):
        method_name = f'compile_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
        
    def generic_visit(self, node):
        raise NotImplementedError(f"No compile_{type(node).__name__} method defined")
        
    def compile_Compound(self, node):
        result = None
        for statement in node.statements:
            result = self.visit(statement)
        return result
        
    def compile_Number(self, node):
        if isinstance(node.value, int):
            return ir.Constant(ir.IntType(32), node.value)
        else:  # float
            return ir.Constant(ir.FloatType(), node.value)
            
    def compile_String(self, node):
        # Create global string constant
        string_name = f"str_{abs(hash(node.value)) % 10000}"
        global_str = self.add_global_string(node.value, string_name)
        return self.get_string_pointer(global_str)
        
    def compile_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        # Handle type conversion
        if left.type != right.type:
            if isinstance(left.type, ir.IntType) and isinstance(right.type, ir.FloatType):
                left = self.current_builder.sitofp(left, ir.FloatType())
            elif isinstance(left.type, ir.FloatType) and isinstance(right.type, ir.IntType):
                right = self.current_builder.sitofp(right, ir.FloatType())
                
        # Arithmetic operations
        if node.op.type == TokenType.PLUS:
            if isinstance(left.type, ir.IntType):
                return self.current_builder.add(left, right)
            else:
                return self.current_builder.fadd(left, right)
        elif node.op.type == TokenType.MINUS:
            if isinstance(left.type, ir.IntType):
                return self.current_builder.sub(left, right)
            else:
                return self.current_builder.fsub(left, right)
        elif node.op.type == TokenType.MULTIPLY:
            if isinstance(left.type, ir.IntType):
                return self.current_builder.mul(left, right)
            else:
                return self.current_builder.fmul(left, right)
        elif node.op.type == TokenType.DIVIDE:
            if isinstance(left.type, ir.IntType):
                return self.current_builder.sdiv(left, right)
            else:
                return self.current_builder.fdiv(left, right)
                
        # Comparison operations
        elif node.op.type in (TokenType.EQUAL, TokenType.NOT_EQUAL, TokenType.LESS, TokenType.GREATER):
            if isinstance(left.type, ir.IntType):
                if node.op.type == TokenType.EQUAL:
                    cmp_result = self.current_builder.icmp_signed('==', left, right)
                elif node.op.type == TokenType.NOT_EQUAL:
                    cmp_result = self.current_builder.icmp_signed('!=', left, right)
                elif node.op.type == TokenType.LESS:
                    cmp_result = self.current_builder.icmp_signed('<', left, right)
                elif node.op.type == TokenType.GREATER:
                    cmp_result = self.current_builder.icmp_signed('>', left, right)
            else:  # Float comparison
                if node.op.type == TokenType.EQUAL:
                    cmp_result = self.current_builder.fcmp_ordered('==', left, right)
                elif node.op.type == TokenType.NOT_EQUAL:
                    cmp_result = self.current_builder.fcmp_ordered('!=', left, right)
                elif node.op.type == TokenType.LESS:
                    cmp_result = self.current_builder.fcmp_ordered('<', left, right)
                elif node.op.type == TokenType.GREATER:
                    cmp_result = self.current_builder.fcmp_ordered('>', left, right)
                    
            # Convert bool to int
            return self.current_builder.zext(cmp_result, ir.IntType(32))
            
    def compile_UnaryOp(self, node):
        expr = self.visit(node.expr)
        
        if node.op.type == TokenType.PLUS:
            return expr  # Unary plus doesn't change anything
        elif node.op.type == TokenType.MINUS:
            if isinstance(expr.type, ir.IntType):
                return self.current_builder.neg(expr)
            else:
                return self.current_builder.fneg(expr)
                
    def compile_Variable(self, node):
        var_name = node.name
        if var_name not in self.global_env:
            raise NameError(f"Variable '{var_name}' is not defined")
            
        return self.current_builder.load(self.global_env[var_name])
        
    def compile_Assign(self, node):
        var_name = node.left.name
        value = self.visit(node.right)
        
        if var_name not in self.global_env:
            # Create a new variable allocation
            if isinstance(value.type, ir.IntType):
                alloca = self.create_entry_block_alloca(var_name, ir.IntType(32))
            elif isinstance(value.type, ir.FloatType):
                alloca = self.create_entry_block_alloca(var_name, ir.FloatType())
            elif isinstance(value.type, ir.PointerType):
                # Assuming string or object
                alloca = self.create_entry_block_alloca(var_name, value.type)
            else:
                raise TypeError(f"Unsupported type: {value.type}")
                
            self.global_env[var_name] = alloca
            
        # Store the value
        self.current_builder.store(value, self.global_env[var_name])
        return value
        
    def create_entry_block_alloca(self, name, type):
        # Create an allocation at the entry point of the function
        builder = ir.IRBuilder()
        builder.position_at_start(self.main_func.entry_basic_block)
        return builder.alloca(type, name=name)
        
    def compile_Print(self, node):
        value = self.visit(node.expr)
        
        if isinstance(value.type, ir.IntType):
            format_str = self.get_string_pointer(self.int_format_str)
            self.current_builder.call(self.printf_func, [format_str, value])
        elif isinstance(value.type, ir.FloatType):
            format_str = self.get_string_pointer(self.float_format_str)
            self.current_builder.call(self.printf_func, [format_str, value])
        elif isinstance(value.type, ir.PointerType):
            # Assuming it's a string
            format_str = self.get_string_pointer(self.string_format_str)
            self.current_builder.call(self.printf_func, [format_str, value])
        else:
            raise TypeError(f"Cannot print value of type {value.type}")
            
        return value
        
    def compile_If(self, node):
        # Evaluate condition
        condition = self.visit(node.condition)
        
        # Convert condition to a boolean value (i1)
        condition_bool = self.current_builder.icmp_signed('!=', condition, 
                                                     ir.Constant(condition.type, 0))
        
        # Create blocks for the if/else branches and the merge point
        then_block = self.current_function.append_basic_block(name="then")
        merge_block = self.current_function.append_basic_block(name="ifcont")
        
        if node.else_body:
            else_block = self.current_function.append_basic_block(name="else")
            self.current_builder.cbranch(condition_bool, then_block, else_block)
        else:
            self.current_builder.cbranch(condition_bool, then_block, merge_block)
            
        # Emit then block
        self.current_builder.position_at_start(then_block)
        then_value = self.visit(node.if_body)
        self.current_builder.branch(merge_block)
        
        # Retrieve the updated builder position after generating the 'then' block
        then_block = self.current_builder.block
        
        # Emit else block
        else_value = None
        if node.else_body:
            self.current_builder.position_at_start(else_block)
            else_value = self.visit(node.else_body)
            self.current_builder.branch(merge_block)
            
            # Retrieve the updated builder position after generating the 'else' block
            else_block = self.current_builder.block
            
        # Emit merge block
        self.current_builder.position_at_start(merge_block)
        
        # Create PHI node for merging the results if both branches return a value
        if then_value is not None and else_value is not None:
            if then_value.type == else_value.type:
                phi = self.current_builder.phi(then_value.type, name="iftmp")
                phi.add_incoming(then_value, then_block)
                phi.add_incoming(else_value, else_block)
                return phi
                
        return None
        
    def compile_While(self, node):
        # Create blocks for the loop condition, body, and after-loop
        cond_block = self.current_function.append_basic_block(name="while.cond")
        body_block = self.current_function.append_basic_block(name="while.body")
        after_block = self.current_function.append_basic_block(name="while.end")
        
        # Store blocks for break/continue statements
        self.continue_blocks.append(cond_block)
        self.exit_blocks.append(after_block)
        
        # Jump to the condition block
        self.current_builder.branch(cond_block)
        
        # Emit condition block
        self.current_builder.position_at_start(cond_block)
        condition = self.visit(node.condition)
        condition_bool = self.current_builder.icmp_signed('!=', condition, 
                                                     ir.Constant(condition.type, 0))
        self.current_builder.cbranch(condition_bool, body_block, after_block)
        
        # Emit loop body
        self.current_builder.position_at_start(body_block)
        self.visit(node.body)
        self.current_builder.branch(cond_block)
        
        # Position builder at the after block
        self.current_builder.position_at_start(after_block)
        
        # Remove blocks from break/continue stacks
        self.continue_blocks.pop()
        self.exit_blocks.pop()
        
        return None
        
    def compile_Class(self, node):
        class_name = node.name
        parent_name = node.parent_name
        
        # Create vtable and class structure
        class_def = {
            'name': class_name,
            'parent': parent_name,
            'methods': {},
            'fields': {}
        }
        
        # Process class body
        for statement in node.body.statements:
            if isinstance(statement, Method):
                class_def['methods'][statement.name] = statement
            
        # Register class
        self.classes[class_name] = class_def
        return None
        
    def compile_Method(self, node):
        method_name = node.name
        params = node.params
        
        # Create function type
        param_types = [ir.IntType(32) for _ in params]  # Assuming all params are int for simplicity
        func_type = ir.FunctionType(ir.IntType(32), param_types)
        
        # Create function
        func = ir.Function(self.current_module, func_type, name=method_name)
        
        # Name the arguments
        for i, arg in enumerate(func.args):
            arg.name = params[i]
            
        # Create entry block
        entry_block = func.append_basic_block(name="entry")
        
        # Save current function and builder
        prev_function = self.current_function
        prev_builder = self.current_builder
        
        # Set current function and builder
        self.current_function = func
        self.current_builder = ir.IRBuilder(entry_block)
        
        # Create allocas for all arguments
        for i, arg in enumerate(func.args):
            alloca = self.create_entry_block_alloca(arg.name, arg.type)
            self.current_builder.store(arg, alloca)
            self.global_env[arg.name] = alloca
            
        # Compile function body
        self.visit(node.body)
        
        # Add a default return if needed
        if not self.current_builder.block.is_terminated:
            self.current_builder.ret(ir.Constant(ir.IntType(32), 0))
            
        # Restore previous function and builder
        self.current_function = prev_function
        self.current_builder = prev_builder
        
        return func
        
    def compile_New(self, node):
        class_name = node.class_name
        
        if class_name not in self.classes:
            raise NameError(f"Class '{class_name}' not defined")
            
        # For simplicity, we're just creating a dummy value to represent the object
        # In a real implementation, we would allocate memory for the object and initialize its fields
        
        # Create a dummy integer to represent the object instance
        return ir.Constant(ir.IntType(32), 1)
        
    def compile_MethodCall(self, node):
        # For simplicity, this is a very basic implementation
        # In a real implementation, we would look up the method in the vtable and call it
        
        # Get method name
        method_name = node.method_name
        
        # Find function in module
        if method_name in self.current_module.globals:
            func = self.current_module.globals[method_name]
            
            # Prepare arguments
            args = [self.visit(arg) for arg in node.args]
            
            # Call function
            return self.current_builder.call(func, args)
        else:
            raise NameError(f"Method '{method_name}' not found")
            
    def compile_Return(self, node):
        if node.expr:
            value = self.visit(node.expr)
            self.current_builder.ret(value)
        else:
            self.current_builder.ret(ir.Constant(ir.IntType(32), 0))
            
        return None

# ====== MAIN COMPILER ENTRY POINT ======
def compile_to_executable(source_code, output_file="output"):
    # Tokenize
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Optional: Interpret for testing
    #interpreter = Interpreter()
    #interpreter.interpret(ast)
    
    # Compile
    compiler = Compiler()
    compiler.compile(ast, output_file)
    
    print(f"Successfully compiled to executable: {output_file}")
    return output_file

# Command-line interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <source_file> [output_file]")
        sys.exit(1)
        
    source_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(source_file)[0]
    
    with open(source_file, 'r') as f:
        source_code = f.read()
        
    try:
        compiled_file = compile_to_executable(source_code, output_file)
        print(f"Compilation successful. Executable created: {compiled_file}")
    except Exception as e:
        print(f"Compilation error: {e}")
        sys.exit(1)
