# Powerful Studies

Add-on nativo para Anki Desktop que substitui visualmente o navegador de decks por um explorador de pastas em cartões. Ele melhora a navegação e a organização, mas não altera cartões, notas nativas, agendamento, filas ou regras de revisão do Anki.

> Idioma da interface: português do Brasil. Compatível com Anki Desktop 25.09.4 ou superior, Qt 6.

## Visão geral

O **Explorador Visual** apresenta somente os decks do nível atual em uma grade responsiva. Cada cartão mostra ícone/emoji, cor, descrição opcional, contadores novos/aprender/revisar, quantidade de subdecks e ações contextuais. O botão **Estudar** apenas seleciona o deck e abre a visão geral nativa do Anki; a revisão continua sendo inteiramente do Anki.

Ainda não há capturas de tela no repositório. A interface usa cartões compactos, cantos arredondados e os tokens claro/escuro definidos no projeto, sem recursos externos ou CDN.

Funcionalidades implementadas na Fase 1:

- navegador visual, breadcrumb, busca local e navegação por subdecks;
- contadores provenientes da árvore agregada do scheduler do Anki;
- personalização independente por deck (ícone, emoji, cor e descrição);
- menu com estudo, opções nativas, renomear, exportar e excluir;
- troca imediata para a lista nativa e tela de configurações;
- persistência atômica e isolada por perfil;
- contrato inicial de `DeckDocument` para a futura Fase 2.

Ficam deliberadamente para fases posteriores: editor/preview Markdown, integração com vault Obsidian, sincronização de documentos, dashboard, Pomodoro e barra lateral.

## Arquitetura

```text
Deck Browser do Anki
  └─ hooks públicos → ExplorerController → HTML/CSS/JS local no AnkiWebView
                                      ├─ operações nativas do Anki (deck/review)
                                      └─ workspace.json por perfil
                                             ├─ aparência por ID estável de deck
                                             └─ metadados de DeckDocument
```

| Pasta                | Responsabilidade                                             |
| -------------------- | ------------------------------------------------------------ |
| `integrations/`      | Hooks do Anki, ponte WebView e adaptação da árvore de decks. |
| `core/models/`       | Entidades independentes: aparência e `DeckDocument`.         |
| `core/services/`     | Regras de aparência e contrato dos documentos.               |
| `core/repositories/` | JSON versionado, validado e escrito atomicamente.            |
| `ui/`                | Diálogos Qt para aparência e configurações.                  |
| `web/`               | Interface local HTML/CSS/JavaScript sem dependências.        |
| `tests/`             | Testes `unittest` de lógica isolada.                         |
| `scripts/`           | Empacotamento `.ankiaddon`.                                  |

O HTML envia somente mensagens JSON prefixadas com `powerful-studies:`. A ponte valida ação e ID antes de executar qualquer operação. Textos renderizados são escapados no Python. A interface usa a árvore retornada por `col.sched.deck_due_tree()` que o Deck Browser já consulta, evitando consulta de scheduler por cartão.

### Estrutura visual do Explorer

O hook do Deck Browser fornece conteúdo dentro de uma tabela nativa. Por isso, o Explorer gera uma linha e célula de tabela válidas antes do seu elemento principal (`<tr><td><main id="ps-explorer">…`). O CSS torna somente essa tabela hospedeira fluida e isola todo o restante sob `#ps-explorer`. Isso evita que o navegador WebEngine reorganize HTML inválido e permite que `.ps-deck-grid` use toda a largura central com `repeat(auto-fill, minmax(min(100%, 220px), 1fr))`.

Cada cartão é um único `article` com cabeçalho (ícone e menu), conteúdo (nome e descrição) e rodapé (subdecks, estatísticas separadas e Estudar). Clique no conteúdo/ícone para navegar em decks-pasta; em deck sem subdecks, esse clique abre a visão geral nativa. O botão Estudar permanece uma ação independente.

## Persistência, perfil e sincronização

Os dados ficam em `<pasta-do-perfil>/powerful-studies/workspace.json`, nunca em `collection.anki2` e nunca na configuração do deck. O arquivo possui `schema_version`, é validado na leitura e salvo por arquivo temporário + substituição atômica. Renomear um deck preserva a aparência, pois a chave é o ID. Personalizações órfãs são removidas quando operações atualizam a coleção.

`DeckDocument` representa um documento Markdown de espaço de trabalho, e **não** uma `Note` nativa do Anki. Nesta versão só existem IDs, vínculo de ID de deck, título, tags e datas; os corpos Markdown não são salvos no Anki nem neste JSON.

