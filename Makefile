IMAGE_NAME=tegi-pegi
PORT=8501

.PHONY: build run

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm -p $(PORT):8501 $(IMAGE_NAME)
