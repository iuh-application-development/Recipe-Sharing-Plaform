from os import name
from share_recipe import create_app

app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
