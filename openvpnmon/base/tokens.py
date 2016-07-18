from django.core.exceptions import PermissionDenied
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import int_to_base36
from django.utils.crypto import salted_hmac
from django.utils import six


class CertDistributionTokenGenerator(PasswordResetTokenGenerator):

    key_salt = "base.tokens.CertDistributionTokenGenerator"

    def _make_token_with_timestamp(self, user, timestamp):
        """
        Generate a token that cannot be used twice and that last some time.
        """
        # IMPORTANT: user is the API param name, but in our context it is a Client model
        client = user

        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)

        # By hashing on the internal state of the client and using state
        # that is sure to change (the cert_public_download_on will change as soon as
        # the certificate is downloaded), we produce a hash that will be
        # invalid as soon as it is used.
        # We limit the hash to 20 chars to keep URL short

        hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(client, timestamp)).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def _make_hash_value(self, client, timestamp):

        if client.cert_public_download_on:
            state_sure_to_change = client.cert_public_download_on.strftime(
                '%Y-%m-%d %H:%M:%S')
        else:
            state_sure_to_change = ""

        try:
            ts_distribution = client.cert_distribution_on.strftime(
                '%Y-%m-%d %H:%M:%S')
        except AttributeError:
            raise PermissionDenied

        return (six.text_type(client.pk) + ts_distribution +
                state_sure_to_change + six.text_type(timestamp))
