.PHONY: up down restart logs update ps

up:
	./setup.sh

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

# Serverda yangi kodni tortib olib qayta qurish uchun
update:
	git pull
	docker compose up -d --build
