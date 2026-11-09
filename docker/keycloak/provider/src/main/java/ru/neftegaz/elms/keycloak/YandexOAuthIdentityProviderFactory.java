package ru.neftegaz.elms.keycloak;

import org.keycloak.broker.oidc.OAuth2IdentityProviderConfig;
import org.keycloak.broker.provider.AbstractIdentityProviderFactory;
import org.keycloak.models.IdentityProviderModel;
import org.keycloak.models.KeycloakSession;

public final class YandexOAuthIdentityProviderFactory
        extends AbstractIdentityProviderFactory<YandexOAuthIdentityProvider> {

    public static final String PROVIDER_ID = "yandex-oauth";

    @Override
    public String getName() {
        return "Yandex OAuth 2.0";
    }

    @Override
    public YandexOAuthIdentityProvider create(
            KeycloakSession session, IdentityProviderModel model) {
        return new YandexOAuthIdentityProvider(
                session, new OAuth2IdentityProviderConfig(model));
    }

    @Override
    public OAuth2IdentityProviderConfig createConfig() {
        return new OAuth2IdentityProviderConfig();
    }

    @Override
    public String getId() {
        return PROVIDER_ID;
    }
}
