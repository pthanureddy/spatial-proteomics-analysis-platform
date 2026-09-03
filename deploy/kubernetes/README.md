# Kubernetes blueprint

These manifests are an un-deployed reference, not a production configuration.
They intentionally use placeholder <code>ghcr.io/example</code> images and an
<code>example.test</code> hostname.

Render without applying:

~~~bash
kubectl kustomize deploy/kubernetes
~~~

Before any real deployment, choose an ingress class, replace image references
with immutable digests, configure TLS/DNS, establish backups, add network
policies and identity, and review storage class/security requirements.

The backend is fixed at one replica with a Recreate strategy because this local
architecture uses SQLite on a ReadWriteOnce volume. Horizontal API scale first
requires replacing that persistence layer.

