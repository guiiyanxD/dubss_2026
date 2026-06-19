import pytest

from apps.reportes import llm_tools


def test_ejecutar_tool_desconocida():
    resultado = llm_tools.ejecutar_tool("algo_inexistente", {})
    assert "error" in resultado


def test_definiciones_tools_formato():
    tools = llm_tools.definiciones_tools()
    assert tools
    assert all(t["type"] == "function" for t in tools)
    nombres = [t["function"]["name"] for t in tools]
    assert "listar_convocatorias" in nombres
    assert len(nombres) == len(set(nombres))


@pytest.mark.django_db
def test_ejecutar_tool_listar_convocatorias(convocatoria):
    resultado = llm_tools.ejecutar_tool("listar_convocatorias", {})
    assert any(c["id"] == convocatoria.pk for c in resultado["convocatorias"])


@pytest.mark.django_db
def test_ejecutar_tool_con_convocatoria_id(convocatoria):
    resultado = llm_tools.ejecutar_tool(
        "embudo_postulaciones", {"convocatoria_id": convocatoria.pk}
    )
    assert "etiquetas" in resultado
    assert "valores" in resultado


@pytest.mark.django_db
def test_ejecutar_tool_sin_argumentos():
    resultado = llm_tools.ejecutar_tool("validacion_documental", {})
    assert "etiquetas" in resultado


@pytest.mark.django_db
def test_ejecutar_tool_argumentos_none_no_rompe():
    resultado = llm_tools.ejecutar_tool("listar_convocatorias", None)
    assert "convocatorias" in resultado
