create table
    categories (
        'id' integer primary key autoincrement,
        'name' varchar(100) unique,
        'min_points' decimal
    );

create table
    classes (
        'id' integer primary key autoincrement,
        'name' varchar(100) unique,
        'min_count' int,
        'min_points' decimal,
        category_id int references categories ('id')
    );

create table
    students ('id' integer primary key autoincrement);

create table
    students_classes (
        'student_id' int references students ('id'),
        'class_id' int references classes ('id'),
        'semester' varchar(8),
        'count' int default 1,
        'points' decimal default 0,
        primary key ('student_id', 'class_id', 'semester')
    );