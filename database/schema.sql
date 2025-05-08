-- Esquema de base de datos para FERREMAS
-- Creación de la base de datos
CREATE DATABASE IF NOT EXISTS ferremas_db;
USE ferremas_db;

-- Tabla de Roles
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de Usuarios
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rol_id INT NOT NULL,
    rut VARCHAR(12) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    activo BOOLEAN DEFAULT true,
    ultimo_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES roles(id),
    INDEX idx_email (email),
    INDEX idx_rut (rut)
);

-- Tabla de Sucursales
CREATE TABLE sucursales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    direccion TEXT NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de Categorías
CREATE TABLE categorias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    categoria_padre_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_padre_id) REFERENCES categorias(id),
    INDEX idx_categoria_padre (categoria_padre_id)
);

-- Tabla de Marcas
CREATE TABLE marcas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de Productos
CREATE TABLE productos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    categoria_id INT NOT NULL,
    marca_id INT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio_base DECIMAL(10,2) NOT NULL,
    imagen_url VARCHAR(255),
    peso DECIMAL(10,2),
    dimensiones VARCHAR(50),
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (marca_id) REFERENCES marcas(id),
    INDEX idx_codigo (codigo),
    INDEX idx_categoria (categoria_id),
    INDEX idx_marca (marca_id)
);

-- Tabla de Inventario
CREATE TABLE inventario (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto_id INT NOT NULL,
    sucursal_id INT NOT NULL,
    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 5,
    ubicacion_bodega VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id),
    UNIQUE KEY unique_producto_sucursal (producto_id, sucursal_id),
    INDEX idx_stock (stock_actual)
);

-- Tabla de Estados de Pedido
CREATE TABLE estados_pedido (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Pedidos
CREATE TABLE pedidos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    sucursal_id INT NOT NULL,
    vendedor_id INT,
    estado_id INT NOT NULL,
    fecha_pedido DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_entrega ENUM('retiro', 'despacho') NOT NULL,
    direccion_entrega TEXT,
    subtotal DECIMAL(10,2) NOT NULL,
    iva DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES usuarios(id),
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id),
    FOREIGN KEY (vendedor_id) REFERENCES usuarios(id),
    FOREIGN KEY (estado_id) REFERENCES estados_pedido(id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_fecha (fecha_pedido)
);

-- Tabla de Detalles de Pedido
CREATE TABLE detalles_pedido (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    INDEX idx_pedido (pedido_id)
);

-- Tabla de Métodos de Pago
CREATE TABLE metodos_pago (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Pagos
CREATE TABLE pagos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pedido_id INT NOT NULL,
    metodo_pago_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    estado ENUM('pendiente', 'completado', 'rechazado', 'reembolsado') NOT NULL,
    referencia_transaccion VARCHAR(100),
    fecha_pago DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id),
    INDEX idx_estado (estado),
    INDEX idx_fecha_pago (fecha_pago)
);

-- Tabla de Facturas
CREATE TABLE facturas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pedido_id INT NOT NULL UNIQUE,
    numero_factura VARCHAR(20) NOT NULL UNIQUE,
    fecha_emision DATETIME NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    iva DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    INDEX idx_numero_factura (numero_factura)
);

-- Tabla de Tipos de Notificación
CREATE TABLE tipos_notificacion (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Notificaciones
CREATE TABLE notificaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipo_id INT NOT NULL,
    usuario_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT false,
    fecha_lectura DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo_id) REFERENCES tipos_notificacion(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    INDEX idx_usuario_leida (usuario_id, leida)
);

-- Tabla de Historial de Precios
CREATE TABLE historial_precios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto_id INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    fecha_inicio DATETIME NOT NULL,
    fecha_fin DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    INDEX idx_producto_fecha (producto_id, fecha_inicio)
);

-- Inserción de datos básicos
INSERT INTO roles (nombre, descripcion) VALUES
('administrador', 'Administrador del sistema'),
('vendedor', 'Vendedor de la tienda'),
('bodeguero', 'Encargado de bodega'),
('contador', 'Contador de la empresa'),
('cliente', 'Cliente registrado');

INSERT INTO estados_pedido (nombre, descripcion) VALUES
('pendiente', 'Pedido recién creado'),
('confirmado', 'Pedido confirmado por el vendedor'),
('en_preparacion', 'Pedido siendo preparado en bodega'),
('listo_para_entrega', 'Pedido listo para ser entregado/despachado'),
('en_transito', 'Pedido en camino al cliente'),
('entregado', 'Pedido entregado al cliente'),
('cancelado', 'Pedido cancelado');

INSERT INTO metodos_pago (nombre, descripcion) VALUES
('webpay_debito', 'Pago con tarjeta de débito vía Webpay'),
('webpay_credito', 'Pago con tarjeta de crédito vía Webpay'),
('transferencia', 'Transferencia bancaria');

INSERT INTO tipos_notificacion (nombre, descripcion) VALUES
('pedido_nuevo', 'Nuevo pedido realizado'),
('pedido_actualizado', 'Actualización en el estado del pedido'),
('stock_bajo', 'Alerta de stock bajo'),
('oferta_especial', 'Notificación de ofertas especiales'); 