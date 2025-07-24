#  Guia de Instalação do Neo4j Desktop no Windows

Este guia irá ajudá-lo a baixar, instalar e configurar o **Neo4j Desktop** para utilizar localmente em seus projetos.

---

##  1. Baixando o Neo4j Desktop

1. Acesse o site oficial: [https://neo4j.com/download](https://neo4j.com/download)
2. Clique em **"Download Desktop"**
3. Crie uma conta gratuita ou entre com a sua conta existente (necessário para liberar o download)
4. Escolha a versão para **Windows** e aguarde o download do instalador (`.exe`)

---

##  2. Instalando o Neo4j Desktop

1. Execute o arquivo `.exe` baixado
2. Siga as instruções do assistente de instalação (Next, Install...)
3. Após a instalação, abra o **Neo4j Desktop**
4. Crie um novo projeto
5. Clique em **"Create instance"** → **"Local DBMS"**
6. Dê um nome ao banco (ex: `biblioteca-db`), defina uma senha (ex: `admin123`) e clique em **Create**

>  Você precisará usar a senha definida no arquivo `.env`

---

## 3. Iniciando o Banco de Dados

1. Dentro do seu projeto no Neo4j Desktop, localize o DBMS criado
2. Clique em **"Start"** para iniciar o banco
3. Aguarde até o status mostrar `Running`
4. A partir dai você ja pode fazer consultas e popular seu BD. Para iso clique em **"Query"** e ao lado de "**neo4j$**"
digite o que você deseja
5. Popule o banco copiando o conteúdo do arquivo população_neo.txt que se encontra nesse repositório também
---

## 4. Verificando a Porta de Conexão

- A porta padrão do Neo4j é `7687` (protocolo `bolt`), usada para conectar com o backend Flask
- No seu arquivo `.env`, use as seguintes variáveis:
- Você pode achar a URI indo no campo local instances. Você vai localizar o "**Connection URI**"  use isso no seu arquivo .env

```
NEO4J_URI=URI_do_seu_bd
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=sua_senha_definida
```

---

## 5. Testando a Conexão

Após iniciar o backend Flask (`python app.py`), você pode acessar no navegador:

```
http://localhost:5000/api/test_connection
```

Se tudo estiver funcionando corretamente, você verá uma resposta como:

```json
{
  "status": "connected",
  "message": "Conexão com Neo4j estabelecida."
}
```

---

