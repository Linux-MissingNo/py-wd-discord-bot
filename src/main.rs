use std::env;
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::Path;
use std::process::Command;

const ENV_KEYS: [&str; 9] = [
    "TOKEN",
    "SHOT_ROLE",
    "SHOT_TIMEOUT_IN_HOURS",
    "GUILD_ID",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
    "DB_HOST",
    "DB_PORT",
];

const MAIN_SCRIPT_PATH: &str = "scripts/main.py";
const CONFIG_PATH: &str = "config";
const ENV_FILE_PATH: &str = "config/.env";

const INIT_SQL: &str = "migrations/init.sql";
const SEED_SQL: &str = "migrations/seed.sql";

fn main() -> io::Result<()> {
    println!("Current working directory: {}", env::current_dir()?.display());

    create_env_file_if_missing()?;
    run_sql_db()?;
    run_python_script()?;

    println!("All setup steps completed successfully.");
    Ok(())
}

fn create_env_file_if_missing() -> io::Result<()> {
    if !Path::new(CONFIG_PATH).exists() {
        println!("Creating config directory...");
        fs::create_dir_all(CONFIG_PATH)?;
    }

    if !Path::new(ENV_FILE_PATH).exists() {
        println!(".env not found, generating new .env...");
        let mut writer = File::create(ENV_FILE_PATH)?;

        for key in ENV_KEYS.iter() {
            let default = match *key {
                "DB_USER" => "your_db_user",
                "DB_PASSWORD" => "your_db_password",
                "DB_NAME" => "your_db_name",
                "DB_HOST" => "localhost",
                "DB_PORT" => "5432",
                _ => "null",
            };
            writeln!(writer, "{key}={default}")?;
        }

        panic!(".env file created at '{ENV_FILE_PATH}'. Please fill in the values and re-run the program.");
    }

    Ok(())
}

fn run_sql_db() -> io::Result<()> {
    dotenv::from_filename(ENV_FILE_PATH).expect("Failed to load .env file from config/");

    let db_user = env::var("DB_USER").expect("DB_USER not set in .env");
    let db_password = env::var("DB_PASSWORD").expect("DB_PASSWORD not set in .env");
    let db_name = env::var("DB_NAME").expect("DB_NAME not set in .env");
    let db_host = env::var("DB_HOST").unwrap_or_else(|_| "localhost".to_string());
    let db_port = env::var("DB_PORT").unwrap_or_else(|_| "5432".to_string());

    if !Path::new("data").exists() {
        println!("Creating data directory...");
        fs::create_dir_all("data")?;
    }

    println!("Connecting to PostgreSQL database...");

    // Schema initialization
    run_psql_command(&db_user, &db_password, &db_host, &db_port, &db_name, INIT_SQL)?;

    println!("Schema created successfully.");

    // Seed database
    run_psql_command(&db_user, &db_password, &db_host, &db_port, &db_name, SEED_SQL)?;

    println!("Database seeded successfully.");

    Ok(())
}

fn run_psql_command(
    user: &str,
    password: &str,
    host: &str,
    port: &str,
    db: &str,
    file: &str,
) -> io::Result<()> {
    let status = Command::new("psql")
        .arg("-U")
        .arg(user)
        .arg("-h")
        .arg(host)
        .arg("-p")
        .arg(port)
        .arg("-d")
        .arg(db)
        .arg("-f")
        .arg(file)
        .env("PGPASSWORD", password)
        .status()?;

    if !status.success() {
        panic!("Failed to execute SQL file: {}", file);
    }

    Ok(())
}

fn run_python_script() -> io::Result<()> {
    let status = Command::new("python3")
        .arg(MAIN_SCRIPT_PATH)
        .status()
        .expect("Failed to execute Python script");

    if status.success() {
        println!("Python script executed successfully.");
    } else {
        println!("Python script execution failed.");
    }

    Ok(())
}
