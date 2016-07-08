# CLIENT_PREPARED means that client has a correct configuration
CLIENT_PREPARED = 10
# CLIENT_CERT_CREATED means that client certificate has been created
CLIENT_CERT_CREATED = 20
# CLIENT_AUTHORIZED means that ACL and FIREWALL policies has been set
CLIENT_AUTHORIZED = 30
# CLIENT_ENABLED means that the client is able to access the corresponding VPN
CLIENT_ENABLED = 40

# CLIENT_CERT_REVOKED means that the client in not able to access the corresponding VPN anymore
CLIENT_CERT_REVOKED = 50

# CLIENT_CERT_IS_NEAR_TO_INVALID_DATE means that certificate provided is near to validity end
CLIENT_CERT_IS_NEAR_TO_INVALID_DATE = 60

######################
#--- ERROR STATES ---#
######################

CLIENT_ERROR_STATE = -10

CLIENT_MISCONFIGURED = 5
CLIENT_CERT_BROKEN_OR_NOT_FOUND = 15
CLIENT_AUTHORIZATION_FAILED = 25

########################
#--- STATES DISPLAY ---#
########################

STATES_D = {
    CLIENT_PREPARED: _("prepared"),
    CLIENT_CERT_CREATED: _("certificate created"),
    CLIENT_AUTHORIZED: _("authorized"),
    CLIENT_ENABLED: _("enabled"),
    CLIENT_ERROR_STATE: _("error state"),
    CLIENT_MISCONFIGURED: _("misconfigured"),
    CLIENT_CERT_BROKEN_OR_NOT_FOUND: _("certificate broken or not found"),
    CLIENT_CERT_IS_NEAR_TO_INVALID_DATE:
    _("certificate near to invalid date end"),
}
