
sh:
	docker exec -it ema bash
logs:
	docker logs -f ema --tail 1000
log:logs

cs:
	docker exec -it ema flake8 ema