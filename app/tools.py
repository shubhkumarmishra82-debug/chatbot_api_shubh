"""
A basic calculator tool. Deliberately does NOT use Python's eval() --
parses the expression into an AST and only allows arithmetic operators,
so it can't execute arbitrary code even on adversarial input.
"""
import ast
import operator
import re

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_PATTERN = re.compile(r"^[\d\s\.\+\-\*/%\(\)]+$")


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Non-numeric constant")
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def try_calculate(message: str):
    """
    Returns a formatted "expr = result" string if the message is a pure
    arithmetic expression, else None (so the caller can fall through to
    other reply paths).
    """
    text = message.strip()
    if not text or not _SAFE_PATTERN.match(text):
        return None
    if not re.search(r"\d", text):
        return None

    try:
        tree = ast.parse(text, mode="eval")
        result = _eval_node(tree.body)
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError):
        return None

    if isinstance(result, float) and result.is_integer():
        result = int(result)

    return f"{text} = {result}"
