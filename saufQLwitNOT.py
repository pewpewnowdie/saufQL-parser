from lark import Lark, Transformer, Token

# ---------------- Grammar ----------------
jql_grammar = r"""
    start: expr (order_by)?

    expr: condition (LOGIC condition)*

    ?condition: (NOT_OP)? base_condition   -> condition_not

    ?base_condition: FIELD OP VALUE                 -> condition_single
                   | FIELD IN_OP "(" value_list ")" -> condition_in

    order_by: "ORDER" "BY" FIELD (DIRECTION)?

    value_list: VALUE ("," VALUE)*

    LOGIC: "AND" | "OR"
    FIELD: /[a-zA-Z_][a-zA-Z0-9_]*/
    OP: "=" | "!=" | ">" | "<" | ">=" | "<=" | "~" | "!~"
    IN_OP: "IN" | "NOT IN"
    VALUE: ESCAPED_STRING | /[A-Za-z0-9_.]+/
    DIRECTION: "ASC" | "DESC"
    NOT_OP: "NOT"

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""

parser = Lark(jql_grammar, parser="lalr")

# ---------------- Transformer ----------------
class ToAST(Transformer):
    def FIELD(self, tok: Token): return tok.value
    def OP(self, tok: Token): return tok.value
    def IN_OP(self, tok: Token): return tok.value
    def VALUE(self, tok: Token): return tok.value.strip('"')
    def DIRECTION(self, tok: Token): return tok.value
    def LOGIC(self, tok: Token): return tok.value
    def NOT_OP(self, tok: Token): return "NOT"

    def start(self, items):
        ast = {"where": items[:-1][0]} if len(items) > 1 else {"where": items[0]}
        if isinstance(items[-1], dict) and "order_by" in items[-1]:
            ast["order_by"] = items[-1]["order_by"]
        return ast

    def expr(self, items):
        return items

    def condition_single(self, items):
        return {"field": items[0], "op": items[1], "value": items[2]}

    def condition_in(self, items):
        field, op, values = items[0], items[1], items[2:][0]
        return {"field": field, "op": op, "values": values}

    def condition_not(self, items):
        if items[0] == "NOT":
            return {"not": items[1]}
        return items[0]

    def value_list(self, items):
        return items

    def order_by(self, items):
        field = items[0]
        direction = items[1] if len(items) > 1 else "ASC"
        return {"order_by": ("-" if direction == "DESC" else "") + field}


# ---------------- Parser Function ----------------
def parse_query(query):
    try:
        tree = parser.parse(query)
        ast = ToAST().transform(tree)
        return ast
    except Exception as e:
        print("Query Parsing failed:", e)
        return None


# ---------------- Example ----------------
if __name__ == "__main__":
    query1 = 'NOT status = "Open" AND assignee = "kshitij.tyagi" ORDER BY priority DESC'
    query2 = 'status NOT IN ("Open", "Closed", "InProgress") AND NOT assignee = "guest"'
    print(parse_query(query1))
    print(parse_query(query2))
