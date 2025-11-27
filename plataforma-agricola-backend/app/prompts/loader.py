import yaml
from pathlib import Path

# Ruta base dinámica
PROMPTS_DIR = Path(__file__).parent

def load_prompt(agent_name: str, file_name: str)->str:
    """Carga un prompt desde un archivo Markdown (.md) o Texto (.txt)
    dentro de la carpeta del agente especificado.

    Args:
        agent_name (str): _description_
        file_name (str): _description_

    Returns:
        str: _description_
    """
    file_path = PROMPTS_DIR / agent_name / file_name
    
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        # Si usas YAML para configuración + texto
        if file_name.endswith(".yaml"):
            data = yaml.safe_load(f)
            return data["template"]
        
        # Si usas texto plano/markdown
        return f.read()