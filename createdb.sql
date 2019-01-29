create table failed
         (session text primary key,
          username text,
          password text,
          timestamp integer,
          src_ip text,
          loc text);

create table success
         (session text primary key,
          username text,
          password text,
          timestamp integer,
          src_ip text,
          loc text);

create table command
         (timestamp integer primary key,
          src_ip text,
          input text,
          session text
);
