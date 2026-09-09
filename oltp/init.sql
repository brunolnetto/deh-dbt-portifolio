CREATE SCHEMA IF NOT EXISTS shop;

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
