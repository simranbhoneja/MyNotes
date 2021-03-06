create database my_notes;

use my_notes;

create table notes (
	`id` int primary key auto_increment,
	`title` varchar(500) not null,
    `content` text not null,
    `is_complete` tinyint default 0,
    `folder_id` int default null,
    `created_at` datetime not null default current_timestamp(),
    `updated_at` datetime not null default current_timestamp() on update now(),
    `deleted_at` datetime default null 
);

create table folder (
	`id` int primary key auto_increment,
    `name` varchar(500) not null,
    `created_at` datetime not null default current_timestamp(),
    `updated_at` datetime not null default current_timestamp() on update now(),
    `deleted_at` datetime default null 
);

alter table notes
ADD CONSTRAINT FK_FolderId
foreign key (`folder_id`) references folder(`id`);

insert into notes  (`title`, `content`) values 
('Note 1', 'This is my first node'),
('Note 2', 'This is my second node'),
('Note 3', 'This is my third node'),
('Note 4', 'This is my Fourth node');

select * from notes;
select * from folder;

insert into folder (`id`, `name`) values
('1', 'Django'),
('2', 'JAVA'),
('3', 'Python'),
('4', 'Web Development');

insert into folder (`id`, `name`) values
('5', 'FLASK');

update notes set deleted_at = null where id > 0;

select * from users;
drop table users;

alter table notes
add user_id int not null default 3;

update notes set user_id = 1 where id > 0;

alter table notes
add constraint FK_notes_user
foreign key (user_id) references users(id);

select * from notes;
	