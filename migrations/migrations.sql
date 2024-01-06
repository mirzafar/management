create schema sales;

create table sales.products
(
    id         serial primary key not null unique,
    title      varchar(200),
    created_at timestamp default (now())::timestamp without time zone,
    status     smallint  default 0
);

