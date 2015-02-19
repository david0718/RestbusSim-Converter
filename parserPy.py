# parser file
#
# Author: Leos Mikulka (mikulkal@hotmail.com)
# Date: 

__author__ = "Leos Mikulka"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "mikulkal@hotmail.com"

from lexer import Lexer
import ply.lex as lex
import ply.yacc as yacc
import ast
import io
import string

class Node:
    def __init__(self,type,children=None,leaf=None):
         self.type = type
         if children:
              self.children = children
         else:
              self.children = [ ]
         self.leaf = leaf

    def __repr__(self):
        return "{type: %s, children: %s, leaf: %s}" % (self.type,self.children,self.leaf)

    #def __str__(self):
    #    return "(type: %s, children: %s, leaf: %s)" % (self.type,self.children,self.leaf)


class Parser:
    
    string = ""
    inside = 0
    tokens = Lexer().tokens                     # define tokens

    precedence = (
        ('left','PLUS','MINUS'),
        ('left','TIMES','DIVIDE','MOD'),
        ('left','EQ_TEST','NOT_EQ_TEST'),
        ('left','GT','GTE','LT','LTE'),
        ('left','BIT_AND','BIT_OR','BIT_XOR'),
        ('left','LSHIFT','RSHIFT'),
    )

    def p_program(self,p):                          # lines of code
        ''' program : code_fragment
                    | program code_fragment '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1],tuple):
                p[0] = p[1],p[2]
            else:
                p[0] = p[1]+(p[2],)             # append to the tuple

    def p_code_fragment_1(self,p):
        ''' code_fragment : user_function compound_statement '''
        p[0] = Node('Function_UD',p[2],p[1])

    def p_code_fragment_2(self,p):              
        ''' code_fragment : capl_event_declaration compound_statement CAPLEND'''
        p[0] = Node('CAPL_event',p[2],p[1])

    def p_code_fragment_3(self,p):
        ''' code_fragment : globalVars_declaration compound_statement CAPLEND'''
        p[0] = Node('GlobalVars_decl',p[2],p[1])

    def p_code_fragment_4(self,p):
        ''' code_fragment : comment '''
        p[0] = p[1]

    def p_user_function(self,p):
        ''' user_function : entry LPAR RPAR
                          | declaration_type entry LPAR RPAR '''
        if len(p) == 3:
            p[0] = p[1]
        else:
            p[0] = p[1],p[2]

    def p_capl_event_declaration(self,p):           # e.g. on envVar initialize
        ''' capl_event_declaration : CAPLBEGIN on_event entry'''
        #p[0] = Node('CAPL_event',(p[1],p[2]))
        p[0] = p[2],p[3]

    def p_globalVars_declaration(self,p):
        ''' globalVars_declaration : CAPLBEGIN variables_keyword '''
        p[0] = p[2]

    def p_statement(self,p):
        ''' statement : capl_function
                      | compound_statement '''
        p[0] = p[1]

    def p_declaration(self,p):                      # terminated declaration with ;
        ''' declaration : declaration_body SMC '''
        p[0] = p[1]

    def p_declaration_body(self,p):
        ''' declaration_body : declaration_type declarations_list '''
        #p[0] = Node('Declaration',(p[1],p[2]))
        p[0] = Node('Declaration',p[2],p[1])

    def p_declaration_type(self,p):                # data types - TODO! Change specific for declarations/functions
        ''' declaration_type : BYTE
                             | INT
                             | WORD
                             | DWORD
                             | LONG
                             | FLOAT
                             | DOUBLE
                             | MESSAGE
                             | TIMER
                             | MSTIMER
                             | CHAR
                             | VOID '''
        p[0] = Node('Type',None,p[1])

    def p_declarations_list(self,p):                # sequence of declarations; e.g. abc, cde
        ''' declarations_list : declaration_single
                              | declarations_list comma declaration_single '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1],p[3]

    def p_declaration_single_var(self,p):
        ''' declaration_single : entry
                               | entry equals expression
                               | entry assign_operator expression '''
        if len(p) == 2:
            p[0] = p[1]
        elif p[2] == '=':
            p[0] = Node('Assign',p[1],p[3])
        else:
            p[0] = Node('Assign_OP',p[1],(p[3],p[2]))

    def p_declaration_single_array(self,p):
        ''' declaration_single : entry array_brackets
                               | entry array_brackets equals unary_expression
                               | entry array_brackets equals initializer_array'''
        if len(p) == 3:
            p[0] = Node('Array',None,(p[1],p[2]))
        else:
            p[0] = Node('Assign_Array',(p[1],p[2]),p[4])

    def p_assignment(self,p):
        ''' assignment : declaration_single SMC '''
        p[0] = p[1]

    def p_expression(self,p):
        ''' expression : binary_expression '''
        p[0] = p[1]

    def p_binary_expression(self,p):
        ''' binary_expression : unary_expression
                              | binary_expression PLUS binary_expression
                              | binary_expression MINUS binary_expression
                              | binary_expression TIMES binary_expression
                              | binary_expression DIVIDE binary_expression
                              | binary_expression MOD binary_expression
                              | binary_expression EQ_TEST binary_expression
                              | binary_expression NOT_EQ_TEST binary_expression
                              | binary_expression GT binary_expression
                              | binary_expression GTE binary_expression
                              | binary_expression LT binary_expression
                              | binary_expression LTE binary_expression
                              | binary_expression BIT_AND binary_expression
                              | binary_expression BIT_OR binary_expression
                              | binary_expression BIT_XOR binary_expression
                              | binary_expression LSHIFT binary_expression
                              | binary_expression RSHIFT binary_expression '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node('Expression',(p[1],p[3]),p[2])

    def p_initializer_array(self,p):
        ''' initializer_array : char_string
                              | const_compound
                              | LCBR const_compound_list RCBR
                              | LCBR string_list RCBR '''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 4:
            p[0] = p[2]

    def p_block_item(self,p):                   # item inside compound statement
        ''' block_item : declaration
                       | assignment 
                       | statement
                       | comment '''
        p[0] = p[1]

    def p_inside_block_list(self,p):
        ''' inside_block_list : block_item
                              | inside_block_list block_item '''
        if len(p) == 2:  # or p[2] == [None]:
            p[0] = p[1]
        else:
            if not isinstance(p[1],tuple):
                p[0] = p[1],p[2]
            else:
                p[0] = p[1]+(p[2],)             # append to the tuple

    def p_const_compound_list(self,p):
        ''' const_compound_list : const_compound
                                | const_compound_list comma const_compound'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1][0],tuple):
                p[0] = p[1],p[3]
            else:
                p[0] = p[1]+(p[3],)

    def p_const_compound(self,p):
        ''' const_compound : LCBR const_list RCBR '''
        p[0] = p[2]

    def p_const_list(self,p):
        ''' const_list : const
                       | const_list comma const '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1],tuple):
                p[0] = p[1],p[3]
            else:
                p[0] = p[1]+(p[3],)

    def p_string_list(self,p):
        ''' string_list : char_string
                        | string_list comma char_string '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1],tuple):
                p[0] = p[1],p[3]
            else:
                p[0] = p[1]+(p[3],)

    def p_compound_statement(self,p):               # i.e. { .... }
        ''' compound_statement : LCBR RCBR
                               | LCBR inside_block_list RCBR '''
        if len(p) == 3:
            pass
        else:
            p[0] = p[2]

    def p_capl_function(self,p):                    # e.g. ILSetSignal( Ctrl_C_Stat1_AR::ReturnKey_Psd_UB, 1);
        ''' capl_function : capl_function_body SMC '''
        p[0] = p[1]

    def p_unary_expression(self,p):
        ''' unary_expression : value_expression
                             | single_expression '''
        p[0] = p[1]

    def p_single_expression_pre(self,p):
        ''' single_expression : INCREMENT value_expression
                              | DECREMENT value_expression
                              | COMPLEMENT value_expression '''
        p[0] = Node("Expression",p[2],p[1])

    def p_single_expression_post(self,p):
        ''' single_expression : value_expression INCREMENT
                              | value_expression DECREMENT '''
        p[0] = Node("Expression",p[1],p[2])

    def p_value_expression(self,p):
        ''' value_expression : entry
                             | const '''
        p[0] = p[1]

    # TODO!! NOT COMPLETE + create reserved words for functions!
    def p_capl_function_body(self,p):               
        ''' capl_function_body : declaration_single LPAR RPAR
                               | declaration_single LPAR capl_function_action RPAR '''
        if len(p) == 3:
            p[0] = Node('CAPL_fcn',None,p[1])
        else:
            p[0] = Node('CAPL_fcn',p[3],p[1])

    # TODO!! define more than message_signal
    def p_capl_function_action(self,p):             # e.g. Ctrl_C_Stat1_AR::ReturnKey_Psd_UB, 1
        ''' capl_function_action : message_signal comma const'''
        p[0] = Node("action",p[1],p[3])

    def p_message_signal(self,p):                   # e.g. Ctrl_C_Stat1_AR::ReturnKey_Psd_UB
        ''' message_signal : declaration_single dcol declaration_single '''
        p[0] = Node("msg_sig",None,(p[1],p[3]))

    def p_entry_ID(self,p):                  
        ''' entry : ID '''                    # single identifier
        p[0] = Node('ID', None ,p[1])
        #p[0] = ast.Str(p[1])

    def p_on_event(self,p):                         # "on" is used at the beginning of CAPL events
        ''' on_event : CAPLEVENT '''
        p[0] = p[1]

    def p_variables_keyword(self,p):                # word 'variables'; used for declaring global vars.
        ''' variables_keyword : VARS '''
        p[0] = p[1]

    def p_comment(self,p):
        ''' comment : COMMENT
                    | CppCOMMENT '''
        p[0] = Node("COMMENT",None,p[1]) 

    def p_char_string(self,p):
        ''' char_string : STRING '''
        p[0] = Node("STRING",None,p[1])

    def p_const_int(self,p):                     # numerical constant
        ''' const : DEC_NUM '''
        p[0] = Node("INT",None,p[1])

    def p_const_hex(self,p):
        ''' const : HEX_NUM '''
        p[0] = Node("HEX",None,p[1])

    def p_const_float(self,p):
        ''' const : FLOAT_NUM '''
        p[0] = Node("FLOAT",None,p[1])

    def p_const_char(self,p):
        ''' const : CHARC '''
        p[0] = Node("CHAR",None,p[1])

    def p_array_brackets(self,p):
        ''' array_brackets : ARRAY '''
        p[0] = p[1]

    def p_dcol(self,p):                         # double-colon (i.e. ::)
        ''' dcol : DCOL '''
        p[0] = p[1]

    def p_comma(self,p):                         # comma
        '''comma : COM
                 | empty'''
        p[0] = p[1]

    def p_equals(self,p):
        ''' equals : EQ '''
        p[0] = p[1]

    def p_assign_operator(self,p):
        ''' assign_operator : ADD_EQ
                            | SUB_EQ
                            | MULT_EQ
                            | DIV_EQ
                            | MOD_EQ
                            | LSHIFT_EQ
                            | RSHIFT_EQ
                            | OR_EQ
                            | XOR_EQ'''
        p[0] = p[1]

    def p_empty(self,p):
        '''empty :'''
        pass

    def p_error(self,p):
        if p:
            print('Syntax error %s' % p.value,p.lineno)
        else:
            print('Syntax error at the end of input')

    def generate_declaration(self,declaration_param,isInside):
        #string_param = "Dim "
        if isInside == 1:
            string_param = "\t"
        else:
            string_param = ""

        variable_type = declaration_param.leaf.leaf
        variable_type_first = (variable_type[0]).upper()    # make first letter uppercase
        variable_type_rest = variable_type[1:len(variable_type)]

        if not isinstance(declaration_param.children,tuple):
            variable = declaration_param.children
            if variable.type == 'Array':
                variable_name = variable.leaf[0].leaf
                string_param = "Dim %s(" % variable_name
                array_dims = []
                array_split = variable.leaf[1].split('[')
                array_split = array_split[1:]
                for array_split_i in array_split:
                     array_split_i = array_split_i.split(']')
                     array_dims.append(array_split_i[0])
                if len(array_dims) == 1:
                    dim = int(array_dims[0])-1
                    string_param += "%d)" % dim
                else:
                    for i in range(0,len(array_dims)):
                        dim = int(array_dims[i])-1
                        if not i == (len(array_dims)-1):  
                            string_param += "%d," % dim
                        else:
                            string_param += "%d)" % dim
                string_param += " As %s%s\n" % (variable_type_first,variable_type_rest)    

            elif variable.type == 'Assign_Array':
                variable_name = variable.children[0].leaf
                string_param = "Dim %s(" % variable_name
                array_dims = []
                array_split = variable.children[1].split('[')
                array_split = array_split[1:]
                for array_split_i in array_split:
                     array_split_i = array_split_i.split(']')
                     array_dims.append(array_split_i[0])
                if len(array_dims) == 1:
                    dim = int(array_dims[0])-1
                    string_param += "%d)" % dim
                else:
                    for i in range(0,len(array_dims)):
                        dim = int(array_dims[i])-1
                        if not i == (len(array_dims)-1):
                            string_param += "%d," % dim
                        else:
                            string_param += "%d)" % dim
                string_param += " As %s%s\n" % (variable_type_first,variable_type_rest)

                values_array = []
                val_entry = []
                if len(array_dims) == 2:
                    for val in variable.leaf:
                        for val_dim in val:
                            val_entry.append(val_dim.leaf)
                        values_array.append(val_entry)
                        val_entry = []

                    for i in range(0,int(array_dims[0])):
                        for j in range(0,int(array_dims[1])):
                            string_param += "%s(%d,%d) = %s\n" % (variable_name,i,j,int(values_array[i][j]))
                elif len(array_dims) == 1:
                    for val_dim in variable.leaf:
                        values_array.append(val_dim.leaf)
                    for i in range(0,int(array_dims[0])):
                        string_param += "%s(%d) = %s\n" % (variable_name,i,int(values_array[i]))
                        
            elif variable.type == 'Assign':
                string_param = "Dim %s" % variable.children.leaf
                string_param += " As %s%s\n" % (variable_type_first,variable_type_rest) 
                string_param += self.generate_assignment(variable,isInside)        
            else:
                variable_name = variable.leaf
                string_param += "Dim %s" % variable_name
                string_param += " As %s%s\n" % (variable_type_first,variable_type_rest) 
        else:
            for variable in declaration_param.children:
                if variable.type == 'Array':
                    print(variable)
                    variable_name = variable.leaf[0].leaf
                    string_param = "Dim %s(" % variable_name
                    array_dims = []
                    array_split = variable.leaf[1].split('[')
                    array_split = array_split[1:]
                    for array_split_i in array_split:
                         array_split_i = array_split_i.split(']')
                         array_dims.append(array_split_i[0])
                    if len(array_dims) == 1:
                        string_param += "%s)" % str(array_dims[0])
                    else:
                        for i in range(0,len(array_dims)):
                            if not i == (len(array_dims)-1):
                                string_param += "%s," % str(array_dims[i])
                            else:
                                string_param += "%s)" % str(array_dims[i])
                    string_param += " As %s%s\n" % (variable_type_first,variable_type_rest)   

                if variable.type == 'Assign':
                    string_param = "Dim %s" % variable.children.leaf
                    string_param += " As %s%s\n" % (variable_type_first,variable_type_rest) 
                    string_param += self.generate_assignment(variable,isInside)  
                else:
                    variable_name = variable.leaf
                    string_param += "Dim %s" % variable_name
                    string_param += " As %s%s\n" % (variable_type_first,variable_type_rest)   
            
        return string_param

    def generate_assignment(self,var,isInside):
        string_param = ""
        variable_name = var.children.leaf

        if var.type == 'Assign':
            assign_value = var.leaf.leaf
            if isInside == 1:
                string_param += "\t"
            if var.leaf.children == []:
                string_param += "%s = %s\n" % (variable_name,assign_value)
            else:                                   # expression
                if isinstance(var.leaf.children,tuple):      # binary expression
                    var_1 = var.leaf.children[0].leaf
                    var_2 = var.leaf.children[1].leaf
                    binary_opp = var.leaf.leaf
                    string_param += "%s = %s %s %s\n" % (variable_name,var_1,binary_opp,var_2)
                else:                               # single expression
                    assign_var = var.children.leaf
                    operator = var.leaf.leaf
                    if operator == '++':
                        string_param += "%s = %s + 1\n" % (variable_name,assign_var)
                    if operator == '--':
                        string_param += "%s = %s - 1\n" % (variable_name,assign_var)
                    if operator == '~':
                        string_param += "# %s - NOT SUPPORTED BY WWB" % (operator)

        if var.type == 'Assign_OP':
            operator = (var.leaf[1].split('='))[0]
            assign_value = var.leaf[0].leaf
            if isInside == 1:
                string_param += "\t"
            string_param += "%s = %s %s %s\n" % (variable_name,variable_name,operator,assign_value)

        return string_param

    def generate_function(self,function_param,isInside):
        if isInside == 1:
            string_param = "\t"
        else:
            string_param = ""

        if function_param.type == 'Function_UD':

            function_UD_declar = function_param.leaf
            function_UD_type = function_UD_declar[0].leaf
            function_UD_type_first = (function_UD_type[0]).upper()    # make first letter uppercase
            function_UD_type_rest = function_UD_type[1:len(function_UD_type)]
            function_UD_name = function_UD_declar[1].leaf
            function_UD_name_first = (function_UD_name[0]).upper()    # make first letter uppercase
            function_UD_name_rest = function_UD_name[1:len(function_UD_name)]

            if (function_UD_type == 'void'):
                self.string += "Sub %s%s()\n" % (function_UD_name_first,function_UD_name_rest)
                statements = function_param.children 
                self.inside = 1
                if not isinstance(statements,tuple):
                    self.generate_code(statements)
                else:
                    for statement in statements:
                        self.generate_code(statement)
                self.string += "End Sub\n"
            else:
                self.string += "Function %s%s() as %s%s\n" % (function_UD_name_first,function_UD_name_rest,function_UD_type_first,function_UD_type_rest)
                statements = function_param.children  
                self.inside = 1
                if not isinstance(statements,tuple):
                    self.generate_code(statements)
                else:
                    for statement in statements:
                        self.generate_code(statement)
                self.string += "End Function\n"

        if function_param.type == 'CAPL_fcn':
               
            function_name = function_param.leaf.leaf          # leaf: {ID, _ , ILSetSignal}
            if function_name == 'ILSetSignal':
                string_param += "System.SetSignal"
                action = function_param.children
                signal_value = action.leaf.leaf

                # TODO! CHANGE TO ---> if isinstance(action.children,tuple): ---> prob. don't define alone mes_sig
                if(action.children.type == 'msg_sig'):
                    values = action.children.leaf
                    if isinstance(values,tuple):
                        message_name = values[0].leaf
                        signal_name = values[1].leaf
                string_param += "(\"TX.CTRL_C.%s.%s\", %s)\n" % (message_name,signal_name,signal_value)
        
        #return string_param

    def generate_code(self,tree):
        #if self.string == "":
        #    f = open('testScript.txt','w')
        #else:
        #    f = open('testScript.txt','a')
        
        print(tree)                        # print whole tree - type Node
        print("-------------")

        root = tree             # start with root
        if not isinstance(root,tuple):
            if root.type == 'GlobalVars_decl':      # translation of global variables declaration
                declarations = root.children
                self.inside = 0
                if not isinstance(declarations,tuple):
                    self.string += self.generate_declaration(declarations,self.inside)
                else:
                    for declaration in declarations:
                        self.string += self.generate_declaration(declaration,self.inside)
                self.string += "\n"

            if root.type == 'Assign' or root.type == 'Assign_OP':
                self.string += self.generate_assignment(root,self.inside)

            if root.type == 'Function_UD':             # translation of user-defined functions
                #self.string += self.generate_function(root,self.inside)
                self.generate_function(root,self.inside)

            if root.type == 'CAPL_fcn':             # translation of CAPL defined functions
                self.string += self.generate_function(root,self.inside)

            if root.type == 'Declaration':          # translation of declarations
                self.string += self.generate_declaration(root,self.inside)

            if root.type == 'CAPL_event':           # translation of CAPL events
                self.string += "Sub Main\n"

                statements = root.children
                event_name = root.leaf[0]
                print(event_name)
                if event_name == 'on envVar':     # Provetech doesn't really support on envVar ---> can be dissmissed
                    print("Found \'on envVar\' event")     
                    self.inside = 1 
                    if not isinstance(statements,tuple):
                        self.generate_code(statements)
                    else:
                        for statement in statements:
                            self.generate_code(statement)
                    self.string += "End Sub\n"
                    #if not isinstance(functions,tuple):     # single function
                    #    self.string += self.generate_function(functions)
                    #else:
                    #    for function in functions:             # multiple functions
                    #        self.string += self.generate_function(function)
                    #self.string += "End Sub\n"
                #else:
       
      #              for function in functions:
       #                 pass        # TODO!!!
                        
        else:
            for entry in root:
                self.generate_code(entry)

    def write_to_file(self):
        f = open('testScript.txt','w')
        f.write(self.string)
        print("WWB Script generated.")

    def __init__(self,caplFile):

        lexer_init = Lexer()                         # create instance of Lexer
        lexer_init.build()                           # build the lexer
        if isinstance(caplFile,str):                # program called from command line
            lexer_init.test(caplFile)                   # analyze an input file
            # Build the lexer and parser
            yacc.yacc(module = self)
            ast_tree = yacc.parse(open(caplFile).read())
        else:                                       # program called from GUI
            lexer_init.test(caplFile.get())              # analyze an input file
            # Build the lexer and parser
            yacc.yacc(module = self)
            ast_tree = yacc.parse(open(caplFile.get()).read())

        
        #if isinstance(ast_tree,tuple):
        #    for node in ast_tree:
        #        print(str(node)+"\n")  
        #else:
        #    if isinstance(ast_tree.children,tuple):
        #        for node in ast_tree.children:
        #            print(str(node))
        #    else:
        #        pass
                #print("WHOLE TREE:")
                #print(ast_tree)

        self.generate_code(ast_tree) 
        self.write_to_file()
        #ast_tree = ast.parse(open(caplFile.get()).read())
        #print(ast.dump(ast_tree))
        ##exec(compile(ast_tree, filename="<ast>", mode="exec"))
