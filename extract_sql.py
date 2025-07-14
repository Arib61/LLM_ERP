import re

def extract_last_sql_query(output: str) -> str:
    # Prend la dernière requête SELECT/WITH
    selects = re.findall(r'((?:SELECT|WITH)[\s\S]+?;)', output, re.IGNORECASE)
    if selects:
        return selects[-1].strip()
    # Bloc markdown SQL ?
    code_blocks = re.findall(r"```(?:sql)?(.*?)```", output, re.DOTALL | re.IGNORECASE)
    if code_blocks:
        return code_blocks[-1].strip()
    # Fallback
    return output.strip()
