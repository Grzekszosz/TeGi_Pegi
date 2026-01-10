IMAGE_NAME=tegi-pegi
PORT=8501

.PHONY: build run rebuild

build:
	docker build -t $(IMAGE_NAME) .

run: build
	docker run --rm -p $(PORT):8501 $(IMAGE_NAME)

rebuild:
	docker build --no-cache -t $(IMAGE_NAME) .
