import _ast
import ast


def safe_f_string_evaluation(pattern, context):
    """Safely interpolates the variables in an f-string pattern using the provided context."""
    parsed = ast.parse(f"f'''{pattern}'''", mode="eval")

    # Walk through the AST to ensure it only contains safe expressions
    for node in ast.walk(parsed):
        if isinstance(node, _ast.FormattedValue):
            if not isinstance(node.value, _ast.Name):
                raise ValueError("Unsupported expression in f-string pattern.")
            if node.value.id not in context:
                raise ValueError(f"Variable {node.value.id} not allowed in f-string pattern.")

    compiled = compile(parsed, "<string>", "eval")
    return eval(compiled, {}, context)
