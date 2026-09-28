# Analisador de Finais Espaciais

Aplicação web construída com Streamlit para estudar posições de finais de xadrez. O
projeto combina o tabuleiro interativo do `python-chess`, avaliações de tablebases
Syzygy por meio da API pública do Lichess e uma linha de análise do Stockfish.

## Funcionalidades

- Exibição de uma posição de xadrez em SVG.
- Inserção e alteração de posições usando FEN.
- Navegação pelos lances com os botões de voltar e avançar.
- Seleção de um lance diretamente na tabela de lances legais.
- Movimentação de peças no tabuleiro por arrastar e soltar, com escolha da peça
  em caso de promoção e validação dos lances legais.
- Editor de posição com paleta de peças, remoção e movimentação, vez de jogar,
  direitos de roque e en passant, iniciando pela posição analisada; botões
  para limpar, restaurá-la ou gerar a posição inicial do jogo.
- Desenho de setas amarelas com o botão direito do mouse, independentemente dos
  lances legais.
- Avaliação de finais pela tablebase Syzygy, incluindo:
  - resultado da posição;
  - DTZ (Distance to Zeroing Move);
  - DTM (Distance to Mate), quando disponível;
  - classificação dos lances legais.
- Linha principal de análise do Stockfish.
- Controle da quantidade de lances da linha PV exibidos no tabuleiro e em texto
  (até o limite disponível na análise).
- Indicadores visuais no tabuleiro:
  - azul: lance legal ainda não avaliado pela tablebase;
  - verde: lance que mantém ou produz uma posição vencedora;
  - vermelho: lance que leva a uma posição perdida;
  - cinza: lance que leva a empate;
  - roxo: linha principal do Stockfish.
- Ferramentas didáticas opcionais:
  - regra do quadrado;
  - oposição dos reis;
  - casas bloqueadas;
  - casas-chave.
- Estatísticas predefinidas para alguns tipos de finais.

## Requisitos

- Python 3.10 ou superior.
- Acesso à internet para consultar a API de tablebases do Lichess.
- Stockfish compatível com a plataforma.

Os arquivos `stockfish-ubuntu-x86-64-avx2` e
`stockfish-windows-x86-64-avx2.exe` incluídos no projeto podem ser usados como
executáveis locais e são detectados automaticamente. Também é possível definir
a variável de ambiente `STOCKFISH_PATH` com o caminho de outro executável ou
instalar o comando `stockfish` no `PATH`.

## Instalação

Clone o repositório e entre na pasta do projeto:

```bash
git clone <URL_DO_REPOSITORIO>
cd chess-endgame-explainer
```

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### Configurando o Stockfish no Linux

Se for usar o binário incluído no projeto:

```bash
chmod +x stockfish-ubuntu-x86-64-avx2
```

Alternativamente, instale o Stockfish pelo gerenciador de pacotes da sua
distribuição e confirme que o comando abaixo funciona:

```bash
stockfish
```

## Executando a aplicação

Com o ambiente virtual ativado, execute:

```bash
streamlit run app.py
```

O Streamlit exibirá no terminal o endereço local da aplicação, normalmente:

```text
http://localhost:8501
```

## Como usar

1. Abra a aplicação no navegador.
2. Use os controles à esquerda para ativar ou desativar setas, linha PV e
   recursos didáticos. Ajuste o controle **Lances da linha PV** para escolher
   quantos lances da análise serão exibidos.
3. Edite o campo **Modificar posição (FEN)** para analisar outra posição.
   Para montar uma posição visualmente, clique em **Editar posição do tabuleiro**,
   selecione ou arraste peças da paleta, escolha a vez de jogar e clique em
   **Usar esta posição**. Você também pode ajustar roque e en passant.
   O editor começa com a posição atual da análise. No painel à esquerda,
   **Limpar tabuleiro** esvazia o rascunho e
   **Gerar posição inicial do jogo** dispõe todas as peças como no
   começo de uma partida e **Restaurar posição da análise** recupera a proposta
   original. A análise só muda ao aplicar uma posição válida.
4. Clique em uma linha da tabela **Lances Disponíveis** para executar o lance.
   Você também pode arrastar uma peça no tabuleiro até a casa de destino;
   promoções permitem escolher a peça. Para marcar uma ideia, arraste com o
   botão direito entre duas casas para desenhar uma seta amarela. Repita o
   mesmo gesto para removê-la; clique com o botão direito em uma casa para
   limpar todas as setas amarelas. Elas são removidas ao mudar de posição.
5. Use **Voltar Lance** e **Avançar Lance** para navegar pelo histórico.
6. Use **Trocar a Vez (Brancas / Pretas)** quando precisar alternar o lado a
   jogar sem modificar as peças.

## Fontes de dados e limitações

- As avaliações Syzygy são obtidas de
  `http://tablebase.lichess.ovh/standard`, por meio de uma requisição HTTP.
- A cobertura da tablebase depende das posições suportadas pelo serviço,
  normalmente finais com até sete peças.
- A linha PV depende do executável Stockfish local. Se ele não estiver
  disponível, a aplicação informa o problema na barra lateral e as demais
  funcionalidades continuam disponíveis.
- As estatísticas exibidas para alguns tipos de finais são referências fixas
  definidas no código; elas não são calculadas em tempo real.

## Estrutura principal

```text
.
├── app.py                              # Aplicação Streamlit
├── requirements.txt                    # Dependências Python
├── stockfish-ubuntu-x86-64-avx2       # Binário Stockfish para Linux
└── stockfish-windows-x86-64-avx2.exe  # Binário Stockfish para Windows
```

## Desenvolvimento

Para verificar a sintaxe do arquivo principal:

```bash
python3 -m py_compile app.py
```
