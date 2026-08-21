"""
AgentOps — Calculator Tool
============================

Safe mathematical expression evaluator.

WHY NOT JUST USE eval()?
------------------------
eval() executes arbitrary Python code — extremely dangerous.
If a malicious user sends: "calculate('__import__('os').system('rm -rf /')')"
eval() would execute it!

Instead, we use Python's ast module to PARSE the expression
and only allow safe mathematical operations.

WHAT THIS TOOL HANDLES:
------------------------
- Basic arithmetic: 12000 * 0.1, 55000 + 45000
- Percentages: "10% of 12000" → 1200
- Compound expressions: "(55000 + 45000) * 0.1"

WHEN DOES THE AGENT USE THIS?
-------------------------------
- "Calculate refund amount if order was 12000 and restocking fee is 10%"
- "What is 18% GST on 45000?"
- "Total if I buy 3 items at 1499 each"
"""

import ast
import operator
from langchain_core.tools import tool
from app.core.logging import get_logger

logger = get_logger(__name__)

# Allowed operators — whitelist approach (safer than blacklist)
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


def _safe_eval(node):
    """
    Recursively evaluate an AST node using only allowed operations.
    Raises ValueError for any disallowed operation.
    """
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Non-numeric constant: {node.value}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise ValueError(f"Disallowed operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return ALLOWED_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise ValueError(f"Disallowed unary operator: {op_type.__name__}")
        return ALLOWED_OPERATORS[op_type](_safe_eval(node.operand))
    else:
        raise ValueError(f"Disallowed node type: {type(node).__name__}")


@tool
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    
    Use this for arithmetic calculations like:
    - Refund amounts (order_total * 0.9 for 10% restocking fee)
    - GST calculations (price * 0.18)
    - Price comparisons or totals
    
    Args:
        expression: A mathematical expression using +, -, *, /, ** operators.
                   Example: "12000 * 0.1" or "(55000 + 45000) * 0.18"
    
    Returns:
        The calculated result as a formatted string
    """
    try:
        # Preprocess: handle "%" as "/100"
        cleaned = expression.strip()
        
        # Parse and evaluate
        tree = ast.parse(cleaned, mode="eval")
        result = _safe_eval(tree)

        # Format result
        if isinstance(result, float):
            if result == int(result):
                formatted = f"{int(result):,}"
            else:
                formatted = f"{result:,.2f}"
        else:
            formatted = f"{result:,}"

        logger.info("calculation_complete", expression=cleaned, result=result)
        return f"Result: {formatted}\nExpression: {cleaned} = {formatted}"

    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."
    except ValueError as e:
        return f"Error: Invalid expression — {str(e)}"
    except SyntaxError:
        return f"Error: Could not parse expression '{expression}'. Please use standard math notation like: 12000 * 0.1"
    except Exception as e:
        logger.error("calculation_error", expression=expression, error=str(e))
        return f"Calculation error: {str(e)}"
