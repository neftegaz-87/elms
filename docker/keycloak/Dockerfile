FROM quay.io/keycloak/keycloak:24.0.5@sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9 AS keycloak-base

FROM maven:3.9-eclipse-temurin-17 AS provider-build

WORKDIR /build
COPY --from=keycloak-base /opt/keycloak/lib/lib/main /keycloak-libs
COPY provider/src ./src
RUN mkdir -p classes && \
    javac -cp '/keycloak-libs/*' -d classes $(find src -name '*.java') && \
    cp -r src/main/resources/* classes/ && \
    jar cf elms-keycloak-yandex-oauth-1.0.0.jar -C classes . && \
    mkdir -p target && mv elms-keycloak-yandex-oauth-1.0.0.jar target/

FROM keycloak-base

COPY --from=provider-build /build/target/elms-keycloak-yandex-oauth-1.0.0.jar /opt/keycloak/providers/
COPY entrypoint.sh /opt/keycloak/entrypoint.sh
COPY realm-elms.json /opt/keycloak/data/import-template/realm-elms.json

USER 1000

ENTRYPOINT ["/opt/keycloak/entrypoint.sh"]
