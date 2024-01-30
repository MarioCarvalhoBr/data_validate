# Manual de Revisão de Commit

O uso de repositórios GIT tem diversos benefícios: trabalho em equipe,
desenvolvimento de recursos separadamente, histórico das alterações, etc.
Mas para disponibilizar todo o potencial é preciso um pouco de dedicação
no momento do _commit_.

Não é preciso uma vasta experiência para já ter passado por situações como
conflito de arquivos onde a mensagem não traz nenhuma informações relevante
e é preciso inverstigar o que a outra pessoa estava desenvolvendo ou após
atualizar o repositório ver uma mensagem de depuração no meio da aplicação.

Ao fazer _commit_ recomendo reservar uns 5 minutos para dar atenção especial
a:
- sincronização do repositório remoto
- revisar código
- conferir arquivos que serão incluídos (_staged_)
- mensagem de _commit_.


## Configuração inicialdo git.name e git.email
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"
```
Para ver as configurações
```bash
git config --list
```

## Primeiro _pull_ então _commit_ depois _push_

A simples execução do comando `git pull` evita _merges_ desnecessários que
"sujam" o histórico do repositório e retrabalhos inesperados que podem surgir
ao fazer _push_.

Ao sincronizar com o repositório remoto antes de iniciar o _commit_ possíveis
conflitos de código são antecipados e podem ser resolvidos junto com a revisão
do código, unificar essas duas tarefas faz parecer uma só.

Tão importante quanto _pull_ é o _push_, que deve ser feito logo após o commit,
principalmente se houver outras pessoas trabalhando no mesmo recurso, caso
contrário o cuidado será em vão, pois as situações apresentadas antes podem
acontecer.

## Revisão de código e arquivos incluídos

Por favor, não negligencie essa etapa com `git add .` a pressa e falta de
cuidado podem causar pequenos problemas que atrapalham o trabalho.

É possivel fazer essa tarefa usando apenas o terminal executando o comando
`git diff`, mas usar a IDE vai facilitar muito pois a maioria delas oferece
comparação lado a lado da versão atual e anterior do arquivo. Nesse momento
você terá a oportunidade de ler o código escrito, refinar a lógica, ajustar
nomes de funções e variáveis e remover códigos de depuração e alterações feitas
apenas para teste.

Se após revisar houver certeza que todos os arquivos devem fazer parte do _commit_
use `git add .`, caso contrário a inclusão ou _stage_ deve ser feita um arquivo
por vez, adicionando apenas dos arquivos que de fato fazem parte do recurso.
Novamente a IDE pode ajudar nessa etapa, que também pode ser feita por linha de
comando.

## Recomendações para uma boa mensagem [<sup>1</sup>][1]

_T.L. D.R._ (Longo demais, não li):

1. Separar título e descrição com uma linha em branco
2. Tente limitar o título a 50 caracteres, ou no máximo 72
3. Iniciar título com letra maiúscula
4. O título não deve terminar com ponto
5. Use o modo indicativo do presente no título
6. Na descrição faça quebras de linha em até 72 caracteres
7. Use a descrição para explicar o que e o porquê e não como

Exemplo:

``` markdown
Resume alteração em 50 caracteres

Texto com explicação mais detalhada, caso necessário. Com quebra de
linha em 72 caracteres ou menos. A primeira linha é o título e o
restante do texto a descrição. A linha em branco separando os dois é
obrigatória (a menos que não tenha descrição); vários comandos como
`log`, `shotlog` e `rebase` se comportam de forma inesperada se os dois
elementos estiverem juntos.

Explicação do problema que o _commit_ resolve. Focando no motivo ao
invés como (isso o código explica). Existem efeitos colaterais ou
consequências não intuitívas? Aqui é o local para dizer.

 - listas funcionam

 - geralmente com um hífem ou asterisco, precedido de espaço, com 
   linhas entre os items

É possivel referenciar _issues_:

Resolve: #123
```

Agora, vamos detalhar cada um dos itens destacados.

### Separar título e descrição com uma linha em branco

Nem todo _commit_ precisa de título e descrição. Muitas vezes apenas uma
linha é o suficiente, especialmente quando é feita uma mudança simples.
Por exemplo:

> Corrige erro de digitação no dashboard

Não há mais nada para dizer. Para saber qual foi o erro, basta ver a
alteração com `git show`, `git diff` ou `git log -p`.

Quando o _commit_ merece um pouco de contextualização e/ou explicação, use
a descrição. Por exemplo:

```text
Exibe legenda "sem dados" no gráfico e remove consulta por mês

Os dados da consulta mensal são os mesmos da lista de procedimentos,
remove a consulta e consolida os dados pela lista no front-end.
```

Mensagens de _commit_ com descrição são complicadas para escrever com o 
parâmetro `-m`. Nesses casos é necessário ter configurado um editor como 
vim ou nano, ou usar uma IDE com suporte de mensagem de _commit_ multi-linha.

De qualquer forma a separação se torna evidente ao navegar pelo histórico.
Essa é uma entrada de log completa:

```text
commit 6f668d049f1fef12d775da57dd8fdd8ef81fa1dc
Author: Pedro Sanção <pedrosancao@users.noreply.github.com>
Date:   Wed Jan 15 12:06:58 2020 -0200

    Exibe legenda "sem dados" no gráfico e remove consulta por mês
    
    Os dados da consulta mensal são os mesmos da lista de procedimentos,
    remove a consulta e consolida os dados pela lista no front-end.
