-- Player Tables
CREATE TABLE IF NOT EXISTS players_table (
    player_id VARCHAR(50) PRIMARY KEY,
    balance INTEGER DEFAULT 50 CHECK (balance >= 0),
    guns SMALLINT DEFAULT 0 CHECK (guns >= 0 AND guns <= 127),
    medkit SMALLINT DEFAULT 0 CHECK (medkit >= 0 AND medkit <= 127),
    vest SMALLINT DEFAULT 0 CHECK (vest >= 0 AND vest <= 127),
    is_vested BOOLEAN DEFAULT FALSE,
    last_worked DATE DEFAULT NULL,
    last_dead DATE DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS political_roles_table (
    role_id SERIAL PRIMARY KEY,
    player_id VARCHAR(50),
    role_name VARCHAR(50) NOT NULL,
    assigned_at DATE DEFAULT CURRENT_DATE,
    CONSTRAINT fk_political_player_id
        FOREIGN KEY (player_id) REFERENCES players_table(player_id)
        ON DELETE CASCADE
);

-- Company Tables
CREATE TABLE IF NOT EXISTS companies_table (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(50) UNIQUE NOT NULL,
    company_cash_reserve INTEGER CHECK (company_cash_reserve > 0),
    founding_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shareholders_table (
    company_id INTEGER NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    shareholder_role VARCHAR(50) NOT NULL,
    shareholder_wage INTEGER CHECK (shareholder_wage >= 0),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_shareholders PRIMARY KEY (company_id, player_id),
    CONSTRAINT fk_shareholder_company_id FOREIGN KEY (company_id) REFERENCES companies_table(company_id),
    CONSTRAINT fk_shareholder_player_id FOREIGN KEY (player_id) REFERENCES players_table(player_id)
);

-- Building Tables
CREATE TABLE IF NOT EXISTS buildings_table (
    building_id SERIAL PRIMARY KEY,
    building_cash_reserve INTEGER CHECK (building_cash_reserve > 0)
);

CREATE TABLE IF NOT EXISTS ownerships_table (
    ownership_id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL,
    owner_type TEXT NOT NULL CHECK (owner_type IN ('company', 'player')),
    player_id VARCHAR(50),
    company_id INTEGER,
    ownership_date DATE NOT NULL,

    CONSTRAINT fk_ownership_building_id FOREIGN KEY (building_id) REFERENCES buildings_table(building_id),
    CONSTRAINT fk_ownership_player_id FOREIGN KEY (player_id) REFERENCES players_table(player_id),
    CONSTRAINT fk_ownership_company_id FOREIGN KEY (company_id) REFERENCES companies_table(company_id),

    CHECK (
        (owner_type = 'player' AND player_id IS NOT NULL AND company_id IS NULL) OR
        (owner_type = 'company' AND company_id IS NOT NULL AND player_id IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS building_banks_table (
    bank_id INTEGER PRIMARY KEY,
    bank_name VARCHAR(50) UNIQUE NOT NULL,
    founding_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interest_rate DECIMAL CHECK (interest_rate >= 0.0),
    CONSTRAINT fk_bank_building_id
        FOREIGN KEY (bank_id) REFERENCES buildings_table(building_id)
);

CREATE TABLE IF NOT EXISTS building_factories_table (
    factory_id INTEGER PRIMARY KEY,
    factory_type VARCHAR(10) NOT NULL,
    factory_inventory SMALLINT DEFAULT 0 CHECK (factory_inventory >= 0),
    CONSTRAINT fk_factory_building_id
        FOREIGN KEY (factory_id) REFERENCES buildings_table(building_id)
);

CREATE TABLE IF NOT EXISTS building_employment_table (
    building_id INTEGER,
    player_id VARCHAR(50),
    wage INTEGER CHECK (wage >= 0),
    CONSTRAINT pk_building_employment PRIMARY KEY (building_id, player_id),
    CONSTRAINT fk_employment_building_id FOREIGN KEY (building_id) REFERENCES buildings_table(building_id),
    CONSTRAINT fk_employment_player_id FOREIGN KEY (player_id) REFERENCES players_table(player_id)
);

-- Transfer Parties Table (polymorphic reference)
CREATE TABLE IF NOT EXISTS transfer_parties_table (
    party_id SERIAL PRIMARY KEY,
    party_type TEXT NOT NULL CHECK (party_type IN ('player', 'company', 'building')),
    player_id VARCHAR(50),
    company_id INTEGER,
    building_id INTEGER,
    CHECK (
        (party_type = 'player' AND player_id IS NOT NULL AND company_id IS NULL AND building_id IS NULL) OR
        (party_type = 'company' AND company_id IS NOT NULL AND player_id IS NULL AND building_id IS NULL) OR
        (party_type = 'building' AND building_id IS NOT NULL AND player_id IS NULL AND company_id IS NULL)
    ),
    FOREIGN KEY (player_id) REFERENCES players_table(player_id),
    FOREIGN KEY (company_id) REFERENCES companies_table(company_id),
    FOREIGN KEY (building_id) REFERENCES buildings_table(building_id)
);

-- Transactions Table
CREATE TABLE IF NOT EXISTS transactions_table (
    transaction_number SERIAL PRIMARY KEY,
    time_of_transaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transfer_type VARCHAR(10),
    sender_party_id INTEGER NOT NULL,
    recipient_party_id INTEGER NOT NULL,
    amount SMALLINT NOT NULL CHECK (amount > 0),
    memo VARCHAR(50) DEFAULT 'n/a',
    FOREIGN KEY (sender_party_id) REFERENCES transfer_parties_table(party_id),
    FOREIGN KEY (recipient_party_id) REFERENCES transfer_parties_table(party_id)
);