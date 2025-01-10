build-WebResearchFunction:
	GOOS=linux GOARCH=arm64 go build -tags lambda.norpc -o bootstrap main.go
	cp ./bootstrap $(ARTIFACTS_DIR)/.