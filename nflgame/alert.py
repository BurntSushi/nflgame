"""
A module that provides convenience functions for sending alerts. Currently
this includes sending text (SMS) messages to any phone number.

This module requires a Google Voice account and depends on
pygooglevoice to access your Google Voice account.

You can sign up for a Google Voice account at http://voice.google.com

pygooglevoice is in PyPI but unfortunately is not configured properly. You'll
have to download the source and run::

    sudo python2 setup.py install

in the directory containing setup.py. You can download pygooglevoice at
http://code.google.com/p/pygooglevoice/downloads/list

There are other ways to send SMS messages, so this module is designed such that
other methods could be added. (For instance, using an SMTP server to send
emails to addresses like '0001112222@vtext.com'.) Namely, functions specific
to Google Voice are prefixed with '_gv'.
"""
import smtplib
import sys

try:
    import googlevoice
    _gv_available = True
except ImportError:
    _gv_available = False

_voice = None
"""Store the pygooglevoice.Voice instance."""

_gmail = None
"""Store the smptplib.SMTP session instance for a GMail SMTP session."""

_gmail_from = None
"""Stores the login GMail address for use in the 'from' field."""


def google_voice_login(email, passwd):
    """
    Logs into your Google Voice account with your full email address
    (i.e., 'something@gmail.com') and password. This MUST be called before
    using send without the provider parameter.
    login only needs to be called once per program execution.

    Note that your Google Voice login information is probably the same as your
    gmail login information. Please be careful with your login credentials!
    (It is not a bad idea to setup an entirely separate Google Voice account
    just for sending SMS.)
    """
    global _voice

    if not _gv_available:
        print >> sys.stderr, "The pygooglevoice Python package is required " \
                             "in order to use Google Voice."
        return

    _voice = googlevoice.Voice()
    _voice.login(email, passwd)


def gmail_login(email, passwd):
    """
    Logs into your GMail account with your full email address
    (i.e., 'something@gmail.com') and password. gmail_login MUST be called
    before using sms with the provider parameter. It only needs to be called
    once per program execution.
    """
    global _gmail, _gmail_from

    _gmail = smtplib.SMTP('smtp.gmail.com', port=587)
    _gmail.starttls()
    _gmail.login(email, passwd)
    _gmail_from = email


def email(to_email, msg, from_email=None, smtp_client=None):
    """
    Sends an email to to_email with a message containing msg.

    from_email is an optional parameter that specifies the 'from'
    email address. If gmail_login was used, this is automatically
    populated using the login email address. Otherwise it is left empty.

    smtp_client is an optional parameter that specifies an smtplib.SMTP
    instance to be used to send mail. If one is not provied, gmail_login
    MUST be called prior to using email in order to setup a special GMail
    SMTP instance. (This is only necessary once per program execution.)
    """
    smtp = _gmail if _gmail is not None else smtp_client
    assert smtp is not None, \
        "Either gmail_login must be called to setup a GMail " \
        "smtplib.SMTP instance, or one must be provided in the " \
        "smtp_client parameter."

    from_email_ = ''
    if from_email is not None:
        from_email_ = from_email
    elif _gmail_from is not None:
        from_email_ = _gmail_from

    headers = [
        'To: %s' % to_email,
        'From: %s' % from_email_,
        'Subject: nflgame alert',
    ]
    full_msg = '%s\r\n\r\n%s' % ('\r\n'.join(headers), msg)
    smtp.sendmail(from_email_, to_email, full_msg)


def sms(phone_number, msg, provider=None, smtp_client=None):
    """
    Sends an SMS message to phone_number (which should be a string) with
    a message containing msg.

    If you're using Google Voice to send SMS messages, google_voice_login
    MUST be called before sms can be called. google_voice_login only needs to
    be called once per program execution.

    Note that these are SMS messages, and each SMS message is limited to
    160 characters. If msg is longer than that, it will be broken up into
    multiple SMS messages (hopefully).

    The provider parameter can be used to send SMS messages via email. It
    is necessary because SMS messages are sent by sending a message to
    an email like '111222333@vtext.com' or '1112223333@txt.att.net'. Thus,
    each phone number must be paired with a provider.

    A provider can be specified either as a carrier name (i.e., 'Verizon' or
    'ATT'), or as simply the domain (i.e., 'vtext.com' or 'txt.att.net').
    Supported providers are in the module level providers variable. Please
    feel free to add to it and submit a pull request.

    The provider parameter is not currently used, but is anticipated if this
    module provides a way to send SMS messages via emails. A provider will be
    required to look up the email domain. (i.e., for Verizon it's 'vtext.com'.)
    """
    smtp = _gmail if _gmail is not None else smtp_client
    assert _voice is None or (_voice is not None and provider is None), \
        'You must login to Google Voice using google_voice_login before ' \
        'sending an sms without the provider parameter.'
    assert smtp is None or (smtp is not None and provider is not None), \
        'You must login to an SMTP server using gmail_login or by ' \
        'passing an smtplib.SMTP instance via the smtp parameter' \
        'before sending an sms with the provider parameter.'

    if provider is None:
        _google_voice_sms(phone_number, msg)
    else:
        to = '%s@%s' % (phone_number, providers.get(provider, provider))
        smtp.sendmail('', to, 'To: %s\r\n\r\n%s' % (to, msg))


def _google_voice_sms(phone_number, msg):
    """
    Sends an SMS message to phone_number (which should be a string) with
    a message containing msg.

    google_voice_login MUST be called before _google_voice_sms can be called.
    google_voice_login only needs to be called once per program execution.

    Note that these are SMS messages, and each SMS message is limited to
    160 characters. If msg is longer than that, it will be broken up into
    multiple SMS messages.
    """
    _voice.send_sms(phone_number, msg)


providers = {
    'ATT': 'txt.att.net',
    'Boost': 'myboostmobile.com',
    'Cricket': 'sms.mycricket.com',
    'Sprint': 'messaging.sprintpcs.com',
    'T-Mobile': 'tmomail.net',
    'Verizon': 'vtext.com',
    'Virgin Mobile': 'vmobl.com',
}
"""
A dictionary of providers. The keys are English name identifiers of a
SMS provider. The values are domain suffixes that come after the
'@' symbol in an email address.
"""
