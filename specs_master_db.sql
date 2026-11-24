-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Хост: MySQL-8.4:3306
-- Время создания: Ноя 24 2026 г., 16:04
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
(1, 'AMD Ryzen 9 9950X3D2', 'amd_ryzen_9_9950x3d2', 16, 32, 4.3, ''),
(2, 'AMD Ryzen 7 5700x', 'amd_ryzen_7_5700x', 8, 16, 4.6, '');

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
(2, 'NVIDIA Geforce RTX 5070', 'nvidia_geforce_rtx_5070', 'GDDR7', 12, 14000, 1800, '');

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
  `role` varchar(16) NOT NULL DEFAULT 'user' COMMENT 'user or admin'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT COMMENT 'uniqie cpu''s identifyer', AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT для таблицы `gpus`
--
ALTER TABLE `gpus`
  MODIFY `id` int NOT NULL AUTO_INCREMENT COMMENT 'gpu''s unique identifier', AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT COMMENT 'user''s unique identifyer';
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
