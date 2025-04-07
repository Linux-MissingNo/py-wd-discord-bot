use std::fs::File;
use std::path::Path;
use std::io::{self, Write};
use std::process::Command;

const ENV_KEYS: [&str; 4] = ["TOKEN", "SHOT_ROLE", "SHOT_TIMEOUT_IN_HOURS", "GUILD_ID"];

const MAIN_SCRIPT_PATH: &str = "scripts/main.py";
const CONFIG_PATH: &str = "config/";

fn main() -> io::Result<()> {
    // check the working directory
    println!("Current working directory: {}", env::current_dir().unwrap().display());


    // Step 1: Create and populate .env file if it doesn't exist
    create_env_file()?;

    // TBD: Step 2: Create a function that create the SQL database

    // Step 3: Trigger Python script
    run_python_script()?;

    println!("All setup steps completed successfully.");
    Ok(())
}

// Create .env file
fn create_env_file() -> io::Result<()> {
    let path = format!("{}/.env", CONFIG_PATH); 

    if !Path::new(&path).exists() {
        println!(".env not found, generating new .env...");
        let mut writer = File::create(path)?;

        for key in ENV_KEYS.iter() {
            writeln!(writer, "{key}=null").expect("Failed to write to .env");
        }

        panic!("
            .env was created. Please fill out the values before running the program again. Exiting the program...
        ");
    }
    Ok(())
}

// Run the Python script
fn run_python_script() -> io::Result<()> {
    let status = Command::new("python3")
        .arg(MAIN_SCRIPT_PATH)
        .status()
        .expect("Failed to execute Python script");

    if status.success() {
        println!("Python script executed successfully.");
    } else {
        println!("Python script execution failed with status: {status}");
    }

    Ok(())
}
