from django.db.models import Q

def ast_to_django(ast, model_cls):
    filters = build_filters(ast["where"])
    
    qs = model_cls.objects.filter(filters)
    
    if "order_by" in ast:
        qs = qs.order_by(ast["order_by"])
    
    return qs


def build_filters(expr):
    """Recursively build Q objects from AST"""
    if isinstance(expr, list):
        # Handles [condition, "AND", condition, "OR", ...]
        q = None
        logic = None
        for item in expr:
            if isinstance(item, dict):  # condition
                condition_q = build_filters(item)
                if q is None:
                    q = condition_q
                else:
                    if logic == "AND":
                        q &= condition_q
                    elif logic == "OR":
                        q |= condition_q
            elif isinstance(item, str):  # logic operator
                logic = item
        return q
    
    elif isinstance(expr, dict):
        field = expr["field"]
        op = expr["op"]
        
        if op == "=":
            return Q(**{field: expr["value"]})
        elif op == "!=":
            return ~Q(**{field: expr["value"]})
        elif op == ">":
            return Q(**{f"{field}__gt": expr["value"]})
        elif op == "<":
            return Q(**{f"{field}__lt": expr["value"]})
        elif op == ">=":
            return Q(**{f"{field}__gte": expr["value"]})
        elif op == "<=":
            return Q(**{f"{field}__lte": expr["value"]})
        elif op == "~":
            return Q(**{f"{field}__icontains": expr["value"]})
        elif op == "!~":
            return ~Q(**{f"{field}__icontains": expr["value"]})
        elif op == "IN":
            return Q(**{f"{field}__in": expr["values"]})
        elif op == "NOT IN":
            return ~Q(**{f"{field}__in": expr["values"]})
        else:
            raise ValueError(f"Unsupported operator {op}")
