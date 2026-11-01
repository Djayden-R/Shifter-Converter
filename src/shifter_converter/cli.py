from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import sqlite3
from converter import main as converter_main
import questionary
import os
from converter import validate_shifter_file

cwd = os.getcwd()
console = Console()


def get_file_path(name, folder=False):
    return questionary.path(f"Give file path of {name}", default=cwd, only_directories=folder).ask()


def validate_file(file_path: str):
    try:
        db = sqlite3.connect(file_path)
        if validate_shifter_file(db):
            console.print("[green]File is a valid .Shifter file[/green]")
            return db
        else:
            console.print("[yellow]File is a valid sqlite3 database, but doesn't contain the correct tables for a .Shifter file[/yellow]")
            main()
    except Exception as e:
        console.print(f"[red]File is not a valid sqlite3 database: {e}[/red]")
        main()


def main():
    console.print(Panel.fit("Shifter Converter", style=" bold"))
    console.print("Main menu:")
    console.print("[1] Quick convert (.Shifter -> .ics)")
    console.print("[2] Validate .Shifter")
    console.print("[3] Exit")
    option = Prompt.ask("Select option:", choices=["1", "2", "3", "4"], default="1")

    if option == "1":
        file_path = get_file_path(".Shifter file")
        shifter_file = validate_file(file_path)
        output_dir = get_file_path("output directory", folder=True)
        converter_main(shifter_file, output_dir)  # pyright: ignore[reportArgumentType]
        console.print("[green]Succesfully converted .Shifter to .ics[/green]")
        console.print(f"[cyan]Saved as [italic]{os.path.join(output_dir, 'output_calendar.ics')}[/italic][/cyan]")
        main()
    elif option == "2":
        file_path = get_file_path(".Shifter file")
        validate_file(file_path)
        main()
    elif option == "3":
        quit()
    else:
        print("No clue how you did it, but you selected a number outside of the normal range")


if __name__ == "__main__":
    main()
