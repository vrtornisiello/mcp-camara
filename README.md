# mcp-camara

Um servidor [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) para consultar os dados da [Câmara dos Deputados do Brasil](https://www.camara.leg.br/).

## Instalação

Para instalar e executar este servidor, você precisará do [uv](https://docs.astral.sh/uv/). Para instalá-lo, siga as instruções de instalação da [documentação oficial](https://docs.astral.sh/uv/getting-started/installation/).

Com o uv instalado, clone este repositório e instale o servidor em um ambiente virtual:
```bash
git clone https://github.com/vrtornisiello/mcp-camara.git
uv sync
```

Você pode executar o servidor usando o comando:
```bash
uv run mcp-camara
```

## Ferramentas

Este servidor disponibiliza as seguintes ferramentas:

- `list_endpoints`: Lista todos os endpoints disponíveis na API dos dados abertos da Câmara dos Deputados.
- `get_endpoint_schema`: Retorna o esquema detalhado de um endpoint, incluindo seus parâmetros.
- `call_endpoint`: Executa uma chamada a um endpoint específico.
- `get_deputy_by_name`: Busca por um deputado pelo nome.
- `get_deputy_expenses`: Retorna as despesas de um deputado.
- `get_bills_by_deputy`: Retorna as proposições de um deputado.

## Integração

Você pode instalar esse servidor em qualquer cliente MCP, como o [Claude](https://claude.ai/download) e o [Gemini CLI](https://github.com/google-gemini/gemini-cli).

Para isso, basta instalá-los e adicionar o servidor aos seus respectivos arquivos de configuração:

```json
{
  "mcpServers": {
    "mcp-camara" : {
      "command": "uv",
      "args": [
        "--directory",
        "<caminho para o respositório mcp-camara>",
        "run",
        "mcp-camara"
      ]
    }
  }
}
```

## Referências
- [Portal da Câmara dos Deputados](https://www.camara.leg.br/)
- [Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br/)
- [API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html)
