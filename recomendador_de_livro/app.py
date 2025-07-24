
# Para executar:
# 1. Instale as dependências: pip install Flask neo4j python-dotenv Flask-Cors
# 2. Crie um arquivo .env na mesma pasta com suas credenciais do Neo4j:
#    NEO4J_URI=bolt://localhost:7687
#    NEO4J_USERNAME=neo4j
#    NEO4J_PASSWORD=your_neo4j_password
# 3. Execute: python app.py

from flask import Flask, request, jsonify
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from flask_cors import CORS # Importa a extensão CORS

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
CORS(app) # Habilita CORS para todas as rotas da aplicação

# Configurações do Neo4j
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Inicializa o driver do Neo4j
driver = None # Inicializa como None para garantir que esteja definido
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    # Testa a conexão
    with driver.session() as session:
        session.run("RETURN 1")
    print("Conexão com Neo4j estabelecida com sucesso.")
except Exception as e:
    print(f"Erro ao conectar ao Neo4j: {e}")
    # driver permanece None se a conexão falhar

# Função para fechar a conexão com o banco de dados ao desligar o aplicativo
@app.teardown_appcontext
def close_db(error):
    if driver:
        driver.close()
        print("Conexão com Neo4j fechada.")

# Endpoint de recomendação de livros
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    if not driver:
        return jsonify({"error": "Banco de dados não conectado."}), 500

    genre = request.args.get('genre')
    author = request.args.get('author')

    if not genre:
        return jsonify({"error": "O parâmetro 'genre' é obrigatório."}), 400

    query = """
        MATCH (l:Livro)-[:TEM_GENERO]->(g:Genero)
        WHERE toLower(g.nome) CONTAINS toLower($genre)
    """
    params = {"genre": genre}

    query += """
        OPTIONAL MATCH (l)-[:ESCRITO_POR]->(a:Autor)
    """

    if author and author.lower() != 'qualquer':
        query += """
            WHERE toLower(a.nome) CONTAINS toLower($author)
        """
        params["author"] = author

    query += """
        RETURN l.titulo AS title, a.nome AS author, g.nome AS genre
        LIMIT 3
    """

    try:
        with driver.session() as session:
            result = session.run(query, params)
            recommendations = []
            for record in result:
                recommendations.append({
                    "title": record["title"],
                    "author": record["author"] if record["author"] is not None else "Desconhecido",
                    "genre": record["genre"]
                })
            return jsonify(recommendations), 200
    except Exception as e:
        print(f"Erro ao executar consulta Cypher: {e}")
        return jsonify({"error": "Erro interno do servidor ao buscar recomendações."}), 500

# Endpoint para executar consulta Cypher
@app.route('/api/cypher', methods=['POST'])
def execute_cypher_query():
    if not driver:
        return jsonify({"error": "Banco de dados não conectado."}), 500
    
    data = request.get_json()
    query = data.get('query')
    params = data.get('params', {}) 

    if not query:
        return jsonify({"error": "A consulta Cypher é obrigatória."}), 400

    try:
        with driver.session() as session:
            result = session.run(query, params)
            records = []
            try:
                for record in result:
                    records.append(record.data())
            except Exception:
                # Se não for uma consulta que retorna dados (ex: CREATE, DELETE),
                # result.data() pode falhar. Capturamos metadados da transação.
                summary = result.consume()
                records.append({
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set,
                    "labels_added": summary.counters.labels_added,
                    "labels_removed": summary.counters.labels_removed,
                    "message": "Consulta executada com sucesso. Verifique os contadores."
                })
            return jsonify(records), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao executar consulta Cypher: {str(e)}"}), 500

# Funções auxiliares para contagem de nós 
def get_node_count(label):
    if not driver: return 0
    try:
        with driver.session() as session:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
            return result.single()["count"]
    except Exception as e:
        print(f"Erro ao contar nós {label}: {e}")
        return 0

@app.route('/api/stats/total_authors', methods=['GET'])
def total_authors():
    return jsonify({"count": get_node_count("Autor")})

@app.route('/api/stats/total_books', methods=['GET'])
def total_books():
    return jsonify({"count": get_node_count("Livro")})

@app.route('/api/stats/total_genres', methods=['GET'])
def total_genres():
    return jsonify({"count": get_node_count("Genero")})

@app.route('/api/stats/total_publishers', methods=['GET'])
def total_publishers():
    return jsonify({"count": get_node_count("Editora")})

