
sh:
	docker exec -it ema bash
logs:
	docker logs -f ema --tail 1000
log:logs