FROM quay.io/keycloak/keycloak:24.0.5@sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9

COPY entrypoint.sh /opt/keycloak/entrypoint.sh
COPY realm-elms.json /opt/keycloak/data/import-template/realm-elms.json

USER 1000

ENTRYPOINT ["/opt/keycloak/entrypoint.sh"]
