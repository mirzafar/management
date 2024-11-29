create table users
(
    id          serial primary key,
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
);

alter table users
    owner to postgres;

create unique index users_username_uindex
    on users (username);


create table public.categories
(
    id          serial primary key,
    title       text                 not null,
    unit        text                 not null,
    description text,
    is_active   boolean default TRUE not null
);

comment on column public.categories.unit is 'шт, кв';