AnkiWeb não sincroniza esse arquivo automaticamente. Uma exportação/importação de coleção também não o transporta. Para migrar de dispositivo, copie o diretório `powerful-studies` dentro da pasta do perfil depois de fechar o Anki. O desenho do repositório permite futuramente trocar o armazenamento por arquivos ou SQLite sem mudar a UI.

## Pré-requisitos

- Anki Desktop 25.09.4 ou mais recente, com Qt 6;
- Python embutido no Anki para uso normal — não é necessário `venv`, npm ou servidor;
- Python 3.10+ opcional para rodar os testes e gerar o pacote fora do Anki.

Os hooks foram validados contra o código-fonte de Anki 25.09.4: `deck_browser_will_render_content`, `webview_will_set_content`, `webview_did_receive_js_message` e `operation_did_execute`. O add-on usa as operações públicas `set_current_deck`, `rename_deck`, `remove_decks` e `display_options_for_deck_id`. A única dependência estrutural do navegador é a árvore de renderização já carregada pelo próprio Deck Browser; caso uma versão futura a altere, desative o Explorador Visual nas configurações para recuperar imediatamente a lista nativa.

## Instalação local pelo código-fonte

Não confunda esta modalidade com instalar um `.ankiaddon`: aqui o Anki carrega diretamente esta pasta, ideal para desenvolvimento.

1. Feche o Anki.
2. Descubra o diretório de add-ons:

   - No Anki: **Ferramentas → Complementos → Ver arquivos**. A pasta aberta é `addons21`.
   - Windows (padrão): `%APPDATA%\Anki2\addons21`.
   - Linux (padrão): `~/.local/share/Anki2/addons21`.
   - macOS (padrão): `~/Library/Application Support/Anki2/addons21`.

3. Crie um link simbólico com o nome Python `powerful_studies` dentro de `addons21`.

Windows, PowerShell: prefira uma _junction_ (não exige Modo de Desenvolvedor nem terminal elevado e funciona como diretório normal para o Anki):

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\Anki2\addons21\powerful_studies" -Target "C:\caminho\para\powerful-studies"
```

Um link simbólico também funciona, mas requer Modo de Desenvolvedor ou privilégios administrativos no Windows.

Linux:

```bash
ln -s /caminho/para/powerful-studies ~/.local/share/Anki2/addons21/powerful_studies
```

4. Inicie o Anki. No Navegador de decks, o Explorador Visual aparece automaticamente.

O link elimina a necessidade de copiar arquivos a cada alteração. Reinicie o Anki para recarregar Python; CSS/JS também são recarregados ao voltar ao Navegador de decks.

Após alterar `__init__.py` ou a lista de arquivos exportados da WebView, feche e abra o Anki por completo. O registro de `setWebExports()` acontece durante a inicialização do add-on.

## Uso

- Clique no cartão para entrar em seus subdecks. Use a casa e o breadcrumb para voltar.
- Use a busca para filtrar cartões no nível atual.
- Marque os checkboxes dos decks ou use **Selecionar tudo** para selecionar todos os decks do nível atual. **Excluir selecionados** pede uma confirmação única e remove os decks selecionados, seus subdecks e cartões pela operação nativa do Anki.
- **Estudar** abre a visão geral nativa, sem iniciar revisão automaticamente.
- Use `••• → Personalizar deck` para definir ícone, emoji, fundo e descrição de até 530 caracteres. **Restaurar padrão** remove somente a aparência daquele deck.
- Use `•••` para operações nativas de opções, renomear, exportar e excluir. Excluir é a operação nativa do Anki e tem as mesmas consequências/confirmações dessa operação.

### Visão geral do deck

Ao abrir um deck, o Powerful Studies também substitui a visão geral por um painel de flashcards. Ele mostra contagens nativas disponíveis para estudo, total de cards encontrados e uma página de até 25 cards reais do deck. A busca é enviada à pesquisa nativa do Anki ao pressionar `Enter`; os filtros de estado e inclusão de subdecks também usam `Collection.find_cards()`.

Mesmo quando não há cards disponíveis para estudar, a tela continua acessível e exibe **Revisões concluídas por hoje**. Use **Novo subdeck** para criar um filho do deck aberto. **Novo card** abre o criador original do Anki já apontando para o deck atual; nele é possível escolher Basic, Cloze, Image Occlusion e qualquer outro tipo de nota disponível no perfil, com todos os recursos nativos de formatação, mídia e edição.

Use **Ver resposta** para expandir a representação segura em texto do verso e **Editar** para abrir o Navegador/Editor nativo da nota correspondente. A seleção é feita por ID de card; **Selecionar página** afeta apenas os 25 itens visíveis. Excluir informa o número de notas e cards irmãos afetados, pois a operação nativa remove notas inteiras. A interface não altera o scheduler.

### Tela de revisão

Durante a revisão, o add-on adiciona um breadcrumb com o caminho real do deck e controles para **Decks**, **Visão geral**, **Editar** e **Excluir nota**. Os controles são inseridos fora do conteúdo do cartão: a pergunta, resposta, áudio, imagens, vídeo, fórmulas MathJax, atalhos e os botões nativos de avaliação permanecem sendo renderizados e controlados pelo Reviewer do Anki.

**Editar** abre o Browser/Editor nativo já focado na nota do card atual. **Excluir nota** informa quantos cards são gerados pela nota antes de pedir confirmação e usa a operação nativa de remoção, que mantém o mecanismo de desfazer quando disponível. Não existe exclusão silenciosa de card isolado.

Use **Decks** ou **Visão geral** para sair da revisão pela navegação nativa. O modo de compatibilidade, ativado por padrão, não altera cores, fontes ou layout internos definidos pelo template do card.

Para cards sem `Styling`, abra **Ferramentas → Powerful Studies** e mantenha ativados **Usar layout visual do Powerful Studies na revisão** e **Aplicar tipografia base ao conteúdo**. É possível ajustar a largura máxima entre 900 e 1000px e ativar ou desativar o destaque do verso. O layout-base adiciona espaçamento a parágrafos, listas, títulos e citações, além de separar a resposta com `hr#answer`, sem modificar o HTML, os atributos inline, imagens, áudio, vídeo ou fórmulas do card.

