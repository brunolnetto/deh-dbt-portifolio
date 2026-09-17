-- =================================================================
-- LANDING SEED DATA — Sample data for CI and local testing
-- =================================================================
-- Used by: GitHub Actions CI (after init.sql creates schemas/tables)
-- Used by: docker-compose local development (after extractor populates data)
-- Replaces: hard-coded INSERT statements in CI workflow

-- Varejo landing seed
INSERT INTO landing_varejo.clientes (cliente_id, nome, estado, segmento, data_cadastro, updated_at) VALUES
(101, 'João Silva', 'SP', 'Ouro', '2023-01-15', now()),
(102, 'Maria Santos', 'RJ', 'Bronze', '2023-05-20', now()),
(103, 'Pedro Costa', 'MG', 'Prata', '2024-02-10', now());

INSERT INTO landing_varejo.produtos (produto_id, nome_produto, categoria, preco_sugerido, updated_at) VALUES
('PROD001', 'Notebook Dell i5', 'Informática', 3500.00, now()),
('PROD002', 'Mouse Logitech MX', 'Informática', 250.00, now()),
('PROD003', 'Teclado Mecânico RGB', 'Informática', 350.00, now());

INSERT INTO landing_varejo.vendas (venda_id, data_venda, produto_id, cliente_id, quantidade, valor_total, status, created_at, updated_at) VALUES
(1, '2024-05-04', 'PROD001', 101, 1, 3500.00, 'pago', now(), now()),
(2, '2024-05-05', 'PROD001', 101, 2, 7000.00, 'pago', now(), now()),
(3, '2024-06-15', 'PROD003', 101, 1, 350.00, 'pago', now(), now());

-- Biblioteca landing seed
INSERT INTO landing_biblioteca.usuarios (usuario_id, nome, tipo, email, updated_at) VALUES
(201, 'João Ferreira', 'aluno', 'joao@biblioteca.br', now()),
(202, 'Maria Oliveira', 'professor', 'maria@biblioteca.br', now());

INSERT INTO landing_biblioteca.livros (livro_id, titulo, isbn, ano_publicacao, quantidade_disponivel, updated_at) VALUES
(301, 'Dom Casmurro', '9788520927978', 1899, 3, now()),
(302, 'A Hora da Estrela', '9788532518101', 1977, 2, now());

INSERT INTO landing_biblioteca.emprestimos (emprestimo_id, usuario_id, livro_id, data_emprestimo, data_devolucao_prevista, data_devolucao_real, updated_at) VALUES
(401, 201, 301, '2024-05-01', '2024-06-01', NULL, now()),
(402, 202, 302, '2024-05-10', '2024-06-10', '2024-05-25', now());

INSERT INTO landing_biblioteca.autores (autor_id, nome, nacionalidade, data_nascimento, updated_at) VALUES
(501, 'Machado de Assis', 'Brasileiro', '1839-06-21', now()),
(502, 'Clarice Lispector', 'Brasileira', '1920-12-10', now());

INSERT INTO landing_biblioteca.multas (multa_id, emprestimo_id, valor_multa, pago, updated_at) VALUES
(601, 402, 15.00, TRUE, now());

-- Rede Social landing seed
INSERT INTO landing_rede_social.pessoas (pessoa_id, nome, idade, updated_at) VALUES
(701, 'Alice Silva', 28, now()),
(702, 'Bruno Costa', 35, now()),
(703, 'Carla Santos', 31, now());

INSERT INTO landing_rede_social.leituras (pessoa_id, livro_id, nota, data_leitura, updated_at) VALUES
(701, 301, 4.5, '2024-05-01', now()),
(702, 302, 5.0, '2024-05-05', now()),
(703, 301, 4.0, '2024-05-10', now());

INSERT INTO landing_rede_social.conexoes (seguidor_id, seguido_id, forca_conexao, data_conexao, updated_at) VALUES
(701, 702, 0.95, '2024-01-01', now()),
(702, 703, 0.87, '2024-01-15', now()),
(703, 701, 0.92, '2024-02-01', now());

INSERT INTO landing_rede_social.generos (genero_id, nome, updated_at) VALUES
(801, 'Romance', now()),
(802, 'Ficção Científica', now()),
(803, 'Mistério', now());

INSERT INTO landing_rede_social.livros (livro_id, titulo, autor, ano_publicacao, updated_at) VALUES
(301, 'Dom Casmurro', 'Machado de Assis', 1899, now()),
(302, 'A Hora da Estrela', 'Clarice Lispector', 1977, now()),
(303, 'Grande Sertão: Veredas', 'Guimarães Rosa', 1956, now());
