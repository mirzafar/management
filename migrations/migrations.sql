create table roles
(
    id          serial
        primary key,
    title       varchar(100) default ''::character varying,
    description text         default ''::text,
    status      smallint     default 0,
    key         varchar(50)  default ''::character varying,
    permissions text[]       default '{}'::text[]
);

create table users
(
    id          serial
        primary key,
    last_name   varchar(100) default ''::character varying,
    first_name  varchar(100) default ''::character varying,
    middle_name varchar(100) default ''::character varying,
    status      smallint     default 0,
    password    text         default ''::text not null,
    username    varchar(100)                  not null,
    photo       varchar(150) default ''::character varying,
    created_at  timestamp    default (now())::timestamp without time zone,
    birthday    date,
    role_id     integer
        constraint users_roles_id_fk
            references roles
);

create unique index users_username_uindex
    on users (username);

create table permissions
(
    id          serial
        primary key,
    key         varchar(100) not null,
    title       varchar(250),
    status      smallint default 0,
    description text     default ''::text
);

create table clients
(
    id          serial
        primary key,
    last_name   varchar(100) default ''::character varying,
    first_name  varchar(100) default ''::character varying,
    middle_name varchar(100) default ''::character varying,
    photo       varchar(150) default ''::character varying,
    phone       varchar(13)  default ''::character varying,
    created_at  timestamp    default (now())::timestamp without time zone,
    is_active   boolean      default true not null,
    address     varchar(200)
);

create table categories
(
    id          serial
        primary key,
    title       text                 not null,
    unit        text                 not null,
    description text,
    is_active   boolean default true not null
);

comment on column categories.unit is 'шт, кв';

create table goods
(
    id              serial
        primary key,
    title           text,
    category_id     integer,
    arrival_price   double precision,
    sale_price      double precision,
    balance         double precision,
    is_active       boolean   default true,
    last_updated_at timestamp default (now())::timestamp without time zone,
    price           double precision
);

create schema store;
create table store.overheads
(
    id          serial
        primary key,
    title       text,
    description text,
    uid         text,
    date        date,
    is_active   boolean default true,
    count       double precision,
    sum         double precision,
    is_close    boolean default false not null
);

create table store.overhead_items
(
    id            serial
        primary key,
    title         text,
    good_id       integer,
    description   text,
    arrival_price double precision,
    sale_price    double precision,
    is_active     boolean   default true,
    count         double precision,
    created_at    timestamp default (now())::timestamp without time zone,
    overhead_id   integer,
    category_id   integer
);

create index overhead_items_overhead_id_index
    on store.overhead_items (overhead_id);

create table store.reasons
(
    id          serial
        primary key,
    title       text,
    description text,
    price       double precision,
    is_active   boolean default true not null
);

create table store.visits
(
    id          serial
        primary key,
    title       text,
    description text,
    good_id     integer,
    is_our      boolean   default false,
    reason_id   integer,
    count       double precision,
    sum         double precision,
    is_active   boolean   default true,
    created_at  timestamp default (now())::timestamp without time zone,
    client_id   integer,
    is_paid     boolean   default false,
    pledged_sum double precision
);


alter table public.goods
    rename column arrival_price to last_arrival_price;

alter table store.reasons
    add parent_id integer;

alter table public.categories
    add parent_id integer;

alter table store.overheads
    drop column count;

alter table store.visits
    drop column title;

alter table public.goods
    drop column sale_price;

INSERT INTO public.users (id, last_name, first_name, middle_name, status, password, username, photo, created_at,
                          birthday, role_id)
VALUES (1, 'admin', 'admin', 'admin', 0, '21232f297a57a5a743894a0e4a801fc3', 'admin', '', '2025-11-22 09:16:27.867288',
        null, null);

create table sales.orders
(
    id         serial primary key,
    sum        float,
    discount   float,
    cashier_id smallint,
    is_paid    boolean,
    pledge     float,
    paid_type  text,
    created_at timestamp default now(),
    total_sum  float
);

create table sales.orders_item
(
    id       serial primary key,
    good_id  integer,
    count    float,
    sum      float,
    price    float,
    order_id integer
);