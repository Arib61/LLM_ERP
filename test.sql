CREATE TABLE clients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    secteur VARCHAR(100)
);



CREATE TABLE produits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    categorie VARCHAR(100)
);


CREATE TABLE commandes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_client INT,
    id_produit INT,
    date_commande DATE,
    montant DECIMAL(10,2),
    FOREIGN KEY (id_client) REFERENCES clients(id),
    FOREIGN KEY (id_produit) REFERENCES produits(id)
);


CREATE TABLE fournisseurs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100),
    pays VARCHAR(100)
);


INSERT INTO clients (nom, secteur) VALUES 
('Involys', 'Technologie'),
('Maroc Telecom', 'Télécom'),
('Ministère de Education', 'Public');

-- Produits
INSERT INTO produits (nom, categorie) VALUES 
('Logiciel RH', 'Logiciel'),
('Serveur Dell', 'Matériel'),
('Formation sécurité', 'Service');

-- Fournisseurs
INSERT INTO fournisseurs (nom, pays) VALUES 
('HP Maroc', 'Maroc'),
('Dell France', 'France');

-- Commandes
INSERT INTO commandes (id_client, id_produit, date_commande, montant) VALUES
(1, 1, '2024-04-12', 12500.00),
(2, 2, '2023-07-18', 29500.00),
(3, 3, '2022-05-10', 10500.00);