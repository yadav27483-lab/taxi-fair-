CREATE DATABASE taxiapp;
USE taxiapp;

-- USERS
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user'
);

-- BOOKINGS
CREATE TABLE taxi_bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id VARCHAR(20),
    user_name VARCHAR(100),
    phone_number VARCHAR(20),
    pickup_location TEXT,
    drop_location TEXT,
    distance_km FLOAT,
    fare FLOAT,
    booking_date DATE,
    booking_time TIME,
    booking_status VARCHAR(20) DEFAULT 'pending'
);

-- VEHICLES
CREATE TABLE vehicles_for_sale (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_name VARCHAR(100),
    vehicle_type VARCHAR(50),
    model VARCHAR(100),
    price FLOAT,
    seller_name VARCHAR(100),
    contact_number VARCHAR(20),
    description TEXT
);

-- RENTALS
CREATE TABLE vehicle_rentals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100),
    vehicle_name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    total_days INT,
    price_per_day FLOAT,
    total_charge FLOAT
);
SET password_hash = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
WHERE username = 'admin';

SELECT username, role, password_hash FROM users WHERE username = 'admin';