A revisão apresenta a pergunta em um painel **Frente**. Depois de **Mostrar resposta**, o conteúdo de resposta do Anki aparece em um segundo painel **Verso**, visualmente destacado. Os elementos originais apenas são agrupados em contêineres visuais; não são convertidos nem recriados, preservando mídia, MathJax e comportamento do template.

O layout é preparado no ciclo de atualização do próprio Reviewer (`card_will_show` e `onUpdateHook`), antes de o conteúdo do card se tornar visível. Assim, ele não depende de cliques, atrasos artificiais ou de recarregar a WebView para reaparecer ao mudar de pergunta, revelar a resposta ou avançar para o próximo card.

## Desenvolvimento e testes

Na raiz do projeto:

```powershell
python -m unittest discover -s tests -v
python scripts/package_addon.py
```

### Formatação

O projeto usa **Prettier** para CSS, JavaScript, JSON e Markdown, e **Ruff** para Python. São ferramentas de desenvolvimento: o Anki não precisa de npm, Node ou Ruff para executar o add-on.

```powershell
npx prettier@3.5.3 --write "web/**/*.js" "web/**/*.css" "*.json" "README.md"
npx prettier@3.5.3 --check "web/**/*.js" "web/**/*.css" "*.json" "README.md"
ruff format .
ruff check .
```

Os testes unitários não importam `aqt`, não acessam seu perfil e não exercitam agendamento. Testes de integração Qt/Anki devem usar uma coleção temporária — nunca um perfil real. Antes de publicar, teste manualmente criação, renomeação, sincronização e visualização da lista nativa em uma cópia descartável de coleção.

## Empacotamento e instalação do pacote

Para gerar o pacote:

```powershell
python scripts/package_addon.py
```

O arquivo `dist/powerful-studies.ankiaddon` é criado. Para instalar esse arquivo em vez do código-fonte: no Anki, abra **Ferramentas → Complementos → Instalar por arquivo...**, selecione o `.ankiaddon` e reinicie. Não mantenha simultaneamente o pacote instalado e o link simbólico do mesmo add-on.

## Solução de problemas e desinstalação

- Para erros de carregamento, abra **Ferramentas → Complementos**, selecione o add-on e consulte a saída/depuração do Anki; iniciar pelo terminal também expõe o traceback.
- Se uma atualização do Anki alterar o Deck Browser, abra Complementos, desative **Powerful Studies** e reinicie. A lista e seus decks continuam nativos e intactos.
- Para desinstalar o desenvolvimento, feche o Anki e remova apenas o link `addons21/powerful_studies`. Para uma instalação empacotada, use **Complementos → Excluir**.
- Nenhuma dessas ações exclui decks, cartões ou notas nativas. Se também quiser descartar preferências visuais, remova manualmente `<pasta-do-perfil>/powerful-studies` após fechar o Anki.
