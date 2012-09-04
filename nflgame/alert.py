"""
A module that provides convenience functions for sending alerts. Currently
this includes sending text (SMS) messages or emails.

This is accomplished through two mechanisms: Google Voice B{or} SMTP.

Using Google Voice
==================
To use Google Voice, this module requires a Google Voice account and depends on
pygooglevoice to access your Google Voice account.

You can sign up for a Google Voice account at
U{voice.google.com<http://voice.google.com>}.

pygooglevoice is in PyPI but unfortunately is not configured properly. You'll
have to download the source and run::

    sudo python2 setup.py install

in the directory containing setup.py. You can download pygooglevoice at
U{code.google.com/p/pygooglevoice
<http://code.google.com/p/pygooglevoice/downloads/list/>}.

A quick example of sending an SMS message with Google Voice::

    import nflgame.alert
    nflgame.alert.google_voice_login('YOUR GMAIL ADDRESS', 'YOUR PASSWORD')
    nflgame.alert.sms('1112223333', 'This is a text message!')

If you don't have a Google Voice account or don't want to install a third
party library, you can still use this module but the C{google_voice_login}
function will not work.

The disadvantage of using Google Voice is that it limits text messages. Since
you'll probably be using this module to send a fair number of alerts, this
might be prohibitive.

Using SMTP
==========
SMTP can be used to send SMS messages or emails. For sending SMS messages,
the SMTP approach requires that you know the provider of the recipient's
cell phone (i.e., Verizon, Sprint, T-Mobile). Although this is a burden,
sending SMS messages through email doesn't seem to be as vigorously rate
limited as Google Voice is.

To send an SMS message using your GMail account::

    import nflgame.alert
    nflgame.alert.gmail_login('YOUR GMAIL ADDRESS', 'YOUR PASSWORD')
    nflgame.alert.sms('1112223333', 'Test message', provider='Verizon')

In this case, the C{provider} parameter is required.

Similarly, you can send email alerts with your GMail account::

    import nflgame.alert
    nflgame.alert.gmail_login('YOUR GMAIL ADDRESS', 'YOUR PASSWORD')
    nflgame.alert.email('somewhere@someplace.com', 'Email message')

Once you login to GMail using C{gmail_login}, you may send both text messages
and emails. You may be logged into Google Voice and GMail at the same time.

Using SMTP without GMail
------------------------
You may use SMTP servers that aren't GMail by using C{smtp_login}. In fact,
C{gmail_login} is a special case of C{smtp_login}::

    def gmail_login(email, passwd):
        def connect():
            gmail = smtplib.SMTP('smtp.gmail.com', port=587)
            gmail.starttls()
            return gmail

        smtp_login(email, passwd, connect)

The connection setup must be provided as a function because it will
typically need to be reused in a long running program. (i.e., If you don't
send an alert for a while, you'll probably be disconnected from the SMTP
server. In which case, the connection setup will be executed again.)
"""
import smtplib
import sys

try:
    import googlevoice
    _gv_available = True
except ImportError:
    _gv_available = False

_voice = None
"""Store the googlevoice.Voice instance."""

_smtp = None
"""Store the smptplib.SMTP session instance."""

_email_from = None
"""Stores the login email address for use in the 'from' field."""

_smtp_connect = None
"""A function that will (re)connect and login"""


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


def smtp_login(email, passwd, connectfun):
    """
    Logs into an SMTP mail server. connectfun should be a function that
    takes no parameters and returns an smtplib.SMTP instance that is ready
    to be logged into. (See the source of gmail_login for an example.)

    username and passwd are then used to log into that smtplib.SMTP instance.

    connectfun may be called again automatically if the SMTP connection
    is broken during program execution.
    """
    global _email_from, _smtp, _smtp_connect

    def connect():
        smtp = connectfun()
        smtp.login(email, passwd)
        return smtp

    _email_from = email
    _smtp_connect = connect
    _smtp = _smtp_connect()


def gmail_login(email, passwd):
    """
    Logs into your GMail account with your full email address
    (i.e., 'something@gmail.com') and password. gmail_login MUST be called
    before using sms with the provider parameter. It only needs to be called
    once per program execution.
    """
    def connect():
        gmail = smtplib.SMTP('smtp.gmail.com', port=587)
        gmail.starttls()
        return gmail

    smtp_login(email, passwd, connect)


def email(to_email, msg, from_email=None):
    """
    Sends an email to to_email with a message containing msg.

    from_email is an optional parameter that specifies the 'from'
    email address. If gmail_login was used, this is automatically
    populated using the login email address. Otherwise it is left empty.
    """
    assert _smtp is not None, \
        "Either gmail_login or smtp_login must be called to setup an " \
        "smtplib.SMTP instance."

    from_email_ = ''
    if from_email is not None:
        from_email_ = from_email
    elif _email_from is not None:
        from_email_ = _email_from

    headers = [
        'To: %s' % to_email,
        'From: %s' % from_email_,
        'Subject: nflgame alert',
    ]
    full_msg = '%s\r\n\r\n%s' % ('\r\n'.join(headers), msg)
    _send_email(from_email_, to_email, full_msg)


def sms(phone_number, msg, provider=None):
    """
    Sends an SMS message to phone_number (which should be a string) with
    a message containing msg.

    If you're using Google Voice to send SMS messages, google_voice_login
    MUST be called before sms can be called. google_voice_login only needs to
    be called once per program execution.

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

    Note that these are SMS messages, and each SMS message is limited to
    160 characters. If msg is longer than that and you're using Google Voice,
    it will be broken up into multiple SMS messages (hopefully). Otherwise,
    if you're sending SMS messages via email, the behavior will vary
    depending upon your carrier.
    """
    if provider is None:
        assert _voice is not None, \
            'You must login to Google Voice using google_voice_login before ' \
            'sending an sms without the provider parameter.'
    if provider is not None:
        assert _smtp is not None, \
            'You must login to an SMTP server using gmail_login or by ' \
            'passing an smtplib.SMTP instance via the smtp parameter' \
            'before sending an sms with the provider parameter.'

    if provider is None:
        _google_voice_sms(phone_number, msg)
    else:
        to = '%s@%s' % (phone_number, providers.get(provider, provider))
        _send_email('', to, 'To: %s\r\n\r\n%s' % (to, msg))


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
    try:
        _voice.send_sms(phone_number, msg)
    except googlevoice.ValidationError:
        # I seem to be getting these but the text messages still go
        # through (eventually).
        pass


def _send_email(from_email, to_email, msg):
    """
    Sends an email using nflgame.alert._smtp. It handles a connection that has
    been disconnected, and reconnects.

    Note that this only works if smtp_login (or gmail_login) was used.
    """
    global _smtp

    try:
        _smtp.sendmail(from_email, to_email, msg)
    except smtplib.SMTPServerDisconnected:
        _smtp = _smtp_connect()
        _smtp.sendmail(from_email, to_email, msg)


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
