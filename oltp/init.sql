-- =================================================================
-- PORTIFÓLIO OLTP: varejo + biblioteca + rede_social
-- =================================================================

CREATE SCHEMA IF NOT EXISTS varejo;
CREATE SCHEMA IF NOT EXISTS biblioteca;
CREATE SCHEMA IF NOT EXISTS rede_social;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =================================================================
-- SYSTEM — operational logs (written by services, read by dbt)
-- =================================================================
CREATE SCHEMA IF NOT EXISTS system;

CREATE TABLE system.request_log (
    id          BIGSERIAL PRIMARY KEY,
    service     TEXT NOT NULL,
    method      TEXT NOT NULL,
    endpoint    TEXT NOT NULL,
    status_code INT,
    duration_ms DOUBLE PRECISION,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE system.app_log (
    id         BIGSERIAL PRIMARY KEY,
    service    TEXT NOT NULL,
    level      TEXT NOT NULL,
    logger     TEXT,
    message    TEXT NOT NULL,
    extra      JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =================================================================
-- LANDING — populated by extractor on each extraction cycle
-- =================================================================
CREATE SCHEMA IF NOT EXISTS landing_varejo;
CREATE SCHEMA IF NOT EXISTS landing_biblioteca;
CREATE SCHEMA IF NOT EXISTS landing_rede_social;

-- Varejo landing tables
CREATE TABLE landing_varejo.clientes (
    cliente_id    INTEGER PRIMARY KEY,
    nome          VARCHAR(100),
    estado        CHAR(2),
    segmento      VARCHAR(50),
    data_cadastro DATE,
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_varejo.produtos (
    produto_id     VARCHAR(20) PRIMARY KEY,
    nome_produto   VARCHAR(200),
    categoria      VARCHAR(50),
    preco_sugerido DECIMAL(10, 2),
    updated_at     TIMESTAMP,
    _extracted_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_varejo.vendas (
    venda_id      INTEGER PRIMARY KEY,
    data_venda    DATE,
    produto_id    VARCHAR(20),
    cliente_id    INTEGER,
    quantidade    INTEGER,
    valor_total   DECIMAL(10, 2),
    status        VARCHAR(20),
    created_at    TIMESTAMP,
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Biblioteca landing tables
CREATE TABLE landing_biblioteca.usuarios (
    usuario_id    INTEGER PRIMARY KEY,
    nome          VARCHAR(100),
    tipo          VARCHAR(20),
    email         VARCHAR(100),
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_biblioteca.livros (
    livro_id              INTEGER PRIMARY KEY,
    titulo                VARCHAR(200),
    isbn                  VARCHAR(13),
    ano_publicacao        INTEGER,
    quantidade_disponivel INTEGER,
    updated_at            TIMESTAMP,
    _extracted_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_biblioteca.emprestimos (
    emprestimo_id           INTEGER PRIMARY KEY,
    usuario_id              INTEGER,
    livro_id                INTEGER,
    data_emprestimo         DATE,
    data_devolucao_prevista DATE,
    data_devolucao_real     DATE,
    updated_at              TIMESTAMP,
    _extracted_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_biblioteca.autores (
    autor_id        INTEGER PRIMARY KEY,
    nome            VARCHAR(100),
    nacionalidade   VARCHAR(50),
    data_nascimento DATE,
    updated_at      TIMESTAMP,
    _extracted_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_biblioteca.multas (
    multa_id      INTEGER PRIMARY KEY,
    emprestimo_id INTEGER,
    valor_multa   DECIMAL(10, 2),
    pago          BOOLEAN,
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Rede Social landing tables
CREATE TABLE landing_rede_social.pessoas (
    pessoa_id     INTEGER PRIMARY KEY,
    nome          VARCHAR(100),
    idade         INTEGER,
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_rede_social.leituras (
    leitura_id    SERIAL PRIMARY KEY,
    pessoa_id     INTEGER,
    livro_id      INTEGER,
    nota          DECIMAL(3, 1),
    data_leitura  DATE,
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_rede_social.conexoes (
    conexao_id    SERIAL PRIMARY KEY,
    seguidor_id   INTEGER,
    seguido_id    INTEGER,
    forca_conexao DECIMAL(5, 2),
    data_conexao  DATE,
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_rede_social.generos (
    genero_id     INTEGER PRIMARY KEY,
    nome          VARCHAR(50),
    updated_at    TIMESTAMP,
    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE landing_rede_social.livros (
    livro_id       INTEGER PRIMARY KEY,
    titulo         VARCHAR(200),
    autor          VARCHAR(100),
    ano_publicacao INTEGER,
    updated_at     TIMESTAMP,
    _extracted_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =================================================================
-- LANDING SEED DATA — Sample data for CI and local testing
-- =================================================================
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

-- =================================================================
-- VAREJO
-- =================================================================
CREATE TABLE varejo.origem_cliente (
    cliente_id    INTEGER PRIMARY KEY,
    nome          VARCHAR(100) NOT NULL,
    estado        CHAR(2),
    segmento      VARCHAR(50),
    data_cadastro DATE NOT NULL,
    updated_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE varejo.origem_produto (
    produto_id     VARCHAR(20) PRIMARY KEY,
    nome_produto   VARCHAR(200),
    categoria      VARCHAR(50),
    preco_sugerido DECIMAL(10, 2),
    updated_at     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE varejo.origem_venda (
    venda_id    SERIAL PRIMARY KEY,
    data_venda  DATE NOT NULL,
    produto_id  VARCHAR(20) NOT NULL REFERENCES varejo.origem_produto(produto_id),
    cliente_id  INTEGER NOT NULL REFERENCES varejo.origem_cliente(cliente_id),
    quantidade  INTEGER NOT NULL,
    valor_total DECIMAL(10, 2) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pago'
                    CHECK (status IN ('pendente', 'pago', 'cancelado', 'devolvido')),
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_at  TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO varejo.origem_cliente (cliente_id, nome, estado, segmento, data_cadastro) VALUES
(101, 'João Silva',    'SP', 'Ouro',   '2023-01-15'),
(102, 'Maria Santos',  'RJ', 'Bronze', '2023-05-20'),
(103, 'Pedro Costa',   'MG', 'Prata',  '2024-02-10'),
(104, 'Ana Oliveira',  'PR', 'Bronze', '2023-08-11'),
(105, 'Carlos Mendes', 'SC', 'Ouro',   '2022-11-05'),
(106, 'Beatriz Lima',  'RS', 'Prata',  '2024-01-22'),
(107, 'Diego Souza',   'BA', 'Bronze', '2023-06-30'),
(108, 'Fernanda Reis', 'PE', 'Prata',  '2023-09-14');

INSERT INTO varejo.origem_produto (produto_id, nome_produto, categoria, preco_sugerido) VALUES
('PROD001', 'Notebook Dell i5',     'Informática', 3500.00),
('PROD002', 'Mouse Logitech MX',    'Informática',  250.00),
('PROD003', 'Teclado Mecânico RGB', 'Informática',  350.00),
('PROD004', 'Monitor 24" Full HD',  'Informática', 1200.00),
('PROD005', 'Headset Bluetooth',    'Acessórios',   299.00),
('PROD006', 'Webcam HD 1080p',      'Acessórios',   189.00),
('PROD007', 'Mesa Digitalizadora',  'Acessórios',   450.00),
('PROD008', 'SSD 1TB NVMe',         'Informática',  320.00),
('PROD009', 'Cadeira Gamer',        'Móveis',      1800.00),
('PROD010', 'Suporte para Monitor', 'Móveis',       150.00);

INSERT INTO varejo.origem_venda (data_venda, produto_id, cliente_id, quantidade, valor_total, status) VALUES
('2024-05-04', 'PROD001', 101, 1, 3500.00, 'pago'),
('2024-05-05', 'PROD001', 101, 2, 7000.00, 'pago'),
('2024-06-15', 'PROD003', 101, 1,  350.00, 'pago'),
('2024-06-28', 'PROD002', 101, 1,  250.00, 'pago'),
('2024-07-01', 'PROD002', 101, 1,  250.00, 'cancelado'),
('2024-07-03', 'PROD001', 101, 1, 3500.00, 'devolvido'),
('2024-05-10', 'PROD004', 102, 1, 1200.00, 'pago'),
('2024-05-20', 'PROD005', 102, 1,  299.00, 'pago'),
('2024-06-01', 'PROD006', 103, 2,  378.00, 'pago'),
('2024-06-10', 'PROD007', 104, 1,  450.00, 'cancelado'),
('2024-06-25', 'PROD008', 105, 1,  320.00, 'pago'),
('2024-07-05', 'PROD009', 106, 1, 1800.00, 'pago'),
('2024-07-10', 'PROD002', 107, 3,  750.00, 'pago'),
('2024-07-15', 'PROD010', 108, 2,  300.00, 'pendente'),
('2024-07-20', 'PROD003', 103, 1,  350.00, 'devolvido');

-- =================================================================
-- BIBLIOTECA
-- =================================================================
CREATE TABLE biblioteca.autor (
    autor_id        SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    nacionalidade   VARCHAR(50),
    data_nascimento DATE,
    updated_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE biblioteca.livro (
    livro_id              SERIAL PRIMARY KEY,
    titulo                VARCHAR(200) NOT NULL,
    isbn                  VARCHAR(13) UNIQUE,
    ano_publicacao        INTEGER,
    quantidade_disponivel INTEGER DEFAULT 0,
    updated_at            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE biblioteca.usuario (
    usuario_id SERIAL PRIMARY KEY,
    nome       VARCHAR(100) NOT NULL,
    tipo       VARCHAR(20) CHECK (tipo IN ('aluno', 'professor')) DEFAULT 'aluno',
    email      VARCHAR(100) UNIQUE,
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE biblioteca.livro_autor (
    livro_id INTEGER REFERENCES biblioteca.livro(livro_id),
    autor_id INTEGER REFERENCES biblioteca.autor(autor_id),
    PRIMARY KEY (livro_id, autor_id)
);

CREATE TABLE biblioteca.emprestimo (
    emprestimo_id           SERIAL PRIMARY KEY,
    usuario_id              INTEGER REFERENCES biblioteca.usuario(usuario_id),
    livro_id                INTEGER REFERENCES biblioteca.livro(livro_id),
    data_emprestimo         DATE NOT NULL DEFAULT CURRENT_DATE,
    data_devolucao_prevista DATE NOT NULL,
    data_devolucao_real     DATE,
    updated_at              TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE biblioteca.multa (
    multa_id      SERIAL PRIMARY KEY,
    emprestimo_id INTEGER UNIQUE REFERENCES biblioteca.emprestimo(emprestimo_id),
    valor_multa   DECIMAL(10, 2),
    pago          BOOLEAN DEFAULT FALSE,
    updated_at    TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO biblioteca.autor (nome, nacionalidade, data_nascimento) VALUES
('Machado de Assis',   'Brasileiro', '1839-06-21'),
('Clarice Lispector',  'Brasileira', '1920-12-10'),
('Jorge Amado',        'Brasileiro', '1912-08-10'),
('Guimarães Rosa',     'Brasileiro', '1908-06-27'),
('Graciliano Ramos',   'Brasileiro', '1892-10-27');

INSERT INTO biblioteca.livro (titulo, isbn, ano_publicacao, quantidade_disponivel) VALUES
('Dom Casmurro',             '9788520927978', 1899, 3),
('A Hora da Estrela',        '9788532518101', 1977, 2),
('Gabriela, Cravo e Canela', '9788535906295', 1958, 2),
('Grande Sertão: Veredas',   '9788520922534', 1956, 1),
('Memórias do Cárcere',      '9788520936046', 1953, 2),
('O Alienista',              '9788520929866', 1882, 4),
('A Paixão Segundo G.H.',    '9788532518118', 1964, 2),
('Capitães da Areia',        '9788535906301', 1937, 3);

INSERT INTO biblioteca.usuario (nome, tipo, email) VALUES
('João Ferreira',  'aluno',     'joao@biblioteca.br'),
('Maria Oliveira', 'professor', 'maria@biblioteca.br'),
('Carlos Santos',  'aluno',     'carlos@biblioteca.br'),
('Ana Pereira',    'aluno',     'ana@biblioteca.br'),
('Roberto Lima',   'professor', 'roberto@biblioteca.br'),
('Sandra Ramos',   'aluno',     'sandra@biblioteca.br');

INSERT INTO biblioteca.livro_autor (livro_id, autor_id) VALUES
(1, 1), (2, 2), (3, 3), (4, 4),
(5, 5), (6, 1), (7, 2), (8, 3);

INSERT INTO biblioteca.emprestimo
    (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista, data_devolucao_real)
VALUES
(1, 1, '2024-05-01', '2024-05-15', '2024-05-14'),
(2, 4, '2024-05-10', '2024-06-10', NULL),
(3, 2, '2024-04-01', '2024-04-15', '2024-04-20'),
(4, 6, '2024-05-20', '2024-06-03', '2024-06-02'),
(5, 5, '2024-03-01', '2024-03-15', NULL),
(6, 3, '2024-05-05', '2024-05-19', '2024-05-18'),
(1, 7, '2024-06-01', '2024-06-15', NULL),
(3, 1, '2024-04-25', '2024-05-09', '2024-05-08'),
(4, 8, '2024-05-15', '2024-05-29', '2024-05-28'),
(2, 6, '2024-06-05', '2024-06-19', NULL);

INSERT INTO biblioteca.multa (emprestimo_id, valor_multa, pago) VALUES
(3, 15.00, TRUE),
(5, 30.00, FALSE);

-- =================================================================
-- REDE SOCIAL
-- =================================================================
CREATE TABLE rede_social.pessoa (
    pessoa_id  SERIAL PRIMARY KEY,
    nome       VARCHAR(100) NOT NULL,
    idade      INTEGER,
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE rede_social.livro (
    livro_id       SERIAL PRIMARY KEY,
    titulo         VARCHAR(200) NOT NULL,
    autor          VARCHAR(100),
    ano_publicacao INTEGER,
    updated_at     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE rede_social.genero (
    genero_id  SERIAL PRIMARY KEY,
    nome       VARCHAR(50) UNIQUE NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE rede_social.conexao_social (
    seguidor_id    INTEGER REFERENCES rede_social.pessoa(pessoa_id),
    seguido_id     INTEGER REFERENCES rede_social.pessoa(pessoa_id),
    forca_conexao  DECIMAL(5, 2),
    data_conexao   DATE DEFAULT CURRENT_DATE,
    updated_at     TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (seguidor_id, seguido_id),
    CHECK (seguidor_id != seguido_id)
);

CREATE TABLE rede_social.leitura (
    pessoa_id    INTEGER REFERENCES rede_social.pessoa(pessoa_id),
    livro_id     INTEGER REFERENCES rede_social.livro(livro_id),
    nota         DECIMAL(3, 1),
    data_leitura DATE DEFAULT CURRENT_DATE,
    updated_at   TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (pessoa_id, livro_id),
    CHECK (nota >= 0 AND nota <= 5)
);

CREATE TABLE rede_social.livro_genero (
    livro_id   INTEGER REFERENCES rede_social.livro(livro_id),
    genero_id  INTEGER REFERENCES rede_social.genero(genero_id),
    PRIMARY KEY (livro_id, genero_id)
);

CREATE TABLE rede_social.pessoa_preferencia (
    pessoa_id  INTEGER REFERENCES rede_social.pessoa(pessoa_id),
    genero_id  INTEGER REFERENCES rede_social.genero(genero_id),
    PRIMARY KEY (pessoa_id, genero_id)
);

INSERT INTO rede_social.pessoa (nome, idade) VALUES
('Ana Silva', 28), ('Bruno Costa', 35), ('Carla Mendes', 42),
('Daniel Santos', 31), ('Evelyn Rocha', 27), ('Fabio Lima', 40),
('Gisele Pires', 33), ('Helder Souza', 29), ('Igor Dias', 36), ('Julia Barros', 24);

INSERT INTO rede_social.livro (titulo, autor, ano_publicacao) VALUES
('1984', 'George Orwell', 1949),
('Sapiens', 'Yuval Harari', 2011),
('Cem Anos de Solidão', 'Gabriel García Márquez', 1967),
('Admirável Mundo Novo', 'Aldous Huxley', 1932),
('Meditações', 'Marco Aurélio', 180),
('Duna', 'Frank Herbert', 1965),
('O Alquimista', 'Paulo Coelho', 1988),
('Fundação', 'Isaac Asimov', 1951);

INSERT INTO rede_social.genero (nome) VALUES
('Ficção Científica'), ('Distopia'), ('História'),
('Filosofia'), ('Fantasia'), ('Drama'), ('Romance');

INSERT INTO rede_social.livro_genero (livro_id, genero_id) VALUES
(1,1),(1,2),(2,3),(3,7),(4,1),(4,2),(5,4),(6,1),(7,4),(7,5),(8,1);

INSERT INTO rede_social.pessoa_preferencia (pessoa_id, genero_id) VALUES
(1,1),(1,2),(2,3),(2,4),(3,7),(4,1),(5,6),(6,3),(7,1),(8,3),(8,4),(9,7),(10,1);

INSERT INTO rede_social.conexao_social (seguidor_id, seguido_id, forca_conexao) VALUES
(1,2,0.8),(2,3,0.9),(3,1,0.7),(4,1,0.6),(4,2,0.6),(4,3,0.5),
(3,5,0.85),(5,6,0.75),(6,7,0.95),(7,8,0.8),(8,9,0.6),(9,10,0.9),
(1,4,0.4),(10,1,0.2),(5,1,0.5),(2,7,0.6);

INSERT INTO rede_social.leitura (pessoa_id, livro_id, nota, data_leitura) VALUES
(1,1,5.0,'2024-01-15'),(1,3,4.5,'2024-02-20'),(2,2,5.0,'2024-01-10'),
(2,1,3.0,'2024-03-05'),(3,3,4.8,'2024-02-28'),(4,1,5.0,'2024-01-20'),
(4,2,2.5,'2024-03-10'),(5,4,5.0,'2024-04-01'),(6,5,4.9,'2024-04-10'),
(7,6,4.7,'2024-05-01'),(8,7,4.8,'2024-05-15'),(9,8,5.0,'2024-06-01'),
(10,4,4.2,'2024-06-10'),(7,1,4.5,'2024-01-05'),(3,2,4.0,'2024-02-01');


create table shop.customers (
    customer_id bigint generated always as identity primary key,
    name varchar(200) not null,
    email varchar(200) not null unique,
    country_code char(2) not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    deleted_at timestamp null
);

create table shop.orders (
    order_id bigint generated always as identity primary key,
    customer_id bigint not null references shop.customers(customer_id),
    order_date timestamp not null default now(),
    amount numeric(12, 2) not null,
    status varchar(20) not null
        check (status in ('pending', 'paid', 'cancelled', 'refunded')),
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    deleted_at timestamp null
);

insert into shop.customers
    (name, email, country_code)
values
    ('Ana Silva', 'ana@example.com', 'BR'),
    ('Bruno Costa', 'bruno@example.com', 'BR'),
    ('Carla Mendes', 'carla@example.com', 'DE'),
    ('Daniel Souza', 'daniel@example.com', 'US'),
    ('Emma Fischer', 'emma@example.com', 'DE'),
    ('Felipe Rocha', 'felipe@example.com', 'BR'),
    ('Grace Miller', 'grace@example.com', 'US'),
    ('Helena Martins', 'helena@example.com', 'BR');

insert into shop.orders
    (customer_id, order_date, amount, status)
values
    (1, '2026-08-20 10:15:00', 120.50, 'paid'),
    (2, '2026-08-20 11:30:00', 89.90, 'paid'),
    (1, '2026-08-21 09:00:00', 45.00, 'cancelled'),
    (3, '2026-08-21 15:10:00', 230.00, 'paid'),
    (4, '2026-08-22 14:20:00', 59.99, 'refunded'),
    (5, '2026-08-23 17:30:00', 310.40, 'paid'),
    (2, '2026-08-24 08:45:00', 75.50, 'paid'),
    (6, '2026-08-25 13:00:00', 150.00, 'paid'),
    (7, '2026-08-26 16:20:00', 42.75, 'cancelled'),
    (8, '2026-08-27 10:10:00', 199.90, 'paid');

create table shop.salespeople (
    salesperson_id bigint generated always as identity primary key,
    name varchar(200) not null,
    email varchar(200) not null unique,
    region varchar(100) not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    deleted_at timestamp null
);

insert into shop.salespeople
    (name, email, region)
values
    ('Sofia Almeida', 'sofia@example.com', 'South'),
    ('Lucas Ferreira', 'lucas@example.com', 'Southeast'),
    ('Marta Nunes', 'marta@example.com', 'Europe'),
    ('Owen Price', 'owen@example.com', 'North America');

alter table shop.orders
    add column salesperson_id bigint null references shop.salespeople(salesperson_id);

update shop.orders
set salesperson_id = case order_id
    when 1 then 1
    when 2 then 2
    when 3 then 1
    when 4 then 3
    when 5 then 4
    when 6 then 2
    when 7 then 1
    when 8 then 4
    when 9 then 3
    when 10 then 2
end;

create table shop.products (
    product_id bigint generated always as identity primary key,
    name varchar(200) not null,
    category varchar(100) not null,
    unit_price numeric(12, 2) not null,
    is_active boolean not null default true,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    deleted_at timestamp null
);

insert into shop.products
    (name, category, unit_price, is_active)
values
    ('Classic T-Shirt', 'Apparel', 29.90, true),
    ('Running Sneakers', 'Footwear', 89.00, true),
    ('Notebook Pro 14', 'Electronics', 1299.00, true),
    ('Coffee Grinder', 'Home', 74.50, true),
    ('Travel Mug', 'Home', 18.00, true),
    ('Wireless Headphones', 'Electronics', 199.99, true),
    ('Desk Lamp', 'Home', 42.75, true),
    ('Leather Wallet', 'Accessories', 59.00, true),
    ('Yoga Mat', 'Fitness', 49.90, true),
    ('Bluetooth Speaker', 'Electronics', 119.90, true);

create table shop.order_items (
    order_item_id bigint generated always as identity primary key,
    order_id bigint not null references shop.orders(order_id),
    product_id bigint not null references shop.products(product_id),
    quantity integer not null check (quantity > 0),
    unit_price numeric(12, 2) not null,
    amount numeric(12, 2) not null check (amount >= 0),
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    deleted_at timestamp null
);

insert into shop.order_items
    (order_id, product_id, quantity, unit_price, amount)
values
    (1, 1, 2, 29.90, 59.80),
    (1, 5, 1, 18.00, 18.00),
    (2, 2, 1, 89.00, 89.00),
    (3, 7, 1, 42.75, 42.75),
    (4, 3, 1, 1299.00, 1299.00),
    (4, 6, 1, 199.99, 199.99),
    (5, 8, 1, 59.00, 59.00),
    (6, 4, 2, 74.50, 149.00),
    (6, 10, 1, 119.90, 119.90),
    (7, 2, 1, 89.00, 89.00),
    (8, 1, 3, 29.90, 89.70),
    (8, 9, 1, 49.90, 49.90),
    (9, 7, 1, 42.75, 42.75),
    (10, 6, 1, 199.99, 199.99),
    (10, 5, 2, 18.00, 36.00);

CREATE SCHEMA IF NOT EXISTS analytics;
