MST4K or Maitre d'Strife of Theater 4 Keyboarders is a Discord bot that facilitates the democratic process through the maintenance of a list of movies along with automated poll creation using youpoll.me

### Setup

- Create a `.env` file containing your discord bot token as `BOT_TOKEN=xxxxx`
- Run `docker build . -t mst4k`

### Running

Run `docker run -d -v $PWD/data:/opt/mst4k/data mst4k`