@app.route('/api/stats/most_productive_authors', methods=['GET'])
def most_productive_authors():
    if not driver: return jsonify([])
    try:
        with driver.session() as session:
            query = """
            MATCH (a:Autor)-[:ESCRITO_POR]->(l:Livro)
            RETURN a.nome AS author, count(l) AS bookCount
            ORDER BY bookCount DESC
            LIMIT 3
            """
            result = session.run(query)
            return jsonify([record.data() for record in result]), 200
    except Exception as e:
        print(f"Erro ao buscar autores mais produtivos: {e}")
        return jsonify({"error": f"Erro ao buscar autores mais produtivos: {str(e)}"}), 500

@app.route('/api/stats/most_popular_genres', methods=['GET'])
def most_popular_genres():
    if not driver: return jsonify([])
    try:
        with driver.session() as session:
            query = """
            MATCH (g:Genero)<-[:TEM_GENERO]-(l:Livro)
            RETURN g.nome AS genre, count(l) AS bookCount
            ORDER BY bookCount DESC
            LIMIT 3
            """
            result = session.run(query)
            return jsonify([record.data() for record in result]), 200
    except Exception as e:
        print(f"Erro ao buscar gêneros mais populares: {e}")
        return jsonify({"error": f"Erro ao buscar gêneros mais populares: {str(e)}"}), 500

# Endpoint para limpar banco de dados
@app.route('/api/clear_database', methods=['POST'])
def clear_database_endpoint():
    if not driver:
        return jsonify({"error": "Banco de dados não conectado."}), 500
    try:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        return jsonify({"message": "Banco de dados limpo com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao limpar o banco de dados: {e}")
        return jsonify({"error": f"Erro ao limpar o banco de dados: {str(e)}"}), 500

# Endpoint para testar conexao
@app.route('/api/test_connection', methods=['GET'])
def test_connection_endpoint():
    if driver:
        try:
            with driver.session() as session:
                session.run("RETURN 1") # Consulta simples para verificar a conectividade
            return jsonify({"status": "connected", "message": "Conexão com Neo4j estabelecida."}), 200
        except Exception as e:
            return jsonify({"status": "disconnected", "message": f"Erro na conexão com Neo4j: {str(e)}"}), 500
    else:
        return jsonify({"status": "disconnected", "message": "Driver Neo4j não inicializado."}), 500

# Endpoint para adicionar livro
@app.route('/api/add_book', methods=['POST'])
def add_book():
    if not driver:
        return jsonify({"error": "Banco de dados não conectado."}), 500

    data = request.get_json()
    title = data.get('title')
    author_name = data.get('author')
    genres_str = data.get('genres', '') 
    publisher_name = data.get('publisher')
    year = data.get('year')
    pages = data.get('pages')

    # Validação basica
    if not all([title, author_name, genres_str]):
        return jsonify({"error": "Título, autor e pelo menos um gênero são obrigatórios."}), 400

    genres = [g.strip() for g in genres_str.split(',') if g.strip()] # Divide e limpa a string de gêneros

    try:
        with driver.session() as session:

            session.run("MERGE (a:Autor {nome: $author_name})", {"author_name": author_name})

            if publisher_name:
                session.run("MERGE (p:Editora {nome: $publisher_name})", {"publisher_name": publisher_name})

            book_props = {"titulo": title}
            if year:
                try:
                    book_props["ano"] = int(year)
                except ValueError:
                    return jsonify({"error": "Ano deve ser um número válido."}), 400
            if pages:
                try:
                    book_props["paginas"] = int(pages)
                except ValueError:
                    return jsonify({"error": "Páginas deve ser um número válido."}), 400

          
            session.run("""
                MERGE (l:Livro {titulo: $title})
                ON CREATE SET l += $properties
            """, {"title": title, "properties": book_props})

        
            session.run("""
                MATCH (l:Livro {titulo: $title})
                MATCH (a:Autor {nome: $author_name})
                MERGE (l)-[:ESCRITO_POR]->(a)
            """, {"title": title, "author_name": author_name})

         
            for genre_name in genres:
                session.run("""
                    MERGE (g:Genero {nome: $genre_name})
                    WITH g
                    MATCH (l:Livro {titulo: $title})
                    MERGE (l)-[:TEM_GENERO]->(g)
                """, {"genre_name": genre_name, "title": title})

       
            if publisher_name:
                session.run("""
                    MATCH (l:Livro {titulo: $title})
                    MATCH (p:Editora {nome: $publisher_name})
                    MERGE (l)-[:PUBLICADO_POR]->(p)
                """, {"title": title, "publisher_name": publisher_name})

            return jsonify({"message": f"Livro '{title}' adicionado/atualizado com sucesso!"}), 201 
    except Exception as e:
        print(f"Erro ao adicionar livro: {e}")
        return jsonify({"error": f"Erro interno do servidor ao adicionar livro: {str(e)}"}), 500

if __name__ == '__main__':

    app.run(debug=True, port=5000)
