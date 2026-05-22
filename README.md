# envoy-local

A shell-based utility to spin up and manage local Envoy proxy configurations for service mesh testing.

---

## Installation

```bash
pip install envoy-local
```

> **Requires:** Python 3.8+, Docker, and a local Envoy binary or image.

---

## Usage

Initialize a new Envoy configuration and start a local proxy instance:

```bash
# Bootstrap a default Envoy config
envoy-local init --name my-service --port 8080

# Start the proxy
envoy-local start --config ./envoy-local.yaml

# List running instances
envoy-local list

# Stop a running instance
envoy-local stop --name my-service
```

A minimal `envoy-local.yaml` is generated automatically on `init`, which you can customize to define listeners, clusters, and routing rules for your service mesh testing environment.

---

## Configuration

| Flag | Description | Default |
|------|-------------|---------|
| `--name` | Name of the proxy instance | `default` |
| `--port` | Listener port | `10000` |
| `--admin-port` | Envoy admin interface port | `9901` |
| `--config` | Path to config file | `./envoy-local.yaml` |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes and open a pull request

---

## License

This project is licensed under the [MIT License](LICENSE).