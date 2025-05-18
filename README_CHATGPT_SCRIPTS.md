# Geração Automatizada de Vídeos com ChatGPT-4o

Este guia explica como usar a API do ChatGPT-4o para gerar automaticamente scripts de narração para os slides de uma apresentação LaTeX e criar um vídeo narrado.

## Visão Geral do Processo

O processo pode ser realizado de duas maneiras:

### Método 1: Processo Totalmente Automatizado (Recomendado)

Um único script que realiza todo o processo automaticamente:
1. Extrai o conteúdo dos slides
2. Gera scripts usando a API do OpenAI
3. Cria áudio a partir dos scripts
4. Monta o vídeo final

### Método 2: Processo em Etapas

Alternativamente, você pode executar o processo em etapas separadas:
1. **Extração do conteúdo dos slides**: Extrair o conteúdo de cada slide da apresentação LaTeX.
2. **Geração de scripts com a API do OpenAI**: Enviar o conteúdo para a API do OpenAI e obter scripts.
3. **Geração do vídeo com os scripts**: Usar os scripts gerados para criar o vídeo final.

## Pré-requisitos

- Python 3.6 ou superior
- Chave de API do OpenAI
- Arquivo de apresentação LaTeX (.tex)
- Dependências do projeto (listadas em `requirements.txt`)

## Configuração

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure sua chave de API do OpenAI no arquivo `config/config.yaml`:
   ```yaml
   openai:
     api_key: "api-key"
     model: "gpt-4o"
     temperature: 0.7
     max_tokens: 1000
   ```

## Método 1: Processo Totalmente Automatizado

Execute o script `automated_video_generation.py` para realizar todo o processo em uma única etapa:

```bash
python -m src.automated_video_generation assets/presentation.tex
```

Este comando irá:
- Analisar o arquivo LaTeX
- Gerar imagens dos slides
- Gerar scripts usando a API do OpenAI
- Criar arquivos de áudio a partir dos scripts
- Montar o vídeo final

Para salvar os scripts gerados em arquivos, adicione a opção `--save-scripts`:

```bash
python -m src.automated_video_generation assets/presentation.tex --save-scripts
```

## Método 2: Processo em Etapas

### 1. Gerar scripts com a API do OpenAI

Execute o script `openai_script_generator.py`:

```bash
python -m src.openai_script_generator assets/presentation.tex
```

Este comando irá:
- Analisar o arquivo LaTeX
- Extrair o conteúdo de cada slide
- Enviar o conteúdo para a API do OpenAI
- Salvar os scripts gerados em `output/chatgpt_responses/`

### 2. Gerar o vídeo com os scripts

Execute o script `use_chatgpt_scripts.py`:

```bash
```
python -m src.use_chatgpt_scripts assets/presentation.tex

Este comando irá:
- Analisar o arquivo LaTeX
- Gerar imagens dos slides
- Carregar os scripts gerados
- Criar arquivos de áudio a partir dos scripts
- Montar o vídeo final

## Método 3: Processo Manual (Interface Web do ChatGPT)

Se preferir usar a interface web do ChatGPT-4o em vez da API:

### 1. Extrair o conteúdo dos slides

```bash
python -m src.chatgpt_script_generator assets/presentation.tex
```

### 2. Enviar o conteúdo para o ChatGPT-4o

```bash
python -m src.send_to_chatgpt
```

### 3. Gerar o vídeo com os scripts

```bash
python -m src.use_chatgpt_scripts assets/presentation.tex
```

## Dicas para Obter Melhores Resultados

1. **Ajuste de parâmetros da API**: Você pode ajustar a temperatura e o número máximo de tokens no arquivo `config/config.yaml` para controlar a criatividade e o comprimento dos scripts gerados.

2. **Revisão dos scripts**: Mesmo com o processo automatizado, é recomendável revisar os scripts gerados antes de criar o vídeo final. Use a opção `--save-scripts` para salvar os scripts e revisá-los.

3. **Personalização do prompt**: Você pode personalizar as instruções enviadas ao ChatGPT-4o editando a função `format_slide_for_chatgpt` no arquivo `src/chatgpt_script_generator.py`.

4. **Ajustes de áudio**: Se necessário, você pode ajustar as configurações de áudio no arquivo `config/config.yaml`.

## Solução de Problemas

- **Erro na API do OpenAI**: Verifique se sua chave de API está correta e se você tem créditos suficientes.

- **Erro na extração de slides**: Verifique se o arquivo LaTeX está formatado corretamente e se as estruturas de frame estão bem definidas.

- **Problemas com fórmulas matemáticas**: Se as fórmulas não estiverem sendo formatadas corretamente, você pode ajustar os padrões de expressão regular no arquivo `src/chatgpt_script_generator.py`.

- **Erro na geração de áudio**: Verifique se as credenciais da API de síntese de voz estão configuradas corretamente no arquivo `config/config.yaml`.

O vídeo final será salvo em `output/final_video.mp4`.
