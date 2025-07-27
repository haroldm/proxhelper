import typer
from proxhelper import get_image, create_nixos_container

app = typer.Typer()

app.add_typer(get_image.app)
app.add_typer(create_nixos_container.app)

if __name__ == "__main__":
    app()
