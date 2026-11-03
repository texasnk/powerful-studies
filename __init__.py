"""Powerful Studies bootstrap for Anki 25.09.4+."""

from aqt import mw

# Anki deliberately blocks arbitrary add-on files from its media server. The
# Explorer's CSS and JavaScript must be exported before stdHtml() can load them.
mw.addonManager.setWebExports(__name__, r"web/.*\.(css|js)")

from .integrations.anki_hooks import install

install()
