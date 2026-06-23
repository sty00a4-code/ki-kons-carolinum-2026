create table
    categories ('id' int primary key, 'name' varchar(100) unique);

create table
    classes (
        'id' int primary key,
        'name' varchar(100) unique,
        'min' int not null,
        category_id int references categories ('id')
    );

create table
    students ('id' int primary key);

create table
    students_classes (
        'student_id' int references students ('id'),
        'class_id' int references classes ('id'),
        'semester' varchar(8),
        'points' decimal default 0,
        primary key ('student_id', 'class_id', 'semester')
    );