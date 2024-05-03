import ply.lex as lex
import ply.yacc as yacc
from pymystem3 import Mystem

Lemmatizer = Mystem()


def lemmatize_sentence(text):
    lemmas = Lemmatizer.lemmatize(text)
    return "".join(lemmas).strip().upper()


# Лексер
tokens = ("NUMBER", "PLUS", "MINUS", "TIMES", "DIVIDE", "LPAREN", "RPAREN")

t_PLUS = r"ПЛЮС"
t_MINUS = r"МИНУС"
t_TIMES = r"УМНОЖИТЬ"
t_DIVIDE = r"РАЗДЕЛИТЬ"
t_LPAREN = r"СКОБКА\sОТКРЫВАТЬСЯ"
t_RPAREN = r"СКОБКА\sЗАКРЫВАТЬСЯ"


def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    return t


t_ignore = " \t"


def t_error(t):
    print(f"Неверный символ: '{t.value[0]}'")
    t.lexer.skip(1)


lexer = lex.lex()


# Парсер
def p_expression(p):
    """
    expression : expression PLUS term
               | expression MINUS term
    """
    if p[2] == "ПЛЮС":
        p[0] = p[1] + p[3]
    elif p[2] == "МИНУС":
        p[0] = p[1] - p[3]


def p_expression_term(p):
    """
    expression : term
    """
    p[0] = p[1]


def p_term(p):
    """
    term : term TIMES factor
         | term DIVIDE factor
    """
    if p[2] == "УМНОЖИТЬ":
        p[0] = p[1] * p[3]
    elif p[2] == "РАЗДЕЛИТЬ":
        p[0] = p[1] / p[3]


def p_term_factor(p):
    """
    term : factor
    """
    p[0] = p[1]


def p_factor_number(p):
    """
    factor : NUMBER
    """
    p[0] = p[1]


def p_factor_group(p):
    """
    factor : LPAREN expression RPAREN
    """
    p[0] = p[2]


def p_error(p):
    print("Синтаксическая ошибка")


parser = yacc.yacc()


def evaluate(p):
    return parser.parse(p)


if __name__ == "__main__":
    query = "3 плюс 4 минус скобка открывается 5 плюс 6 скобка закрывается"
    lemm_query = lemmatize_sentence(query)
    result = evaluate(lemm_query)
    print(result)
