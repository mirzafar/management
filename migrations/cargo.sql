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
    birthday    date
);

create index users_password_index
    on users (password);

create index users_status_index
    on users (status);

create unique index users_username_uindex
    on users (username);

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


create table permissions
(
    id          serial
        primary key,
    key         varchar(100) not null,
    title       varchar(250),
    status      smallint default 0,
    description text     default ''::text
);

