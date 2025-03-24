<p align="right">
    <a href="https://github.com/Nayjest/ema/actions/workflows/code-style.yml" target="_blank"><img src="https://github.com/Nayjest/ema/actions/workflows/code-style.yml/badge.svg" alt="Code Style"></a>
    <a href="https://github.com/Nayjest/ema/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/static/v1?label=license&message=MIT&color=d08aff" alt="License"></a>
</p>

# EMA: Engineering Manager Assistant AI

## Integrations

- Linear
- Slack
- GitHub
- Confluence

## Installation

1. Clone this repository and navigate into the folder:
```sh
git clone git@github.com:Nayjest/ema.git
cd ema
```

2. Copy `.env.example` to `.env` and populate it with all required configuration values:
```sh
cp .env.example .env
nano .env
```

3. Start containers:
```sh
docker-compose up
```

4. Index your data:
```sh
docker exec -it ema bash -c "python -m ema index-issues"
```

## 📝 License

Licensed under the [MIT License](https://github.com/Nayjest/ema/blob/main/LICENSE)
© 2025 [Vitalii Stepanenko](mailto:mail@vitaliy.in)
