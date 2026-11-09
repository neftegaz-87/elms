package ru.neftegaz.elms.keycloak;

import com.fasterxml.jackson.databind.JsonNode;
import org.keycloak.broker.oidc.AbstractOAuth2IdentityProvider;
import org.keycloak.broker.oidc.OAuth2IdentityProviderConfig;
import org.keycloak.broker.oidc.mappers.AbstractJsonUserAttributeMapper;
import org.keycloak.broker.provider.BrokeredIdentityContext;
import org.keycloak.broker.provider.IdentityBrokerException;
import org.keycloak.broker.provider.util.SimpleHttp;
import org.keycloak.models.KeycloakSession;

import java.io.IOException;

/** OAuth 2.0 broker for Yandex ID, which is not an OpenID Connect provider. */
public final class YandexOAuthIdentityProvider
        extends AbstractOAuth2IdentityProvider<OAuth2IdentityProviderConfig> {

    public YandexOAuthIdentityProvider(
            KeycloakSession session,
            OAuth2IdentityProviderConfig config) {
        super(session, config);
    }

    @Override
    protected String getDefaultScopes() {
        return "login:email login:info";
    }

    @Override
    protected BrokeredIdentityContext doGetFederatedIdentity(String accessToken) {
        try {
            SimpleHttp.Response response = SimpleHttp
                    .doGet(getConfig().getUserInfoUrl(), session)
                    .header("Authorization", "OAuth " + accessToken)
                    .asResponse();
            if (response.getStatus() != 200) {
                throw new IdentityBrokerException(
                        "Yandex user profile request failed with HTTP " + response.getStatus());
            }

            JsonNode profile = response.asJson();
            String id = required(profile, "id");
            String email = first(profile, "default_email", "email");
            if (email == null) {
                throw new IdentityBrokerException("Yandex profile has no email");
            }
            String username = first(profile, "login", "default_login");
            String firstName = first(profile, "first_name");
            String lastName = first(profile, "last_name");
            String name = first(profile, "real_name", "display_name");

            BrokeredIdentityContext identity = new BrokeredIdentityContext(id);
            identity.setBrokerUserId(getConfig().getAlias() + "." + id);
            identity.setUsername(username != null ? username : email);
            identity.setEmail(email);
            identity.setFirstName(firstName);
            identity.setLastName(lastName);
            if (firstName == null && lastName == null) {
                identity.setName(name);
            }
            AbstractJsonUserAttributeMapper.storeUserProfileForMapper(
                    identity, profile, getConfig().getAlias());
            return identity;
        } catch (IOException e) {
            throw new IdentityBrokerException("Could not fetch Yandex user profile.", e);
        }
    }

    private static String required(JsonNode node, String field) {
        String value = first(node, field);
        if (value == null) {
            throw new IdentityBrokerException("Yandex profile has no " + field);
        }
        return value;
    }

    private static String first(JsonNode node, String... fields) {
        for (String field : fields) {
            JsonNode value = node.get(field);
            if (value != null && !value.isNull() && !value.asText().isBlank()) {
                return value.asText();
            }
        }
        return null;
    }
}