```

E essa é a mesma entrada com `git log --oneline`:

```text
6f668d Exibe legenda "sem dados" no gráfico e remove consulta por mês
```

### Tente limitar o título a 50 caracteres, ou no máximo 72

Manter o título com menos de 50 caracteres torna ele legível no histórico
e te força a pensar na forma mais concisa de explicar o que está acontecendo.

Se for muito difícil resumir, é possível que o _commit_ tenha uma alteração
muito grande e pode ser necessário dividi-lo.

### Iniciar título com letra maiúscula

Simples como escrito. O título deve ser iniciado com letra maiúscula.

Use:

> Adiciona contâiner do banco de dados Oracle &#x2714;

Ao invés de:

> adiciona contâiner do banco de dados Oracle &#x274C;

### O título não deve terminar com ponto

Estamos tentando resumir o título em 50 caracteres, então por que gastar mais
um com o ponto final?

### Use o modo indicativo do presente no título

O modo indicativo é um modo verbal que expressa uma certeza, um fato.

Se a mensagem de _commit_ for em inglês o tempo verbal recomendado é o
imperativo, que geralmente representa uma ordem ou comando.

Algumas vezes essa forma pode parecer rude e por isso é pouco usada. Mas é
perfeita para os títulos. O próprio GIT usa essa forma ao fazer commits por
você.

Por exemplo, a mensagem padrão de _merge_:

> Merge 'my featur' into develop

Ou em tradução livre:

> Mescla ramificação 'meu-recurso' para develop

Ou `git revert`:

> Reverte "Cria recurso experimental"

Então ao escrever mensagens de _commit_ use o modo indicativo no presente, por
exemplo:

- Atualiza estilos da página inicial &#x2714;
- Trata exceção de tempo expirado na sincronização &#x2714;
- Corrige bug da interação de filtros &#x2714;
- Adiciona cliente da API de pagamentos &#x2714;

Escrever dessa forma pode ser estranho no começo. Estamos mais acostumados a
usar o tempo passado ou gerúdio ao descrever as mudanças, por isso é comum
encontrar títulos como:

- Corrigindo bug no envio de e-mail &#x274C;
- Atualizei texto do blog &#x274C;

E algumas vezes a mensagem é a descrição do conteúdo

- Endpoint da API para importação &#x274C;
- Novo fluxo de compra &#x274C;

Para evitar confusão há uma regra simples para acertar todas as vezes. O título
deve completar a frase "Se aplicado, esse commit **seu título**". Por exemplo:

- Se aplicado, esse commit **atualiza estilos da página inicial** &#x2714;
- Se aplicado, esse commit **trata exceção de tempo expirado na sincronização** &#x2714;
- Se aplicado, esse commit **corrige bug da interação de filtros** &#x2714;
- Se aplicado, esse commit **adiciona cliente da API de pagamentos** &#x2714;

Veja como não faz sentido ao usar com outras formas:

- Se aplicado, esse commit **corrigindo bug no envio de e-mail** &#x274C;
- Se aplicado, esse commit **atualizei texto do blog** &#x274C;
- Se aplicado, esse commit **endpoint da API para importação** &#x274C;
- Se aplicado, esse commit **novo fluxo de compra** &#x274C;

Lembrando que esse modo se aplica apenas ao título. A descrição não está
limitada a essa restrição.

### Na descrição faça quebras de linha em até 72 caracteres

O GIT nunca faz quebras de linha automaticamente. Ao escrever a descrição do
_commit_ você precisa medir a margem direita e quebrar linha manualmente.

A recomendação de 72 caracteres é para que o GIT tenha espaço para indentar,
e manter tudo em menos de 80 caracteres.

Um editor pode ajudar aqui. É possível configurar plugins do Vim para fazer as
quebras de linhas por você. Algumas _IDEs_ suportam mensagens multi-linha e já
tem uma linha após o 72º caracter.

### Use a descrição para explicar o que e o porquê e não como

Eis um exemplo de uma mensagem destacando o quê mudou e o porquê:

```
    Grava estado dos dados simulados no teste de interface

    Grava o estado dos dados aleatórios gerados para posterior manipulação
    tornando o comportamento da inteface mais próximo do que acontece com
    dados reais.

    O estado foi armazenado no cache da aplicação para que todos os
    usuários vejam os mesmos dados permitindo comparação entre navegadores
    distintos.
```

Nesse exemplo a alteração foi contextualizada e as escolhas explicadas. O que
pode salvar tempo para a próxima pessoa que alterar o código em questão. Caso
as informações fornecidas não fossem registradas aqui elas seriam perdidas para
sempre.

Na maioria dos casos, você pode deixar de lado como a alteração foi feita.
Geralmente o código é auto-explicativo. Se for complexo demais comentários de
código pontuais são permitidos. Deixe claro os motivos para a mudança, a forma
de funcionamento antes da alteração e qual o problema existente, como funciona
agora e porque você decidiu resolver dessa forma.

A próxima pessoa que vai te agradecer pode ser você mesmo.

## Interfaces que podem ajudar

- gitg
- plugin GitLens para VSCode
- plugin GitToolbox para PHP Storm

[1]: https://chris.beams.io/posts/git-commit/#seven-rules