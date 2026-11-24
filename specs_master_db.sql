-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Хост: MySQL-8.4:3306
-- Время создания: Ноя 24 2026 г., 18:14
-- Версия сервера: 8.4.6
-- Версия PHP: 8.4.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `specs_master_db`
--

-- --------------------------------------------------------

--
-- Структура таблицы `cpus`
--

CREATE TABLE `cpus` (
  `id` int NOT NULL COMMENT 'uniqie cpu''s identifyer',
  `full_product_name` varchar(255) NOT NULL COMMENT 'full product name',
  `technical_name` varchar(255) NOT NULL COMMENT 'technical product name',
  `cores_count` int NOT NULL,
  `threads_count` int NOT NULL,
  `clock_frequency` float NOT NULL,
  `cpu_image_dir_path` varchar(255) NOT NULL COMMENT 'path to the product image'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `cpus`
--

INSERT INTO `cpus` (`id`, `full_product_name`, `technical_name`, `cores_count`, `threads_count`, `clock_frequency`, `cpu_image_dir_path`) VALUES
(2, 'AMD Ryzen 7 5700x', 'amd_ryzen_7_5700x', 8, 16, 4.6, ''),
(7, 'AMD Ryzen 5 5600', 'amd_ryzen5_5600', 6, 12, 3.8, ''),
(11, 'AMD Ryzen 9 9950X3D2', 'amd_ryzen_9_9950x3d2', 32, 16, 4.2, 'images/site/cpus/amd_ryzen_9_9950x3d2.jpg');

-- --------------------------------------------------------

--
-- Структура таблицы `gpus`
--

CREATE TABLE `gpus` (
  `id` int NOT NULL COMMENT 'gpu''s unique identifier',
  `full_product_name` varchar(255) NOT NULL COMMENT 'full gpu name',
  `technical_name` varchar(255) NOT NULL COMMENT 'technical product name, unvisible for user. with no whitespaces, lowercase',
  `vram_type` set('GDDR4','GDDR5','GDDR6','GDDR6X','GDDR7') NOT NULL,
  `vram_volume` int NOT NULL,
  `vram_clock_frequency` int NOT NULL,
  `core_clock_frequency` int NOT NULL,
  `gpu_image_dir_path` varchar(255) NOT NULL COMMENT 'path to the image of the gpu'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `gpus`
--

INSERT INTO `gpus` (`id`, `full_product_name`, `technical_name`, `vram_type`, `vram_volume`, `vram_clock_frequency`, `core_clock_frequency`, `gpu_image_dir_path`) VALUES
(1, 'NVIDIA Geforce RTX 5090', 'nvidia_geforce_rtx_5090', 'GDDR7', 32, 14000, 2017, ''),
(2, 'NVIDIA Geforce RTX 5070', 'nvidia_geforce_rtx_5070', 'GDDR7', 12, 14000, 1800, ''),
(5, 'NVIDIA Geforce GTX 1050', 'nvidia_geforce_gtx_1050', 'GDDR4', 2, 5000, 1200, '');

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL COMMENT 'user''s unique identifyer',
  `nickname` varchar(33) NOT NULL COMMENT 'user''s nickname. unique',
  `email` varchar(255) NOT NULL COMMENT 'user''s email address. unique',
  `password` varchar(255) NOT NULL COMMENT 'user''s password. stored in hashed form',
  `avatar_dir_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'path to the user''s uploaded avatar image',
  `role` varchar(16) NOT NULL DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `nickname`, `email`, `password`, `avatar_dir_path`, `role`) VALUES
(5, 'EFIM', 'efimkaepta@gmail.com', 'pbkdf2_sha256$310000$a98b7fdce22732380159e50c51c8d22d$319c3a21859266fc033dfcfd6742917b247bc3b5c03117de2e9032a616756663', 'images/users/efim.jpg', 'user'),
(6, 'Админ SPECS-MASTER', 'specs-admin@mail.com', 'pbkdf2_sha256$310000$94903ae671ea7ac2b5f4e8f85da64db9$38a4e44beb8c98d9ce62642e9aaf3219263ff107a8a9d597704eca1e53dc7e2f', 'images/users/admin_specs_master.png', 'admin');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `cpus`
--
ALTER TABLE `cpus`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `UNIQUE_PRODUCT_NAME` (`full_product_name`);

--
-- Индексы таблицы `gpus`
--
ALTER TABLE `gpus`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `UNIQUE_PRODUCT_NAME` (`full_product_name`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `UNIQUE_NICKNAME_KEY` (`nickname`),
  ADD UNIQUE KEY `UNIQUE_EMAIL_KEY` (`email`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `cpus`
--
ALTER TABLE `cpus`
  MODIFY `id` int NOT NULL AUTO_INCREMENT COMMENT 'uniqie cpu''s identifyer', AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT для таблицы `gpus`
--
ALTER TABLE `gpus`
  MODIFY `id` int NOT NULL AUTO_INCREMENT COMMENT 'gpu''s unique identifier', AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT COMMENT 'user''s unique identifyer', AUTO_INCREMENT=12;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
