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
import googlevoice

_voice = None
"""Store the pygooglevoice.Voice instance."""


def google_voice_login(email, passwd):
    """
    Logs into to your Google Voice account with your full email address
    (i.e., 'something@gmail.com') and password. This MUST be called before
    using send. login only needs to be called once per program execution.

    Note that your Google Voice login information is probably the same as your
    gmail login information. Please be careful with your login credentials!
    (It is not a bad idea to setup an entirely separate Google Voice account
    just for sending SMS.)
    """
    global _voice

    _voice = googlevoice.Voice()
    _voice.login(email, passwd)


def sms(phone_number, msg, provider=None):
    """
    Sends an SMS message to phone_number (which should be a string) with
    a message containing msg.

    If you're using Google Voice to send SMS messages, google_voice_login
    MUST be called before sms can be called. google_voice_login only needs to
    be called once per program execution.

    Note that these are SMS messages, and each SMS message is limited to
    160 characters. If msg is longer than that, it will be broken up into
    multiple SMS messages (hopefully).

    The provider parameter is not currently used, but is anticipated if this
    module provides a way to send SMS messages via emails. A provider will be
    required to look up the email domain. (i.e., for Verizon it's 'vtext.com'.)
    """
    _google_voice_sms(phone_number, msg)


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
