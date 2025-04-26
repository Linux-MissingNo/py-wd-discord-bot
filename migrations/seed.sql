BEGIN;
-- create government as the user
-- Insert a player for the government
INSERT INTO players_table (player_id, balance, guns, medkit, vest, is_vested, last_worked, last_dead)
VALUES ('GOVERNMENT', 10000, 10, 5, 5, FALSE, CURRENT_DATE, NULL);

INSERT INTO companies_table (company_name, company_cash_reserve, founding_date)
VALUES ('Government', 500000, CURRENT_TIMESTAMP);

-- Insert government player as the owner (shareholder) of the government company
INSERT INTO shareholders_table (
    company_id,
    player_id,
    shareholder_role,
    shareholder_wage,
    joined_at
)
VALUES (
    1,                    -- Assuming government company has company_id = 1
    'GOVERNMENT',         -- ID of the government player
    'owner',              -- Role of the shareholder
    0,                    -- Government owner doesn’t take a wage here
    CURRENT_TIMESTAMP
);

INSERT INTO buildings_table (building_cash_reserve)
VALUES (1000000);

-- Insert the central bank associated with the building
INSERT INTO building_banks_table (bank_name, interest_rate, bank_id)
VALUES ('Central Bank', 0.05, 1);  -- Assuming the bank_id from the building table is 1


-- Insert ownership for the Government Company on Central Bank Building
INSERT INTO ownerships_table (building_id, owner_type, company_id, ownership_date)
VALUES (1, 'company', 1, CURRENT_DATE);

COMMIT;